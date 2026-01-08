from datetime import datetime
from app.models.user import User
from app.api.deps import get_current_user
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.datastructures import UploadFile
import os

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

# FIXME: convert ChatRequest to Request for form-data input


@router.post("/chat", response_model=AskResponse | CompleteResponse)
async def chat(request: Request, current_user: User = Depends(get_current_user)):
    form = await request.form()
    session_id = form.get("session_id")
    answer = form.get("answer")

    # Handle File Uploads
    uploaded_files = []
    for key, value in form.items():
        if isinstance(value, UploadFile):
            uploaded_files.append((key, value))

    if uploaded_files:
        uploaded_info = []
        session_upload_dir = settings.EXPORT_IMAGES_DIR / session_id
        os.makedirs(session_upload_dir, exist_ok=True)

        for key, file in uploaded_files:
            file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            orig_filename = file.filename or ""
            ext = os.path.splitext(orig_filename)[1] or ""
            safe_key = "".join(
                [c if c.isalnum() or c in "._-" else "_" for c in key])
            filename = f"{file_timestamp}_{safe_key}{ext}"

            file_path = session_upload_dir / filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_info.append(f"{key}{ext}")

        upload_msg = f"[User uploaded {len(uploaded_files)} files: {', '.join(uploaded_info)}]"
        if not answer:
            answer = upload_msg
        else:
            answer = f"{answer} {upload_msg}"

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    search_pattern = settings.EXPORT_JSON_DIR / \
        f"requirements_{session_id}_*.json"
    if glob.glob(str(search_pattern)):
        raise HTTPException(
            status_code=400, detail="this project requirements are already completed")

    # 1️ Load existing session
    stored_state = redis_service.get_session(session_id)
    if not stored_state:
        # Check if they have finished the Branding Phase
        branding_data = get_branding_export(session_id)

        if not branding_data:
            # BLOCKED: User skipped the branding interview
            raise HTTPException(
                status_code=403,
                detail="Branding Phase Required. Please complete the company profile interview first."
            )

        if answer:
            raise HTTPException(
                status_code=400,
                detail="Answer is not allowed in the initial request"
            )

        session_state = initialize_state(None, branding_data=branding_data)

    else:
        session_state = initialize_state(stored_state)

    is_empty_answer = answer is None or (
        isinstance(answer, dict) and not answer)
    if session_state.last_question and is_empty_answer:
        raise HTTPException(
            status_code=400, detail=f"session {session_id} is already started with last question {session_state.last_question.text}")

    # Normalize empty answers
    normalized_answer = answer
    if isinstance(normalized_answer, dict) and not normalized_answer:
        normalized_answer = None

    # If we have a last question AND an answer, record it
    if session_state.last_question and normalized_answer:
        new_item = ConversationItem(
            question=session_state.last_question.text,
            answer=str(normalized_answer),
            timestamp=datetime.utcnow().isoformat(),
            session_id=session_id
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
            last_question=session_state.last_question.text if session_state.last_question else None,
            company_profile=session_state.company_profile
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3️ ASK → store updated state
    if agent_result.status == "ASK":
        redis_service.set_session(
            session_id,
            build_ask_state(
                phase=agent_result.phase,
                context=agent_result.updated_context,
                question=agent_result.question,
                pending_intent=agent_result.pending_intent.model_dump(),
                additional_questions_asked=agent_result.additional_questions_asked,
                history=[item.model_dump()
                         # <--- Pass history
                         for item in session_state.history],
                company_profile=session_state.company_profile
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
                session_id=session_id,
                history=[item.model_dump() for item in session_state.history]
            )
            save_requirements(
                session_id=session_id,
                requirements=agent_result.requirements
            )

        redis_service.delete_session(session_id)

        return CompleteResponse(
            status="COMPLETE",
            requirements=agent_result.requirements
        )

    raise HTTPException(status_code=500, detail="Invalid agent response")
