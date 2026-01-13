from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect, Query, status
from pydantic import BaseModel
import glob
import os
import json
from datetime import datetime
from app.config import settings
from app.services.branding_service import branding_service
from app.services.export_service import save_branding_files
from app.agent.branding_agent import BrandingAgent
from app.schemas.branding import BrandingResponse, BrandingAskResponse, BrandingCompleteResponse, BrandingTurn
from typing import Optional, Any, List
from app.models.user import User
from app.api.deps import get_current_user, get_db
from sqlalchemy.orm import Session
from app.services.auth_service import auth_service
from app.services.user_service import user_service

router = APIRouter()
agent = BrandingAgent()


class BrandingRequest(BaseModel):
    session_id: str
    answer: Optional[Any] = None


async def get_websocket_user(websocket: WebSocket, token: str, db: Session):
    try:
        payload = auth_service.verify_token(token, None)
        username = payload.get("sub")
        if not username:
            return None
        return user_service.get_user_by_email(db, email=username)
    except Exception:
        return None


@router.websocket("/ws/branding/{session_id}")
async def websocket_branding(
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
        search_pattern = settings.EXPORT_BRANDING_DIR / \
            f"branding_profile_{session_id}_*.json"
        if glob.glob(str(search_pattern)):
            await websocket.send_json({
                "status": "ERROR",
                "detail": "this branding is already completed"
            })
            await websocket.close()
            return

        # 2. Load State
        state = branding_service.get_state(session_id)

        # 3. If already complete, send complete message and close
        if state.is_complete:
            await websocket.send_json({
                "status": "COMPLETE",
                "phase": "BRANDING",
                "requirements": state.profile.model_dump(exclude_none=True)
            })
            await websocket.close()
            return

        # 4. If session just started (no last question), run agent once to get first question
        if not state.last_question and not state.history:
            agent_result = agent.run(state.profile, None, None)
            state.last_question = agent_result.next_question
            state.profile = agent_result.updated_profile
            branding_service.save_state(session_id, state)

            await websocket.send_json({
                "status": "ASK",
                "phase": "BRANDING",
                "question": agent_result.next_question,
                "context": state.profile.model_dump(exclude_none=True)
            })
        else:
            # Send current question if already started
            await websocket.send_json({
                "status": "ASK",
                "phase": "BRANDING",
                "question": state.last_question,
                "context": state.profile.model_dump(exclude_none=True)
            })

        # 5. Loop for messages
        while True:
            try:
                # Treat incoming text directly as the answer
                answer = await websocket.receive_text()
                if not answer or not answer.strip():
                    continue
            except Exception as e:
                await websocket.send_json({"status": "ERROR", "detail": f"Error receiving message: {str(e)}"})
                break

            # Reload state
            state = branding_service.get_state(session_id)

            if state.is_complete:
                break

            # Run Agent
            agent_result = agent.run(
                state.profile, answer, state.last_question)
            state.profile = agent_result.updated_profile

            if not agent_result.is_complete and agent_result.next_question:
                if answer:
                    prev_q = state.last_question if state.last_question else "[Initial Inquiry]"
                    state.history.append(BrandingTurn(
                        question=prev_q, answer=answer))

                state.last_question = agent_result.next_question
                branding_service.save_state(session_id, state)

                await websocket.send_json({
                    "status": "ASK",
                    "phase": "BRANDING",
                    "question": agent_result.next_question,
                    "context": state.profile.model_dump(exclude_none=True)
                })

            else:
                state.is_complete = True
                if answer:
                    prev_q = state.last_question if state.last_question else "Final Input"
                    state.history.append(BrandingTurn(
                        question=prev_q, answer=answer))

                save_branding_files(session_id, state.model_dump())
                branding_service.delete_state(session_id)

                await websocket.send_json({
                    "status": "COMPLETE",
                    "phase": "BRANDING",
                    "requirements": state.profile.model_dump(exclude_none=True)
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


@router.post("/branding/chat", response_model=BrandingResponse)
async def chat_branding(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Keep REST as fallback (existing logic)
    form = await request.form()
    session_id = form.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    answer = form.get("answer")

    search_pattern = settings.EXPORT_JSON_DIR / \
        f"requirements_{session_id}_*.json"
    if glob.glob(str(search_pattern)):
        raise HTTPException(
            status_code=400, detail="this project requirements are already completed")

    state = branding_service.get_state(session_id)
    is_empty_input = (not answer or not str(answer).strip())
    if state.last_question and is_empty_input:
        raise HTTPException(
            status_code=400, detail=f"session {session_id} is already started with last question {state.last_question}")

    if state.is_complete:
        return BrandingCompleteResponse(status="COMPLETE", phase="BRANDING", requirements=state.profile.model_dump(exclude_none=True))

    agent_result = agent.run(state.profile, answer, state.last_question)
    state.profile = agent_result.updated_profile

    if not agent_result.is_complete and agent_result.next_question:
        if answer:
            prev_q = state.last_question if state.last_question else "[Initial Inquiry]"
            state.history.append(BrandingTurn(question=prev_q, answer=answer))
        state.last_question = agent_result.next_question
        branding_service.save_state(session_id, state)
        return BrandingAskResponse(status="ASK", phase="BRANDING", question=agent_result.next_question, context=state.profile.model_dump(exclude_none=True))
    else:
        state.is_complete = True
        if answer:
            prev_q = state.last_question if state.last_question else "Final Input"
            state.history.append(BrandingTurn(question=prev_q, answer=answer))
        save_branding_files(session_id, state.model_dump())
        branding_service.delete_state(session_id)
        return BrandingCompleteResponse(status="COMPLETE", phase="BRANDING", requirements=state.profile.model_dump(exclude_none=True))
