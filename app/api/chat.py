from datetime import datetime
from app.models.user import User
from app.api.deps import get_current_user
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.request import ChatRequest
from app.schemas.response import AskResponse, CompleteResponse
from app.schemas.state import ConversationItem

from app.services.redis_service import redis_service
from app.services.state_manager import initialize_state, build_ask_state
from app.services.export_service import save_to_excel, get_branding_export, save_requirements

from app.agent.agent import RequirementAgent
from app.config import settings

import glob

router = APIRouter()
agent = RequirementAgent()


@router.post("/chat", response_model=AskResponse | CompleteResponse)
def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):

    search_pattern = settings.EXPORT_XLSX_DIR / \
        f"session_{request.session_id}_*.xlsx"
    if glob.glob(str(search_pattern)):
        raise HTTPException(
            status_code=400, detail="this session is already completed")

    # 1️ Load existing session
    stored_state = redis_service.get_session(request.session_id)
    if not stored_state:
        # Check if they have finished the Branding Phase
        branding_data = get_branding_export(request.session_id)

        if not branding_data:
            # BLOCKED: User skipped the branding interview
            raise HTTPException(
                status_code=403,
                detail="Branding Phase Required. Please complete the company profile interview first."
            )

        if request.answer:
            raise HTTPException(
                status_code=400,
                detail="Answer is not allowed in the initial request"
            )

        session_state = initialize_state(None)

    else:
        session_state = initialize_state(stored_state)

    is_empty_answer = request.answer is None or (
        isinstance(request.answer, dict) and not request.answer)
    if session_state.last_question and is_empty_answer:
        raise HTTPException(
            status_code=400, detail=f"session {request.session_id} is already started with last question {session_state.last_question.text}")

    # Normalize empty answers
    normalized_answer = request.answer
    if isinstance(normalized_answer, dict) and not normalized_answer:
        normalized_answer = None

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

    # 2️ Run agent
    try:
        agent_result = agent.run(
            phase=session_state.phase,
            context=session_state.context,
            answer=normalized_answer,
            pending_intent=(
                session_state.pending_intent.model_dump()
                if session_state.pending_intent
                else None
            ),
            additional_questions_asked=session_state.additional_questions_asked,
            last_question=session_state.last_question.text if session_state.last_question else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3️ ASK → store updated state
    if agent_result.status == "ASK":
        redis_service.set_session(
            request.session_id,
            build_ask_state(
                phase=agent_result.phase,
                context=agent_result.updated_context,
                question=agent_result.question,
                pending_intent=agent_result.pending_intent.model_dump(),
                additional_questions_asked=agent_result.additional_questions_asked,
                history=[item.model_dump()
                         # <--- Pass history
                         for item in session_state.history]
            )
        )

        return AskResponse(
            status="ASK",
            phase=agent_result.phase,
            question=agent_result.question,
            context=agent_result.updated_context
        )

    # 4️ COMPLETE → cleanup + return final requirements
    if agent_result.status == "COMPLETE":
        if session_state.history:
            save_to_excel(
                session_id=request.session_id,
                history=[item.model_dump() for item in session_state.history]
            )
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
