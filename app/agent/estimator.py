import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.estimation import SiteMapResponse

ESTIMATION_SYSTEM_PROMPT = """
You are an expert UX Architect and Product Manager.
You will be provided with two data sources:
1. **SRS (Software Requirements):** The functional scope, roles, and features.
2. **BRANDING PROFILE:** The company name, audience, and voice.

**YOUR TASK:**
Combine these inputs to generate a comprehensive Sitemap.

**LOGIC:**
1. **Business Type:** Infer from SRS + Branding (e.g., "SRS says cars" + "Branding says tourists" = "Car Rental for Tourists").
2. **Page Naming:** Use the Company Name from Branding to label pages (e.g., "About [Company Name]").
3. **Audience Alignment:** If Branding says "Elderly Users", ensure page descriptions mention simplicity.
4. **Standard Pages:** Always include Home, About, Contact, etc., tailored to the brand.

**OUTPUT:**
Return strictly valid JSON matching the schema.
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
        # 1. Serialize both inputs safely
        try:
            srs_str = json.dumps(srs_data, indent=2, ensure_ascii=False)
        except:
            srs_str = str(srs_data)

        branding_str = "No Branding Data Available"
        if branding_data:
            try:
                branding_str = json.dumps(branding_data, indent=2, ensure_ascii=False)
            except:
                branding_str = str(branding_data)

        # 2. Build the Dual-Input Prompt
        messages = [
            SystemMessage(content=ESTIMATION_SYSTEM_PROMPT),
            HumanMessage(content=f"""
            === INPUT 1: BRANDING PROFILE ===
            {branding_str}

            === INPUT 2: SRS REQUIREMENTS ===
            {srs_str}
            """)
        ]

        response = self.llm.invoke(messages)
        content = response.content.strip()

        # 3. Cleanup & Validate (Standard logic)
        if "```" in content:
            pattern = r"```(?:json)?\s*(.*?)\s*```"
            match = re.search(pattern, content, re.DOTALL)
            content = match.group(1) if match else content.replace("```json", "").replace("```", "").strip()
        
        content = re.sub(r",\s*([\]}])", r"\1", content)

        try:
            return SiteMapResponse.model_validate_json(content)
        except Exception as e:
            print(f"Validation Failed. Content: {content[:200]}...")
            raise e