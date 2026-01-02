import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.estimation import SiteMapResponse

# ✅ FIX: General prompt that handles ANY input structure
ESTIMATION_SYSTEM_PROMPT = """
You are an expert UX Architect and Product Manager.
You will be provided with a raw JSON object containing the "Software Requirements" for a project.

**CONTEXT:** The input JSON is dynamic and unstructured. It collects data from a conversation. 
- It MAY contain keys like 'project_description', 'roles', 'system_features', 'context', or 'summary'.
- It MAY contain scattered strings or lists defining what the software does.
- It MAY be incomplete.

**YOUR TASK:**
1. **Scan the entire JSON structure** to understand the intent of the software.
2. **Infer the Business Type** (e.g., "E-commerce", "Internal Tool", "SaaS") based on whatever clues you find.
3. **Deduce the Site Map**: Based on mentioned roles (e.g., "Admin" implies an Admin Panel) and features (e.g., "Login" implies Auth pages), generate a list of necessary pages.
4. **Output strictly valid JSON** matching the schema below.

**JSON OUTPUT STRUCTURE:**
{
  "business_type": "Inferred Business Type",
  "pages": [
    {
      "name": "Page Name",
      "description": "Why this page exists",
      "features": ["Feature 1", "Feature 2 found in input"]
    }
  ]
}

**CRITICAL RULES:**
- Do NOT use Markdown formatting (no ```json).
- Return ONLY the JSON object.
- If the input is empty or nonsensical, generate a generic sitemap for a "Standard Web Application" and note this in the description.
"""

class PageEstimationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def estimate(self, srs_data: dict) -> SiteMapResponse:
        # 1. Serialization Safety
        try:
            context_str = json.dumps(srs_data, indent=2, ensure_ascii=False)
        except Exception:
            context_str = str(srs_data)

        messages = [
            SystemMessage(content=ESTIMATION_SYSTEM_PROMPT),
            HumanMessage(content=f"RAW SRS DATA:\n\n{context_str}")
        ]

        response = self.llm.invoke(messages)
        content = response.content.strip()

        # 2. Markdown Cleanup
        if "```" in content:
            pattern = r"```(?:json)?\s*(.*?)\s*```"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                content = content.replace("```json", "").replace("```", "").strip()
        
        # 3. Trailing Comma Cleanup
        content = re.sub(r",\s*([\]}])", r"\1", content)

        # 4. Validation
        try:
            return SiteMapResponse.model_validate_json(content)
        except Exception as e:
            print(f"Details: AI Output validation failed.\nRaw Content: {content[:500]}...") 
            raise e