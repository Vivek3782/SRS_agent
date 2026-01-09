import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.estimation import SiteMapResponse
from fastapi import HTTPException
from app.utils.llm_utils import call_llm_with_fallback

ESTIMATION_SYSTEM_PROMPT = """
You are an expert UX Architect and Technical Business Analyst.
You will be provided with a **Requirements Registry (SRS)** and a **Branding Profile**.

**YOUR MISSION:**
Generate a structured Sitemap JSON that accurately reflects the intended project scope.

**SCOPE-BASED LOGIC (CRITICAL):**
1. **IF `project_scope` == "PARTIAL_UPDATE":**
   - YOU MUST ONLY generate pages that are explicitly mentioned as "new", "updated", or "refactored".
   - DO NOT include existing stable pages unless they are being modified.
   - The sitemap should represent the **target delta** of the project.
2. **IF `project_scope` == "NEW_BUILD" or missing:**
   - Generate a **complete, end-to-end sitemap** for the entire application.
   - Include all standard plumbing (Home, Login/Auth, Dashboard, Settings, etc.) plus the specific features requested.

**STRICT JSON OUTPUT STRUCTURE:**
Return a SINGLE JSON object:
{
  "business_type": "Inferred Business Type (e.g., Industrial MES)",
  "pages": [
    {
      "name": "Page Name",
      "description": "Functional purpose",
      "features": ["Atomic feature 1", "Atomic feature 2"],
      "url": "/page-path",
      "complexity": "Low" | "Medium" | "High",
      "notes": "Technical or UX notes (e.g., 'Requires real-time WebSocket')"
    }
  ]
}

**CRITICAL RULES:**
1. **NO 'sitemap' WRAPPER:** The root must have "business_type" and "pages" keys only.
2. **ATOMICTY:** Break large pages into sub-pages if they serve distinct user roles.
3. **DESIGN ALIGNMENT:** If Siemens IX or any design system is mentioned, ensure the page structure follows those industrial standards (e.g., clear separation of monitoring vs. configuration).
4. **NO MARKDOWN:** Return raw JSON only.
"""


class PageEstimationAgent:
    def __init__(self):
        pass

    def estimate(self, srs_data: dict, branding_data: dict | None) -> SiteMapResponse:
        # 1. Serialize inputs
        try:
            srs_str = json.dumps(srs_data, indent=2, ensure_ascii=False)
        except:
            srs_str = str(srs_data)

        branding_str = "No Branding Data Available"
        if branding_data:
            try:
                branding_str = json.dumps(
                    branding_data, indent=2, ensure_ascii=False)
            except:
                branding_str = str(branding_data)

        # 2. Invoke AI
        messages = [
            SystemMessage(content=ESTIMATION_SYSTEM_PROMPT),
            HumanMessage(content=f"""
            === INPUT 1: BRANDING PROFILE ===
            {branding_str}

            === INPUT 2: SRS REQUIREMENTS ===
            {srs_str}
            """)
        ]

        try:
            response = call_llm_with_fallback(messages, temperature=0.2)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        content = response.content.strip()

        # 3. Cleanup String (Markdown & Commas)
        if "```" in content:
            pattern = r"```(?:json)?\s*(.*?)\s*```"
            match = re.search(pattern, content, re.DOTALL)
            content = match.group(1) if match else content.replace(
                "```json", "").replace("```", "").strip()

        content = re.sub(r",\s*([\]}])", r"\1", content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}\nContent: {content}")
            raise e

        # Case A: Wrapped in "sitemap" key
        if "sitemap" in data and isinstance(data["sitemap"], list):
            data["pages"] = data.pop("sitemap")

        # Case B: Missing "business_type"
        if "business_type" not in data:
            data["business_type"] = "Standard Web Application"

        # Case C: If "pages" is missing but keys look like a list
        if "pages" not in data and isinstance(data, list):
            # AI returned just the list of pages
            data = {"business_type": "inferred", "pages": data}

        try:
            return SiteMapResponse.model_validate(data)
        except Exception as e:
            print(f"Validation Failed. Data: {data}")
            raise e
