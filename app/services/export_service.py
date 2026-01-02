import os
import json
from datetime import datetime
from openpyxl import Workbook
from app.config import settings

# 1. Define Separate Directories
EXPORT_XLSX_DIR = settings.BASE_DIR / "exports_xlsx"
EXPORT_JSON_DIR = settings.BASE_DIR / "exports_json"

# 2. Ensure Both Directories Exist
os.makedirs(EXPORT_XLSX_DIR, exist_ok=True)
os.makedirs(EXPORT_JSON_DIR, exist_ok=True)

def save_to_excel(session_id: str, history: list):
    """
    Saves the conversation history to the 'exports_xlsx' folder.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Conversation Log"

    headers = ["Question", "Answer", "Timestamp", "Customer ID"]
    ws.append(headers)

    for item in history:
        # Handle both dict (from Redis) and object (from memory)
        q = item.get("question") if isinstance(item, dict) else item.question
        a = item.get("answer") if isinstance(item, dict) else item.answer
        t = item.get("timestamp") if isinstance(item, dict) else item.timestamp
        s = item.get("session_id") if isinstance(item, dict) else item.session_id
        
        ws.append([q, a, t, s])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{session_id}_{timestamp}.xlsx"
    
    # Save to XLSX Directory
    filepath = EXPORT_XLSX_DIR / filename
    wb.save(filepath)
    return filepath


def save_requirements(session_id: str, requirements: dict):
    """
    Saves the final requirements JSON to the 'exports_json' folder.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"requirements_{session_id}_{timestamp}.json"
    
    # Save to JSON Directory
    filepath = EXPORT_JSON_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(requirements, f, indent=4, ensure_ascii=False)
        
    return filepath