from pydantic import BaseModel
from typing import Any, Dict, Optional


class PendingIntent(BaseModel):
    type: str
    role: Optional[str] = None


class LastQuestion(BaseModel):
    text: str
    asked_at: str


class SessionState(BaseModel):
    phase: str
    context: Dict[str, Any]

    last_question: Optional[LastQuestion] = None
    pending_intent: Optional[PendingIntent] = None

    additional_questions_asked: int = 0
