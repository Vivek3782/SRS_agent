from datetime import datetime
from app.schemas.state import SessionState


def initialize_state(existing_state: dict | None, branding_data: dict | None = None) -> SessionState:
    if not existing_state:
        # Pre-fill context from Branding Data if available
        initial_context = {}
        if branding_data:
            # Store branding info as background context for the agent to refer to
            # but do NOT pre-fill requirement fields like PROJECT_DESCRIPTION
            initial_context["company_profile"] = branding_data

        return SessionState(
            phase="INIT",
            context=initial_context,
            additional_questions_asked=0,
            history=[]
        )
    return SessionState(**existing_state)


def build_ask_state(
    *,
    phase: str,
    context: dict,
    question: str,
    pending_intent: dict | None,
    additional_questions_asked: int,
    history: list
) -> dict:
    state = SessionState(
        phase=phase,
        context=context,
        last_question={
            "text": question,
            "asked_at": datetime.utcnow().isoformat()
        },
        pending_intent=pending_intent,
        additional_questions_asked=additional_questions_asked,
        history=history
    )
    return state.model_dump()
