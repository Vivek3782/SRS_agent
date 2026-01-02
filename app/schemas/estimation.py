from pydantic import BaseModel, field_validator
from typing import List, Optional


class EstimateRequest(BaseModel):
    session_id: str

    @field_validator('session_id')
    @classmethod
    def check_existing_estimation(cls, v: str) -> str:
        from app.config import settings
        import glob

        estimated_pages_dir = settings.BASE_DIR / "estimated_pages_json"
        search_pattern = estimated_pages_dir / f"sitemap_{v}_*.json"

        if glob.glob(str(search_pattern)):
            raise ValueError("You already created a estimation")
        return v

class DeleteEstimationRequest(BaseModel):
    session_id: str

    @field_validator('session_id')
    @classmethod
    def check_existing_estimation(cls, v: str) -> str:
        from app.config import settings
        import glob

        estimated_pages_dir = settings.BASE_DIR / "estimated_pages_json"
        search_pattern = estimated_pages_dir / f"sitemap_{v}_*.json"

        if not glob.glob(str(search_pattern)):
            raise ValueError("No estimation found for session_id")
        return v


class PageSchema(BaseModel):
    name: str
    description: str
    features: List[str] = []
    url: Optional[str] = None
    complexity: str = "Medium"
    notes: str = ""


class SiteMapResponse(BaseModel):
    business_type: str
    pages: List[PageSchema]
