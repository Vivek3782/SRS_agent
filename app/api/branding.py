from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.branding_service import branding_service
from app.services.export_service import save_branding_files
from app.agent.branding_agent import BrandingAgent
from app.schemas.branding import BrandingResponse, BrandingTurn
from typing import Optional, Any

router = APIRouter()
agent = BrandingAgent()

class BrandingRequest(BaseModel):
    session_id: str
    answer: Optional[Any] = None

@router.post("/branding/chat", response_model=BrandingResponse)
def chat_branding(request: BrandingRequest):
    # 1. Load State (or create new)
    state = branding_service.get_state(request.session_id)

    # 2. Check if already complete
    if state.is_complete:
        return BrandingResponse(status="COMPLETE", profile=state.profile)

    # 3. If this is a reply (not the first load), record the history
    # Note: We need to know what the *last* question was to record the pair.
    # For simplicity, we just run the agent first to process the answer.
    
    agent_result = agent.run(state.profile, request.answer)

    # 4. Update State Logic
    if request.answer and state.history: 
        # Update the PREVIOUS turn with this answer? 
        # Actually, simpler approach: Record the interaction that JUST happened.
        # But we don't have the question yet.
        # Let's assume the Frontend sends the answer to the *previous* question.
        pass

    # Update Profile
    state.profile = agent_result.updated_profile

    # If the agent asked a question, we are still in "ASK" mode
    if not agent_result.is_complete and agent_result.next_question:
        # Record this turn (User Answer -> New Question? No, usually Question -> Answer)
        # To keep transcript simple:
        if request.answer:
            # We don't have the text of the question asked *before* this answer easily 
            # unless we stored it. But for now, let's just log the flow.
            state.history.append(BrandingTurn(
                question="[Previous Question]", 
                answer=request.answer
            ))
        
        # Save 'next_question' so we can log it next time? 
        # Alternatively, just append the question now with empty answer?
        # Let's append the NEW question to history to be filled later? 
        # No, easier: Just append the answer to the list.
        
        branding_service.save_state(request.session_id, state)
        
        return BrandingResponse(
            status="ASK",
            question=agent_result.next_question,
            profile=state.profile
        )

    # 5. Handle Completion
    else:
        state.is_complete = True
        
        # Capture final answer if any
        if request.answer:
             state.history.append(BrandingTurn(question="Final Input", answer=request.answer))

        # Save to Disk (JSON + XLSX)
        save_branding_files(request.session_id, state.model_dump())
        
        # Clean up Redis
        branding_service.delete_state(request.session_id)

        return BrandingResponse(
            status="COMPLETE",
            profile=state.profile
        )