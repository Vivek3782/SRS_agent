import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.gen_prompts import PromptGenerationOutput, ScreenDetail

PROMPT_GEN_SYSTEM_PROMPT = """
You are a Lead Product Engineer and Prompt Specialist.
Your task is to take a Branding Profile and a specific Screen definition (from a Sitemap) and expand them into HIGHLY SPECIFIC Generative AI Prompts.

**MISSION:**
Convert the sitemap requirement for this specific screen into "ready-to-use" prompts for developers, designers, and copywriters. 
DO NOT be generic. Use ACTUAL facts from the Branding Profile (Company Name, Contact Info, Values, Brand Voice).

**INPUTS:**
1. **Branding Profile:** Context about the company (Name, Mission, Voice, Contact).
2. **Screen Definition:** The specific page details (Name, Features, Technical Notes, Complexity).

**OUTPUT SCHEMA (Strict JSON):**
{
  "screen_name": "Exact Name from Sitemap",
  "complexity": "Low" | "Medium" | "High",
  "notes": "Relevant technical notes",
  "prompts": {
    "developer": "Detailed implementation prompt. List ALL features for this screen. Specify React/Tailwind, state management, and API needs.",
    "designer": "Visual design prompt. Use brand colors, voice, and specified layout. Mention specific UI components.",
    "copywriter": "Content strategy prompt. MUST use 'Company Name', 'Contact Info', and 'Brand Voice' from branding. Write actual placeholder headings/CTAs."
  }
}

**CRITICAL RULES:**
1. **FACT INJECTION:** Instead of "add contact info", provide the ACTUAL contact details from branding.
2. **FEATURE FOCUS:** Ensure every feature mentioned in the screen definition is included in the developer prompt.
3. **BRAND ALIGNMENT:** Visual and content prompts must strictly follow the brand voice (e.g., if brand is 'Professional', prompts must be formal).
4. **NO MARKDOWN:** Return raw JSON only.
"""


class PromptGenerationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.2,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def generate(self, sitemap_data: dict, branding_data: dict | None = None) -> PromptGenerationOutput:
        # 1. Determine Project Name
        if branding_data and "company_name" in branding_data:
            project_name = branding_data["company_name"]
        else:
            project_name = sitemap_data.get("business_type", "Project")

        branding_context = json.dumps(
            branding_data, indent=2, ensure_ascii=False) if branding_data else "No branding data available."

        screens_output = []
        pages = sitemap_data.get("pages", [])

        print(
            f"Generating prompts for {len(pages)} screens for project: {project_name}")

        # 2. Iterate through screens one by one to avoid token limits
        for i, page_data in enumerate(pages):
            print(
                f"Processing screen {i+1}/{len(pages)}: {page_data.get('name')}")

            screen_prompts = self._generate_single_screen(
                branding_context, page_data)
            if screen_prompts:
                screens_output.append(screen_prompts)

        return PromptGenerationOutput(
            project_name=project_name,
            screens=screens_output
        )

    def _generate_single_screen(self, branding_context: str, page_data: dict) -> ScreenDetail | None:
        screen_context = json.dumps(page_data, indent=2, ensure_ascii=False)

        messages = [
            SystemMessage(content=PROMPT_GEN_SYSTEM_PROMPT),
            HumanMessage(
                content=f"BRANDING PROFILE:\n{branding_context}\n\nSCREEN DEFINITION:\n{screen_context}")
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()

            # Cleanup
            if "```" in content:
                pattern = r"```(?:json)?\s*(.*?)\s*```"
                match = re.search(pattern, content, re.DOTALL)
                content = match.group(1) if match else content.replace(
                    "```json", "").replace("```", "").strip()

            content = re.sub(r",\s*([\]}])", r"\1", content)
            data = json.loads(content)

            # Normalization
            if "screen_name" not in data and "name" in data:
                data["screen_name"] = data.pop("name")

            # Validation
            return ScreenDetail.model_validate(data)
        except Exception as e:
            print(
                f"Error generating prompts for screen: {page_data.get('name')}. Error: {e}")
            return None
