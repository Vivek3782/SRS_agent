from datetime import datetime
from app.schemas.state import SessionState


def initialize_state(existing_state: dict | None) -> SessionState:
    """
    Normalize Redis data into a valid SessionState.
    """
    if not existing_state:
        return SessionState(
            phase="INIT",
            context={},
            additional_questions_asked=0
        )

    return SessionState(**existing_state)


def build_ask_state(
    *,
    phase: str,
    context: dict,
    question: str,
    pending_intent: dict | None,
    additional_questions_asked: int
) -> dict:
    """
    Build the state object to persist on ASK.
    """
    state = SessionState(
        phase=phase,
        context=context,
        last_question={
            "text": question,
            "asked_at": datetime.utcnow().isoformat()
        },
        pending_intent=pending_intent,
        additional_questions_asked=additional_questions_asked
    )

    return state.model_dump()
