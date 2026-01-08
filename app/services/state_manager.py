from datetime import datetime
from app.schemas.state import SessionState


def initialize_state(existing_state: dict | None, branding_data: dict | None = None) -> SessionState:
    if not existing_state:
        return SessionState(
            phase="SCOPE_DEFINITION",
            context={},
            company_profile=branding_data,
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
    history: list,
    company_profile: dict | None = None
) -> dict:
    state = SessionState(
        phase=phase,
        context=context,
        company_profile=company_profile,
        last_question={
            "text": question,
            "asked_at": datetime.utcnow().isoformat()
        },
        pending_intent=pending_intent,
        additional_questions_asked=additional_questions_asked,
        history=history
    )
    return state.model_dump()
