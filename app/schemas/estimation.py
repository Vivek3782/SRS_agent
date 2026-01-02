from pydantic import BaseModel
from typing import List, Optional

class PageSchema(BaseModel):
    name: str
    description: str
    features: List[str] = [] 
    url: Optional[str] = None

class SiteMapResponse(BaseModel):
    business_type: str
    pages: List[PageSchema]