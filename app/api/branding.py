from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from pydantic import BaseModel
import glob
import os
from datetime import datetime
from app.config import settings
from app.services.branding_service import branding_service
from app.services.export_service import save_branding_files
from app.agent.branding_agent import BrandingAgent
from app.schemas.branding import BrandingResponse, BrandingAskResponse, BrandingCompleteResponse, BrandingTurn
from typing import Optional, Any, List
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()
agent = BrandingAgent()


class BrandingRequest(BaseModel):
    session_id: str
    answer: Optional[Any] = None


@router.post("/branding/chat", response_model=BrandingResponse)
async def chat_branding(
    session_id: str = Form(...),
    answer: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user)
):
    # 0. Check if session already has a final requirements export
    search_pattern = settings.EXPORT_JSON_DIR / \
        f"requirements_{session_id}_*.json"
    if glob.glob(str(search_pattern)):
        raise HTTPException(
            status_code=400, detail="this project requirements are already completed")

    # 1. Load State
    state = branding_service.get_state(session_id)

    # 2. Check if already started (running) but no answer/files provided
    is_empty_input = (answer is None or not answer.strip()
                      ) and (files is None or len(files) == 0)
    if state.last_question and is_empty_input:
        raise HTTPException(
            status_code=400, detail=f"session {session_id} is already started with last question {state.last_question}")

    # 3. Handle File Uploads
    if files:
        uploaded_info = []
        for file in files:
            file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            safe_filename = "".join(
                [c if c.isalnum() or c in "._-" else "_" for c in file.filename])
            filename = f"{file_timestamp}_{safe_filename}"

            session_upload_dir = settings.EXPORT_IMAGES_DIR / session_id
            os.makedirs(session_upload_dir, exist_ok=True)
            file_path = session_upload_dir / filename

            # Save the file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Update Profile
            if state.profile.visual_references is None:
                state.profile.visual_references = []

            # Store relative path for portability
            rel_path = f"exports_branding_images/{session_id}/{filename}"
            state.profile.visual_references.append(rel_path)
            uploaded_info.append(file.filename)

        # Inject info into the answer for the LLM
        upload_msg = f"[User uploaded {len(files)} images: {', '.join(uploaded_info)}]"
        if not answer:
            answer = upload_msg
        else:
            answer = f"{answer} {upload_msg}"

    # 4. Check if already complete
    if state.is_complete:
        return BrandingCompleteResponse(
            status="COMPLETE",
            phase="BRANDING",
            requirements=state.profile.model_dump(exclude_none=True)
        )

    # 5. Run Agent
    agent_result = agent.run(state.profile, answer, state.last_question)

    # 6. Update Profile from Agent Result
    state.profile = agent_result.updated_profile

    # 7. Handle "ASK" Status
    if not agent_result.is_complete and agent_result.next_question:
        if answer:
            prev_q = state.last_question if state.last_question else "[Initial Inquiry]"
            state.history.append(BrandingTurn(question=prev_q, answer=answer))

        state.last_question = agent_result.next_question
        branding_service.save_state(session_id, state)

        # Proactive Save for special fields (URLs/Images)
        special_fields = ["agency_refresh_urls",
                          "external_reference_urls", "visual_references", "color_scheme"]
        current_profile_dict = state.profile.model_dump()
        has_special_info = any(current_profile_dict.get(field)
                               for field in special_fields)

        if has_special_info:
            save_branding_files(session_id, state.model_dump())

        return BrandingAskResponse(
            status="ASK",
            phase="BRANDING",
            question=agent_result.next_question,
            context=state.profile.model_dump(exclude_none=True)
        )

    # 8. Handle "COMPLETE" Status
    else:
        state.is_complete = True
        if answer:
            prev_q = state.last_question if state.last_question else "Final Input"
            state.history.append(BrandingTurn(question=prev_q, answer=answer))

        save_branding_files(session_id, state.model_dump())
        branding_service.delete_state(session_id)

        return BrandingCompleteResponse(
            status="COMPLETE",
            phase="BRANDING",
            requirements=state.profile.model_dump(exclude_none=True)
        )
