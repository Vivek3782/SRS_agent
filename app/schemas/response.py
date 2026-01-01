from pydantic import BaseModel
from typing import Any, Dict, Optional


class AskResponse(BaseModel):
    status: str
    phase: str
    question: str
    context: Dict[str, Any]


class CompleteResponse(BaseModel):
    status: str
    requirements: Dict[str, Any]
