from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.gen_prompt_export_service import save_prompts_data
from app.agent.gen_prompt_agent import PromptGenerationAgent
from app.schemas.gen_prompts import PromptGenerationOutput
from app.models.user import User
from app.api.deps import get_current_user

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

    search = ESTIMATED_PAGES_DIR / f"sitemap_{request.session_id}_*.json"
    files = glob.glob(str(search))

    if not files:
        raise HTTPException(
            status_code=404, detail="Sitemap not found. Please run /estimate first.")

    latest_sitemap = max(files, key=os.path.getctime)

    with open(latest_sitemap, "r") as f:
        sitemap_data = json.load(f)

    result = agent.generate(sitemap_data)

    save_prompts_data(request.session_id, result.model_dump())

    return result
