import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import settings

router = APIRouter()

# Define paths (must match what is in export_service.py)
EXPORT_XLSX_DIR = settings.BASE_DIR / "exports_xlsx"
EXPORT_JSON_DIR = settings.BASE_DIR / "exports_json"

def get_latest_file(directory: Path, session_id: str, extension: str) -> Path:
    """
    Helper to find the most recent file for a session_id in a directory.
    """
    # Look for files matching the pattern (e.g., *session_123*.xlsx)
    files = list(directory.glob(f"*{session_id}*{extension}"))
    
    if not files:
        return None
        
    # Sort by modification time (newest first) and return the latest
    return max(files, key=os.path.getmtime)


@router.get("/export/xlsx/{session_id}")
def download_excel(session_id: str):
    """
    Download the latest Excel log for the given session.
    """
    file_path = get_latest_file(EXPORT_XLSX_DIR, session_id, ".xlsx")
    
    if not file_path:
        raise HTTPException(status_code=404, detail="Excel file not found for this session")
        
    return FileResponse(
        path=file_path, 
        filename=file_path.name, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/export/json/{session_id}")
def download_json(session_id: str):
    """
    Download the latest JSON requirements for the given session.
    """
    file_path = get_latest_file(EXPORT_JSON_DIR, session_id, ".json")
    
    if not file_path:
        raise HTTPException(status_code=404, detail="JSON requirements not found for this session")
        
    return FileResponse(
        path=file_path, 
        filename=file_path.name, 
        media_type="application/json"
    )