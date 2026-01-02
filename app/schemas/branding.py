from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# The data we are gathering
class CompanyProfile(BaseModel):
    name: Optional[str] = None
    slogan: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None

# One turn of conversation
class BrandingTurn(BaseModel):
    question: str
    answer: str

# The Response sent to Frontend
class BrandingResponse(BaseModel):
    status: str  # "ASK" or "COMPLETE"
    question: Optional[str] = None
    profile: Optional[CompanyProfile] = None

# The State stored in Redis
class BrandingState(BaseModel):
    profile: CompanyProfile = CompanyProfile()
    history: List[BrandingTurn] = []
    is_complete: bool = False