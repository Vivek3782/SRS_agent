import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.estimation import SiteMapResponse
from fastapi import HTTPException

ESTIMATION_SYSTEM_PROMPT = """
You are an expert UX Architect.
You will be provided with two data sources:
1. **SRS (Software Requirements)**
2. **BRANDING PROFILE** (Includes mission, voice, reference URLs, and color schemes)

**YOUR TASK:**
Generate a comprehensive Sitemap JSON.

**STRICT JSON OUTPUT STRUCTURE:**
You must return a SINGLE JSON object with exactly two keys: "business_type" and "pages".

{
  "business_type": "Inferred Business Type (e.g., SaaS Platform)",
  "pages": [
    {
      "name": "Page Name (e.g. Home)",
      "description": "Why this page exists",
      "features": ["Feature 1", "Feature 2"],
      "url": "/home",
      "complexity": "Medium",
      "notes": ""
    }
  ]
}

**CRITICAL RULES:**
1. **NO 'sitemap' KEY:** The root object must ONLY have "business_type" and "pages". Do not wrap them in another object.
2. **Page Naming:** Use the Company Name from Branding (e.g., "About Acme").
3. **Standard Pages:** Always include Home, About, Contact.
4. **Markdown:** Do NOT use markdown formatting.
5. **Complexity Estimation:** For each page, estimate implementation complexity (Low, Medium, High) based on the number of features.
6. **Notes:** Add brief tech notes (e.g., "Requires Auth Middleware").
7. **Reference Alignment:** If the Branding Profile contains reference URLs (Agency or External), analyze them to infer required pages, specialized layouts, or specific functionality mentioned in those references.
"""


class PageEstimationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.2,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

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
            response = self.llm.invoke(messages)
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
