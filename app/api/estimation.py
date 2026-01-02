from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.export_service import get_latest_requirements_file, save_estimated_sitemap, get_branding_export, append_screens_to_excel
from app.agent.estimator import PageEstimationAgent
from app.schemas.estimation import SiteMapResponse, EstimateRequest, DeleteEstimationRequest

router = APIRouter()
estimator = PageEstimationAgent()


class EstimateRequest(BaseModel):
    session_id: str


@router.post("/estimate", response_model=SiteMapResponse)
def generate_sitemap(request: EstimateRequest):
    # 1. Fetch SRS Data (Technical Requirements)
    srs_filepath, srs_data = get_latest_requirements_file(request.session_id)
    if not srs_filepath or not srs_data:
        raise HTTPException(
            status_code=404, detail="SRS Requirements not found.")

    # 2. Fetch Branding Data (Company Profile)
    branding_data = get_branding_export(request.session_id)

    if not branding_data:
        raise HTTPException(
            status_code=400,
            detail="Branding is required for this session id. Please complete the branding phase first."
        )

    # 3. RUN ESTIMATOR with BOTH inputs
    try:
        # We pass both dictionaries to the agent
        sitemap = estimator.estimate(srs_data, branding_data)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"AI Estimation failed: {str(e)}")

    # 4. Save the result
    save_estimated_sitemap(request.session_id, sitemap.model_dump())

    try:
        append_screens_to_excel(request.session_id, sitemap.model_dump())
    except Exception as e:
        print(f"Failed to update Excel: {e}")

    return sitemap


@router.delete("/estimate", response_model=SiteMapResponse)
def delete_estimation(request: DeleteEstimationRequest):
    from app.services.export_service import delete_estimated_sitemap

    try:
        sitemap = delete_estimated_sitemap(request.session_id)
        if not sitemap:
            raise HTTPException(
                status_code=404,
                detail=f"No estimation found for session_id: {request.session_id}"
            )
        return sitemap
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Deletion failed: {str(e)}")
