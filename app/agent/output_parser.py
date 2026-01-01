from pydantic import BaseModel
from typing import Any, Dict, Optional, Literal
from app.agent.intents import IntentType


class PendingIntentModel(BaseModel):
    type: IntentType
    role: Optional[str] = None


class AskOutput(BaseModel):
    status: Literal["ASK"]
    phase: str
    question: str
    updated_context: Dict[str, Any]
    pending_intent: PendingIntentModel
    additional_questions_asked: int = 0


class CompleteOutput(BaseModel):
    status: Literal["COMPLETE"]
    phase: Literal["COMPLETE"]
    requirements: Dict[str, Any]


class AgentOutput(BaseModel):
    output: AskOutput | CompleteOutput
