from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    session_id: str
    answer: Optional[Any] = None
