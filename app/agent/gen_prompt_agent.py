import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.gen_prompts import PromptGenerationOutput

PROMPT_GEN_SYSTEM_PROMPT = """
You are a Lead Product Engineer and Prompt Specialist.
Your task is to take a high-level Sitemap and expand it into detailed Generative AI Prompts.

**INPUT:** A JSON list of pages/screens (Sitemap).

**OUTPUT:**
Generate a JSON object containing the Project Name and a list of detailed "Screens".

**JSON STRUCTURE (Strict Enforcement):**
{
  "project_name": "Inferred Project Name",
  "screens": [
    {
      "screen_name": "Name of the screen",
      "complexity": "Low" | "Medium" | "High",
      "notes": "Technical notes...",
      "prompts": {
        "developer": "Act as a React/Node Expert...",
        "designer": "Act as a UI Designer...",
        "copywriter": "Act as a Content Strategist..."
      }
    }
  ]
}

**CRITICAL RULES:**
1. Use the key "screens" (NOT "pages").
2. Do not use Markdown formatting (no ```json).
3. Ensure every screen from the input is included.
"""

class PromptGenerationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.5, 
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def generate(self, sitemap_data: dict) -> PromptGenerationOutput:
        context_str = json.dumps(sitemap_data, indent=2, ensure_ascii=False)

        messages = [
            SystemMessage(content=PROMPT_GEN_SYSTEM_PROMPT),
            HumanMessage(content=f"SITEMAP DATA:\n{context_str}")
        ]

        response = self.llm.invoke(messages)
        content = response.content.strip()

        if "```" in content:
            pattern = r"```(?:json)?\s*(.*?)\s*```"
            match = re.search(pattern, content, re.DOTALL)
            content = match.group(1) if match else content.replace("```json", "").replace("```", "").strip()
        
        content = re.sub(r",\s*([\]}])", r"\1", content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Failed. Raw content: {content}")
            raise e

        if "screens" not in data and "pages" in data:
            data["screens"] = data.pop("pages")
        
        if "project_name" not in data:
            data["project_name"] = sitemap_data.get("business_type", "Project")

        for screen in data.get("screens", []):
            if "screen_name" not in screen and "name" in screen:
                screen["screen_name"] = screen.pop("name")

        try:
            return PromptGenerationOutput.model_validate(data)
        except Exception as e:
            print(f"Validation Error. Data: {data}")
            raise e