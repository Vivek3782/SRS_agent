from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

# --- Internal Data Models ---


class CompanyProfile(BaseModel):
    name: Optional[str] = None
    slogan: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None


class BrandingTurn(BaseModel):
    question: str
    answer: str


class BrandingState(BaseModel):
    profile: CompanyProfile = CompanyProfile()
    history: List[BrandingTurn] = []
    is_complete: bool = False
    last_question: Optional[str] = None

# --- Response Models ---


class BrandingAskResponse(BaseModel):
    status: str = "ASK"
    phase: str = "BRANDING"
    question: str
    context: Dict[str, Any]  # Dynamic dictionary


class BrandingCompleteResponse(BaseModel):
    status: str = "COMPLETE"
    phase: str = "BRANDING"
    requirements: Dict[str, Any]


BrandingResponse = Union[BrandingAskResponse, BrandingCompleteResponse]
