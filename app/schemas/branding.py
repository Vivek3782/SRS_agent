from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

# --- Internal Data Models ---


class CompanyProfile(BaseModel):
    # Required fields
    name: Optional[str] = None
    target_audience: Optional[str] = None

    # Brand Identity
    mission: Optional[str] = None
    slogan: Optional[str] = None
    brand_voice: Optional[str] = None
    industry: Optional[str] = None

    # Company Details
    description: Optional[str] = None
    location: Optional[str] = None
    founding_year: Optional[int] = None

    # Contact Information
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    # Social Media
    # e.g., {"linkedin": "url", "twitter": "handle"}
    social_media: Optional[Dict[str, str]] = None

    # Optional UI/UX References
    agency_refresh_urls: Optional[List[str]] = None
    external_reference_urls: Optional[List[str]] = None
    color_scheme: Optional[Union[str, Any]] = None
    visual_references: Optional[List[str]] = None


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
