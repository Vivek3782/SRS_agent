from fastapi import APIRouter, HTTPException

from app.schemas.request import ChatRequest
from app.schemas.response import AskResponse, CompleteResponse

from app.services.redis_service import redis_service
from app.services.state_manager import initialize_state, build_ask_state

from app.agent.agent import RequirementAgent

router = APIRouter()
agent = RequirementAgent()


@router.post("/chat", response_model=AskResponse | CompleteResponse)
def chat(request: ChatRequest):
    # 1️⃣ Load existing session (or init new)
    stored_state = redis_service.get_session(request.session_id)
    session_state = initialize_state(stored_state)

    # Normalize empty answers
    normalized_answer = request.answer
    if isinstance(normalized_answer, dict) and not normalized_answer:
        normalized_answer = None

    # 2️⃣ Run agent
    agent_result = agent.run(
        phase=session_state.phase,
        context=session_state.context,
        answer=normalized_answer,
        pending_intent=(
            session_state.pending_intent.model_dump()
            if session_state.pending_intent
            else None
        ),
        additional_questions_asked=session_state.additional_questions_asked
    )

    # 3️⃣ ASK → store updated state
    if agent_result.status == "ASK":
        redis_service.set_session(
            request.session_id,
            build_ask_state(
                phase=agent_result.phase,
                context=agent_result.updated_context,
                question=agent_result.question,
                pending_intent=agent_result.pending_intent.model_dump(),
                additional_questions_asked=agent_result.additional_questions_asked
            )
        )

        return AskResponse(
            status="ASK",
            phase=agent_result.phase,
            question=agent_result.question,
            context=agent_result.updated_context
        )

    # 4️⃣ COMPLETE → cleanup + return final requirements
    if agent_result.status == "COMPLETE":
        redis_service.delete_session(request.session_id)

        return CompleteResponse(
            status="COMPLETE",
            requirements=agent_result.requirements
        )

    raise HTTPException(status_code=500, detail="Invalid agent response")
