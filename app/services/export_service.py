import os
from datetime import datetime
from openpyxl import Workbook
from app.config import settings

# Ensure an export directory exists
EXPORT_DIR = settings.BASE_DIR / "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def save_to_excel(session_id: str, history: list):
    """
    Saves the conversation history to an Excel file.
    Columns: Question | Answer | Timestamp | Customer ID
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Conversation Log"

    # 1. Create Headers
    headers = ["Question", "Answer", "Timestamp", "Customer ID"]
    ws.append(headers)

    # 2. Append Data
    for item in history:
        # item is a dict when coming from Redis/Pydantic dump
        ws.append([
            item["question"],
            item["answer"],
            item["timestamp"],
            item["session_id"]
        ])

    # 3. Save File
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{session_id}_{timestamp}.xlsx"
    filepath = EXPORT_DIR / filename
    
    wb.save(filepath)
    return filepath