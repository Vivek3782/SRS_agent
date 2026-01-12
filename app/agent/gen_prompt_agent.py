import json
import re
import os
import glob
import base64
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.gen_prompts import PromptGenerationOutput, ScreenDetail
from app.utils.llm_utils import call_llm_with_fallback
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

IMAGE_ANALYSIS_SYSTEM_PROMPT = """
You are a Senior UI/UX Designer and Visual Analyst.
Your task is to analyze the provided image (logo, mockup, or style guide) and extract EVERY minute detail that a developer or designer would need.

**EXTRACT THE FOLLOWING:**
1. **COLORS:** Exact hex codes or descriptions of primary, secondary, and accent colors.
2. **TYPOGRAPHY:** Font styles, weights (bold/light), and estimated sizes or hierarchy (H1, H2, body).
3. **COMPONENTS:** Identify specific UI elements (buttons, inputs, cards, tables, navigation bars).
4. **LAYOUT:** Describe the grid structure, spacing, density, and alignment.
5. **VISUAL VIBE:** Describe the overall style (e.g., Industrial, Modern, Minimal, Corporate).
6. **ASSETS:** Identify icons, images, or specific graphic elements used.

Provide a concise but technical summary for each image.
"""

PROMPT_GEN_SYSTEM_PROMPT = """
You are a Lead Product Engineer and Prompt Specialist.
Your task is to take a Branding Profile and a specific Screen definition (from a Sitemap) and expand them into HIGHLY SPECIFIC Generative AI Prompts.

**MISSION:**
Convert the sitemap requirement for this specific screen into "ready-to-use" prompts for developers, designers, and copywriters. 
DO NOT be generic. Use ACTUAL facts from the Branding Profile and Design Requirements (Company Name, Contact Info, Brand Voice, Color Schemes, **Current App URL**, and **Inspiration/Style References**).

**INPUTS:**
1. **Branding Profile:** Context about the company (Name, Mission, Voice).
2. **Design Requirements:** Detailed visual preferences, **Current App URL** (for refactoring context), and **Inspiration Sources** (for style/behavior references).
3. **Screen Definition:** The specific page details (Name, Features, Technical Notes, Complexity).

**OUTPUT SCHEMA (Strict JSON):**
{
  "screen_name": "Exact Name from Sitemap",
  "complexity": "Low" | "Medium" | "High",
  "notes": "Relevant technical notes",
  "prompts": {
    "developer": "Detailed implementation prompt. Specify React/Tailwind, state management, and API needs. If a 'Current App URL' is provided, remind the dev this is a refactor of that specific page. Include relevant 'Inspiration URLs' for behavior.",
    "designer": "Visual design prompt. Use specified color schemes and brand voice. Focus on the style found in the 'Inspiration URLs' and ensure consistency with asset analysis.",
    "copywriter": "Content strategy prompt. MUST use 'Company Name', 'Contact Info', and 'Brand Voice'. Write placeholder headings/CTAs aligning with the mission."
  }
}

**CRITICAL RULES:**
1. **FACT INJECTION:** Instead of "add contact info", provide the ACTUAL contact details, color codes, and specific reference links.
2. **FEATURE FOCUS:** Ensure every feature mentioned in the screen definition is included in the developer prompt.
3. **BRAND ALIGNMENT:** Visual and content prompts must strictly follow the brand voice and color palette.
4. **NO MARKDOWN:** Return raw JSON only.
"""


class PromptGenerationAgent:
    def __init__(self):
        pass

    def generate(self, session_id: str, sitemap_data: dict, branding_data: dict | None = None) -> PromptGenerationOutput:
        # 1. Determine Project Name
        if branding_data and "company_name" in branding_data:
            project_name = branding_data["company_name"]
        else:
            project_name = sitemap_data.get("business_type", "Project")

        branding_context = json.dumps(
            branding_data, indent=2, ensure_ascii=False) if branding_data else "No branding data available."

        # 2. Perform Image Analysis if images exist
        visual_context = self._analyze_images(session_id)

        screens_output = []
        pages = sitemap_data.get("pages", [])

        print(
            f"Generating prompts for {len(pages)} screens for project: {project_name}")

        # 3. Iterate through screens one by one to avoid token limits
        import time
        for i, page_data in enumerate(pages):
            print(
                f"Processing screen {i+1}/{len(pages)}: {page_data.get('name')}")

            # Retry logic for individual screen generation
            max_retries = 3
            screen_prompts = None
            for attempt in range(max_retries):
                screen_prompts = self._generate_single_screen(
                    branding_context, visual_context, page_data)

                if screen_prompts:
                    break

                if attempt < max_retries - 1:
                    print(
                        f"Retrying screen '{page_data.get('name')}' (Attempt {attempt + 2}/{max_retries})...")
                    time.sleep(2)  # Wait 2 seconds before retry

            if screen_prompts:
                screens_output.append(screen_prompts)

            # Tiny delay to avoid aggressive rate limiting
            time.sleep(0.1)

        return PromptGenerationOutput(
            project_name=project_name,
            screens=screens_output
        )

    def _generate_single_screen(self, branding_context: str, visual_context: str, page_data: dict) -> ScreenDetail | None:
        screen_context = json.dumps(page_data, indent=2, ensure_ascii=False)

        messages = [
            SystemMessage(content=PROMPT_GEN_SYSTEM_PROMPT),
            HumanMessage(
                content=f"BRANDING PROFILE:\n{branding_context}\n\nVISUAL ASSETS ANALYSIS:\n{visual_context}\n\nSCREEN DEFINITION:\n{screen_context}")
        ]

        try:
            response = call_llm_with_fallback(messages, temperature=0.2)
            raw_content = response.content.strip()

            # Use robust cleaning utility
            from app.utils.llm_utils import clean_json_content
            cleaned_content = clean_json_content(raw_content)

            try:
                data = json.loads(cleaned_content)
            except json.JSONDecodeError:
                # Fallback: if it still fails, try to find the first { and last }
                start_idx = cleaned_content.find("{")
                end_idx = cleaned_content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    cleaned_content = cleaned_content[start_idx:end_idx+1]
                data = json.loads(cleaned_content)

            # Normalization
            if "screen_name" not in data and "name" in data:
                data["screen_name"] = data.pop("name")

            # Validation
            return ScreenDetail.model_validate(data)
        except Exception as e:
            print(
                f"Error generating prompts for screen: {page_data.get('name')}. Error: {e}")
            return None

    def _analyze_images(self, session_id: str) -> str:
        """
        Scans for images in the session folder and uses Gemini to analyze them.
        """
        image_dir = settings.EXPORT_IMAGES_DIR / session_id
        if not os.path.exists(image_dir):
            return "No visual assets found."

        image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(str(image_dir / ext)))

        if not image_files:
            return "No visual assets found."

        print(
            f"Analyzing {len(image_files)} images for session {session_id}...")

        analysis_results = []

        # Use Gemini 2.0 Flash for Image Analysis via OpenRouter
        gemini_vision = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.1
        )

        for img_path in image_files:
            try:
                with open(img_path, "rb") as f:
                    base64_image = base64.b64encode(f.read()).decode('utf-8')

                filename = os.path.basename(img_path)

                messages = [
                    SystemMessage(content=IMAGE_ANALYSIS_SYSTEM_PROMPT),
                    HumanMessage(content=[
                        {"type": "text", "text": f"Analyze this asset: {filename}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ])
                ]

                response = gemini_vision.invoke(messages)
                analysis_results.append(
                    f"ASSET: {filename}\nANALYSIS:\n{response.content}\n---")
                print(f"Analyzed {filename}")

            except Exception as e:
                print(f"Error analyzing image {img_path}: {e}")
                continue

        return "\n".join(analysis_results) if analysis_results else "Image analysis failed or no content extracted."
