import os
import json
import glob
from datetime import datetime
from openpyxl import Workbook
from app.config import settings

# 1. Define Separate Directories
EXPORT_XLSX_DIR = settings.BASE_DIR / "exports_xlsx"
EXPORT_JSON_DIR = settings.BASE_DIR / "exports_json"
ESTIMATED_PAGES_DIR = settings.BASE_DIR / "estimated_pages_json"

# 2. Ensure Both Directories Exist
os.makedirs(EXPORT_XLSX_DIR, exist_ok=True)
os.makedirs(EXPORT_JSON_DIR, exist_ok=True)
os.makedirs(ESTIMATED_PAGES_DIR, exist_ok=True)


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
        s = item.get("session_id") if isinstance(
            item, dict) else item.session_id

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


def get_latest_requirements_file(session_id: str):
    """
    Reads the SOURCE requirements from 'exports_json'.
    """
    search_pattern = EXPORT_JSON_DIR / f"requirements_{session_id}_*.json"
    files = glob.glob(str(search_pattern))

    if not files:
        return None, None

    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)

    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return latest_file, data
    except Exception as e:
        print(f"Error reading file {latest_file}: {e}")
        return latest_file, None


def save_estimated_sitemap(session_id: str, sitemap_data: dict):
    """
    Saves the generated sitemap to the NEW 'estimated_pages_json' folder.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sitemap_{session_id}_{timestamp}.json"

    filepath = ESTIMATED_PAGES_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sitemap_data, f, indent=4, ensure_ascii=False)

    return filepath

from openpyxl import load_workbook

def append_screens_to_excel(session_id: str, sitemap_data: dict):
    # 1. Find the existing Excel file (Scanning EXPORT_XLSX_DIR)
    # (Assuming you have a function to find the file, similar to get_latest_requirements_file)
    search_pattern = EXPORT_XLSX_DIR / f"session_{session_id}_*.xlsx"
    files = glob.glob(str(search_pattern))
    
    if not files:
        print("No Excel file found to append screens.")
        return None
        
    latest_file = max(files, key=os.path.getctime)
    
    # 2. Load Workbook
    wb = load_workbook(latest_file)
    
    # 3. Manage "Screens" Sheet
    if "Screens" in wb.sheetnames:
        # Option A: Delete and recreate (simplest for updates)
        del wb["Screens"]
    
    ws = wb.create_sheet("Screens")
    
    # 4. Write Headers
    headers = ["Screen Name", "Complexity", "Notes", "Description", "Features"]
    ws.append(headers)
    
    # 5. Write Data
    for page in sitemap_data.get("pages", []):
        # Handle list of features for CSV-like cell
        features_str = ", ".join(page.get("features", []))
        
        ws.append([
            page.get("name"),
            page.get("complexity", "Medium"),
            page.get("notes", ""),
            page.get("description", ""),
            features_str
        ])
        
    # 6. Save
    wb.save(latest_file)
    return latest_file


def delete_estimated_sitemap(session_id: str):
    """
    Deletes the estimated sitemap from the NEW 'estimated_pages_json' folder.
    """
    search_pattern = ESTIMATED_PAGES_DIR / f"sitemap_{session_id}_*.json"
    files = glob.glob(str(search_pattern))

    if not files:
        return None

    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)

    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        os.remove(latest_file)
        return data
    except Exception as e:
        print(f"Error deleting file {latest_file}: {e}")
        return None

#for branding 
BRANDING_JSON_DIR = settings.BASE_DIR / "exports_branding_json"
BRANDING_XLSX_DIR = settings.BASE_DIR / "exports_branding_xlsx"

os.makedirs(BRANDING_JSON_DIR, exist_ok=True)
os.makedirs(BRANDING_XLSX_DIR, exist_ok=True)

def save_branding_files(session_id: str, state_data: dict):
    """
    Saves both JSON profile and Excel transcript.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Save JSON Profile
    json_filename = f"branding_profile_{session_id}_{timestamp}.json"
    json_path = BRANDING_JSON_DIR / json_filename
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(state_data["profile"], f, indent=4)

    # 2. Save Excel Transcript
    wb = Workbook()
    ws = wb.active
    ws.title = "Branding Chat"
    ws.append(["Question", "User Answer"]) # Headers

    history = state_data.get("history", [])
    for turn in history:
        ws.append([turn["question"], turn["answer"]])

    xlsx_filename = f"branding_chat_{session_id}_{timestamp}.xlsx"
    xlsx_path = BRANDING_XLSX_DIR / xlsx_filename
    wb.save(xlsx_path)

    return json_path, xlsx_path

BRANDING_JSON_DIR = settings.BASE_DIR / "exports_branding_json"
def get_branding_export(session_id: str) -> dict | None:
    """
    Checks if a completed Branding Profile exists for this session.
    Returns the profile data dict if found, otherwise None.
    """
    # Pattern: branding_profile_{session_id}_{timestamp}.json
    search_pattern = BRANDING_JSON_DIR / f"branding_profile_{session_id}_*.json"
    files = glob.glob(str(search_pattern))
    
    if not files:
        return None
    
    # Get the latest one if multiple exist
    latest_file = max(files, key=os.path.getctime)
    
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

