from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.gen_prompt_export_service import save_prompts_data
from app.agent.gen_prompt_agent import PromptGenerationAgent
from app.schemas.gen_prompts import PromptGenerationOutput
from app.models.user import User
from app.api.deps import get_current_user

from app.config import settings
import glob

router = APIRouter()
agent = PromptGenerationAgent()


class PromptRequest(BaseModel):
    session_id: str


@router.post("/generate-prompts", response_model=PromptGenerationOutput)
def generate_prompts(request: PromptRequest, current_user: User = Depends(get_current_user)):

    from app.services.export_service import ESTIMATED_PAGES_DIR
    import glob
    import os
    import json

    search_sitemap = ESTIMATED_PAGES_DIR / \
        f"sitemap_{request.session_id}_*.json"
    sitemap_files = glob.glob(str(search_sitemap))

    if not sitemap_files:
        raise HTTPException(
            status_code=404, detail="Sitemap not found. Please run /estimate first.")

    search_prompts = settings.EXPORT_PROMPTS_DIR / \
        f"prompts_{request.session_id}_*.json"
    prompt_files = glob.glob(str(search_prompts))

    if prompt_files:
        raise HTTPException(
            status_code=400, detail="Prompts already generated.")

    latest_sitemap = max(sitemap_files, key=os.path.getctime)

    with open(latest_sitemap, "r") as f:
        sitemap_data = json.load(f)

    # 3. Fetch Branding Data (to enrich prompts)
    from app.services.export_service import get_branding_export
    branding_data = get_branding_export(request.session_id)

    # 4. Run Agent with enriched context
    result = agent.generate(request.session_id, sitemap_data, branding_data)

    save_prompts_data(request.session_id, result.model_dump())

    return result
