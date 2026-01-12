from datetime import datetime
from app.models.user import User
from app.api.deps import get_current_user, get_db
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query, status, Request
from starlette.datastructures import UploadFile
from sqlalchemy.orm import Session
import os
import json

from app.schemas.response import AskResponse, CompleteResponse
from app.schemas.state import ConversationItem, LastQuestion

from app.services.redis_service import redis_service
from app.services.state_manager import initialize_state, build_ask_state
from app.services.export_service import save_to_excel, get_branding_export, save_requirements

from app.agent.agent import RequirementAgent
from app.config import settings
from app.services.auth_service import auth_service
from app.services.user_service import user_service

import glob
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
agent = RequirementAgent()


async def get_websocket_user(websocket: WebSocket, token: str, db: Session):
    try:
        payload = auth_service.verify_token(token, None)
        username = payload.get("sub")
        if not username:
            return None
        return user_service.get_user_by_email(db, email=username)
    except Exception:
        return None


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    await websocket.accept()

    # 1. Authenticate
    current_user = await get_websocket_user(websocket, token, db)
    if not current_user:
        await websocket.send_json({
            "status": "ERROR",
            "detail": "Unauthorized: Invalid or expired token"
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Check if project requirements are already completed
        search_pattern = settings.EXPORT_JSON_DIR / \
            f"requirements_{session_id}_*.json"
        if glob.glob(str(search_pattern)):
            await websocket.send_json({
                "status": "ERROR",
                "detail": "this project requirements are already completed"
            })
            await websocket.close()
            return

        # 2️. Initial Session Load
        stored_state = redis_service.get_session(session_id)
        if not stored_state:
            branding_data = get_branding_export(session_id)
            if not branding_data:
                await websocket.send_json({
                    "status": "ERROR",
                    "detail": "Branding Phase Required. Please complete the company profile interview first (session check failed)."
                })
                await websocket.close()
                return

            # Start session and get first question
            session_state = initialize_state(None, branding_data=branding_data)
        else:
            session_state = initialize_state(stored_state)

        # 3. If session just started and has no history, run agent once to get initial question
        if not session_state.last_question and not session_state.history:
            agent_result = agent.run(
                phase=session_state.phase,
                context=session_state.context,
                answer=None,
                pending_intent=None,
                additional_questions_asked=0,
                last_question=None,
                # Pass existing (empty) list
                asked_questions=session_state.asked_questions,
                company_profile=session_state.company_profile
            )

            # Save and send initial question
            session_state.phase = agent_result.phase
            session_state.context = agent_result.updated_context

            if agent_result.status == "ASK":
                session_state.last_question = LastQuestion(
                    text=agent_result.question,
                    asked_at=datetime.utcnow().isoformat()
                )

            # Update asked questions list
            if agent_result.status == "ASK":
                session_state.asked_questions.append(agent_result.question)

            redis_service.set_session(
                session_id,
                build_ask_state(
                    phase=agent_result.phase,
                    context=agent_result.updated_context,
                    question=agent_result.question,
                    pending_intent=agent_result.pending_intent.model_dump(
                    ) if agent_result.pending_intent else None,
                    additional_questions_asked=agent_result.additional_questions_asked,
                    history=[],
                    asked_questions=session_state.asked_questions,
                    company_profile=session_state.company_profile
                )
            )

            await websocket.send_json({
                "status": "ASK",
                "phase": agent_result.phase,
                "question": agent_result.question,
                "context": agent_result.updated_context
            })
        else:
            # Send current question if already started
            await websocket.send_json({
                "status": "ASK",
                "phase": session_state.phase,
                "question": session_state.last_question.text,
                "context": session_state.context
            })

        # 4. Loop for messages
        while True:
            try:
                # Treat incoming text directly as the answer
                answer = await websocket.receive_text()
                if not answer or not answer.strip():
                    continue
            except Exception as e:
                await websocket.send_json({"status": "ERROR", "detail": f"Error receiving message: {str(e)}"})
                break

            # Note: File uploads are still best handled via REST or
            # as base64 in the 'answer' field. For now, we assume text 'answer'.

            # Reload session state to ensure fresh data
            stored_state = redis_service.get_session(session_id)
            session_state = initialize_state(stored_state)

            if session_state.last_question and answer:
                new_item = ConversationItem(
                    question=session_state.last_question.text,
                    answer=str(answer),
                    timestamp=datetime.utcnow().isoformat(),
                    session_id=session_id
                )
                session_state.history.append(new_item)

            # Run agent
            agent_result = agent.run(
                phase=session_state.phase,
                context=session_state.context,
                answer=answer,
                pending_intent=(
                    session_state.pending_intent.model_dump()
                    if session_state.pending_intent
                    else None
                ),
                additional_questions_asked=session_state.additional_questions_asked,
                last_question=session_state.last_question.text if session_state.last_question else None,
                asked_questions=session_state.asked_questions,
                company_profile=session_state.company_profile
            )

            if agent_result.status == "ASK":
                session_state.asked_questions.append(agent_result.question)

            if agent_result.status in ["ASK", "REJECT"]:
                redis_service.set_session(
                    session_id,
                    build_ask_state(
                        phase=agent_result.phase,
                        context=agent_result.updated_context,
                        question=agent_result.question,
                        pending_intent=agent_result.pending_intent.model_dump(),
                        additional_questions_asked=agent_result.additional_questions_asked,
                        history=[item.model_dump()
                                 for item in session_state.history],
                        asked_questions=session_state.asked_questions,
                        company_profile=session_state.company_profile
                    )
                )

                await websocket.send_json({
                    "status": agent_result.status,
                    "phase": agent_result.phase,
                    "question": agent_result.question,
                    "context": agent_result.updated_context
                })

            elif agent_result.status == "COMPLETE":
                if session_state.history:
                    save_to_excel(
                        session_id=session_id,
                        history=[item.model_dump()
                                 for item in session_state.history]
                    )
                    save_requirements(
                        session_id=session_id,
                        requirements=agent_result.requirements
                    )

                redis_service.delete_session(session_id)

                await websocket.send_json({
                    "status": "COMPLETE",
                    "requirements": agent_result.requirements
                })
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"status": "ERROR", "detail": str(e)})
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.post("/chat", response_model=AskResponse | CompleteResponse)
async def chat(request: Request, current_user: User = Depends(get_current_user)):
    # Keep the REST endpoint as a fallback or for simple integration
    # (Existing logic same as before, but maybe user prefers WS now)
    form = await request.form()
    logger.info(f"Received request to /chat. Form keys: {list(form.keys())}")
    for k, v in form.items():
        logger.info(f"Form field: '{k}', Type: {type(v)}")

    session_id = form.get("session_id")
    answer = form.get("answer")

    # Handle File Uploads (Same as before)
    uploaded_files = []
    for key, value in form.items():
        # Check if it's an UploadFile object (has filename and file attributes)
        if hasattr(value, "filename") and hasattr(value, "file"):
            uploaded_files.append((key, value))
            logger.info(
                f"Detected file upload: key='{key}', filename='{value.filename}'")

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

    stored_state = redis_service.get_session(session_id)
    if not stored_state:
        branding_data = get_branding_export(session_id)
        if not branding_data:
            raise HTTPException(
                status_code=403, detail="Branding Phase Required. Please complete the company profile interview first.")

        if answer:
            raise HTTPException(
                status_code=400, detail="Answer is not allowed in the initial request")

        session_state = initialize_state(None, branding_data=branding_data)
    else:
        session_state = initialize_state(stored_state)

    is_empty_answer = answer is None or (
        isinstance(answer, dict) and not answer)
    if session_state.last_question and is_empty_answer:
        raise HTTPException(
            status_code=400, detail=f"session {session_id} is already started with last question {session_state.last_question.text}")

    normalized_answer = answer
    if isinstance(normalized_answer, dict) and not normalized_answer:
        normalized_answer = None

    if session_state.last_question and normalized_answer:
        new_item = ConversationItem(
            question=session_state.last_question.text,
            answer=str(normalized_answer),
            timestamp=datetime.utcnow().isoformat(),
            session_id=session_id
        )
        session_state.history.append(new_item)

    try:
        agent_result = agent.run(
            phase=session_state.phase,
            context=session_state.context,
            answer=normalized_answer,
            pending_intent=(session_state.pending_intent.model_dump()
                            if session_state.pending_intent else None),
            additional_questions_asked=session_state.additional_questions_asked,
            last_question=session_state.last_question.text if session_state.last_question else None,
            asked_questions=session_state.asked_questions,
            company_profile=session_state.company_profile
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if agent_result.status == "ASK":
        session_state.asked_questions.append(agent_result.question)

    if agent_result.status in ["ASK", "REJECT"]:
        redis_service.set_session(
            session_id,
            build_ask_state(
                phase=agent_result.phase,
                context=agent_result.updated_context,
                question=agent_result.question,
                pending_intent=agent_result.pending_intent.model_dump(),
                additional_questions_asked=agent_result.additional_questions_asked,
                history=[item.model_dump() for item in session_state.history],
                asked_questions=session_state.asked_questions,
                company_profile=session_state.company_profile
            )
        )
        return AskResponse(status=agent_result.status, phase=agent_result.phase, question=agent_result.question, context=agent_result.updated_context)

    if agent_result.status == "COMPLETE":
        if session_state.history:
            save_to_excel(session_id=session_id, history=[
                          item.model_dump() for item in session_state.history])
            save_requirements(session_id=session_id,
                              requirements=agent_result.requirements)
        redis_service.delete_session(session_id)
        return CompleteResponse(status="COMPLETE", requirements=agent_result.requirements)

    raise HTTPException(status_code=500, detail="Invalid agent response")
