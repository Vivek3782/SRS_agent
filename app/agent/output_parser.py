from pydantic import BaseModel, RootModel
from typing import Any, Dict, Optional, Literal, Union
from app.agent.intents import IntentType


class PendingIntentModel(BaseModel):
    type: IntentType
    role: Optional[str] = None


class AskOutput(BaseModel):
    status: Literal["ASK", "REJECT"]
    phase: Literal[
        "SCOPE_DEFINITION",
        "INIT",
        "BUSINESS",
        "FUNCTIONAL",
        "DESIGN",
        "NON_FUNCTIONAL",
        "ADDITIONAL"
    ]

    question: str
    updated_context: Dict[str, Any]
    pending_intent: PendingIntentModel
    additional_questions_asked: int = 0

    model_config = {
        "extra": "forbid"
    }


class CompleteOutput(BaseModel):
    status: Literal["COMPLETE"]
    phase: Literal["COMPLETE"]
    requirements: Dict[str, Any]

    model_config = {
        "extra": "forbid"
    }


class AgentOutput(RootModel[Union[AskOutput, CompleteOutput]]):

    def unwrap(self):
        return self.root
