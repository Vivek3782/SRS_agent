from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.schemas.request import ChatRequest
from app.schemas.response import AskResponse, CompleteResponse
from app.schemas.state import ConversationItem # Import this

from app.services.redis_service import redis_service
from app.services.state_manager import initialize_state, build_ask_state
from app.services.export_service import save_to_excel, save_requirements # Import this

from app.agent.agent import RequirementAgent

router = APIRouter()
agent = RequirementAgent()

@router.post("/chat", response_model=AskResponse | CompleteResponse)
def chat(request: ChatRequest):
    # 1️⃣ Load existing session
    stored_state = redis_service.get_session(request.session_id)
    session_state = initialize_state(stored_state)

    # Normalize empty answers
    normalized_answer = request.answer
    if isinstance(normalized_answer, dict) and not normalized_answer:
        normalized_answer = None

    # --- LOGIC CHANGE: Record History ---
    # If we have a last question AND an answer, record it
    if session_state.last_question and normalized_answer:
        new_item = ConversationItem(
            question=session_state.last_question.text,
            answer=str(normalized_answer),
            timestamp=datetime.utcnow().isoformat(),
            session_id=request.session_id
        )
        session_state.history.append(new_item)
    # ------------------------------------

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
                additional_questions_asked=agent_result.additional_questions_asked,
                history=[item.model_dump() for item in session_state.history] # <--- Pass history
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
        # --- LOGIC CHANGE: Export to Excel ---
        if session_state.history:
            save_to_excel(
                session_id=request.session_id,
                history=[item.model_dump() for item in session_state.history]
            )
            
        # -------------------------------------
        save_requirements(
            session_id=request.session_id,
            requirements=agent_result.requirements
        )
        
        redis_service.delete_session(request.session_id)

        return CompleteResponse(
            status="COMPLETE",
            requirements=agent_result.requirements
        )

    raise HTTPException(status_code=500, detail="Invalid agent response")