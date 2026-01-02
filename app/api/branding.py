from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.branding_service import branding_service
from app.services.export_service import save_branding_files
from app.agent.branding_agent import BrandingAgent
from app.schemas.branding import BrandingResponse, BrandingAskResponse, BrandingCompleteResponse, BrandingTurn
from typing import Optional, Any

router = APIRouter()
agent = BrandingAgent()


class BrandingRequest(BaseModel):
    session_id: str
    answer: Optional[Any] = None


@router.post("/branding/chat", response_model=BrandingResponse)
def chat_branding(request: BrandingRequest):
    # 1. Load State
    state = branding_service.get_state(request.session_id)

    # 2. Check if already complete
    if state.is_complete:
        return BrandingCompleteResponse(
            status="COMPLETE",
            phase="BRANDING",
            requirements=state.profile.model_dump(exclude_none=True)
        )

    # 3. Run Agent
    agent_result = agent.run(state.profile, request.answer)

    # 4. Update Profile
    state.profile = agent_result.updated_profile

    # 5. Handle "ASK" Status
    if not agent_result.is_complete and agent_result.next_question:
        if request.answer:
            # Use the stored previous question, or fallback if missing
            prev_q = state.last_question if state.last_question else "[Unknown Question]"

            state.history.append(BrandingTurn(
                question=prev_q,
                answer=request.answer
            ))

        state.last_question = agent_result.next_question
        branding_service.save_state(request.session_id, state)

        return BrandingAskResponse(
            status="ASK",
            phase="BRANDING",
            question=agent_result.next_question,
            # ✅ FIX: Use exclude_none=True to hide null fields
            context=state.profile.model_dump(exclude_none=True)
        )

    # 6. Handle "COMPLETE" Status
    else:
        state.is_complete = True

        if request.answer:
            prev_q = state.last_question if state.last_question else "Final Input"
            state.history.append(BrandingTurn(
                question=prev_q, answer=request.answer))

        save_branding_files(request.session_id, state.model_dump())
        branding_service.delete_state(request.session_id)

        return BrandingCompleteResponse(
            status="COMPLETE",
            phase="BRANDING",
            requirements=state.profile.model_dump(exclude_none=True)
        )
