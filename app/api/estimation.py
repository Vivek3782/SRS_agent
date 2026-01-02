from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.export_service import get_latest_requirements_file, save_estimated_sitemap
from app.agent.estimator import PageEstimationAgent
from app.schemas.estimation import SiteMapResponse

router = APIRouter()
estimator = PageEstimationAgent()

class EstimateRequest(BaseModel):
    session_id: str

@router.post("/estimate", response_model=SiteMapResponse)
def generate_sitemap(request: EstimateRequest):
    # 1. READ: Get the latest requirements from exports_json
    source_filepath, srs_data = get_latest_requirements_file(request.session_id)
    
    if not source_filepath or not srs_data:
        raise HTTPException(
            status_code=404, 
            detail=f"No requirements file found for session_id: {request.session_id}"
        )

    # 2. PROCESS: Run the AI Estimation
    try:
        sitemap = estimator.estimate(srs_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Estimation failed: {str(e)}")

    # 3. WRITE: Save to the NEW separate folder
    saved_path = save_estimated_sitemap(request.session_id, sitemap.model_dump())

    # 4. Return result (Client can see the path in logs or response headers if needed)
    return sitemap