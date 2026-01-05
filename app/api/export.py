import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from app.config import settings
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

EXPORT_XLSX_DIR = settings.BASE_DIR / "exports_xlsx"
EXPORT_JSON_DIR = settings.BASE_DIR / "exports_json"


def get_latest_file(directory: Path, session_id: str, extension: str) -> Path:
    """
    Helper to find the most recent file for a session_id in a directory.
    """
    files = list(directory.glob(f"*{session_id}*{extension}"))

    if not files:
        return None

    return max(files, key=os.path.getmtime)


@router.get("/export/xlsx/{session_id}")
def download_excel(session_id: str, current_user: User = Depends(get_current_user)):
    """
    Download the latest Excel log for the given session.
    """
    try:
        current_user= User.objects.get(id=current_user.id)
        if current_user.is_superuser==False:
            raise HTTPException(status_code=403, detail="User is not authorized to download Excel")
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    file_path = get_latest_file(EXPORT_XLSX_DIR, session_id, ".xlsx")

    if not file_path:
        raise HTTPException(
            status_code=404, detail="Excel file not found for this session")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/export/json/{session_id}")
def download_json(session_id: str, current_user: User = Depends(get_current_user)):
    """
    Download the latest JSON requirements for the given session.
    """
    try:
        current_user= User.objects.get(id=current_user.id)
        if current_user.is_superuser==False:
            raise HTTPException(status_code=403, detail="User is not authorized to download JSON")
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    file_path = get_latest_file(EXPORT_JSON_DIR, session_id, ".json")

    if not file_path:
        raise HTTPException(
            status_code=404, detail="JSON requirements not found for this session")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/json"
    )
