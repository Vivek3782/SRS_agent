from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.branding import CompanyProfile
from pydantic import BaseModel, Field
from typing import Optional

# --- UPDATED PROMPT: STRICTER & MORE EFFICIENT ---
BRANDING_SYSTEM_PROMPT = """
You are an expert **Brand Strategist and UX Consultant**.
Your goal is to interview the user to build a "Company Profile" before technical requirements gathering begins.

────────────────────────────────
**OBJECTIVES (INFO TO COLLECT)**
1. **Company Name** (Required)
2. **Target Audience** (Required - Who is this for?)
3. **Slogan / Brand Mission** (Optional but highly desired)
4. **Brand Voice** (Optional - e.g., Professional, Playful, Luxury)

────────────────────────────────
**DYNAMIC QUESTIONING RULES**
1. **Analyze Context:** Look at the 'Current Profile' to see what is missing.
2. **Be Conversational:** Use the user's previous answer to frame the next question.
   - *Example:* "A coffee shop for students? That sounds cozy. Do you have a slogan yet?"
3. **Maximize Detail:** If the user gives a vague audience (e.g., "Everyone"), ask ONE clarifying question to narrow it down (e.g., "Is it more for budget-conscious people or luxury buyers?").
4. **NO "ANYTHING ELSE" QUESTIONS:**
   - **NEVER** ask: "Is there anything else you want to add?" or "Do you have more info?"
   - **NEVER** ask: "If the company has to give other info..."
   - If you have the Name and Audience, and have asked about Slogan/Voice (or the user skipped them), **STOP IMMEDIATELY** (set `is_complete: true`).

5. **Completion Criteria:**
   - **MANDATORY:** You MUST have `name` and `target_audience`.
   - **OPTIONAL:** You should try to get `slogan` or `brand_voice` if appropriate.
   - **TRIGGER:** If you have Name + Audience, and you feel you have enough to start designing, set `is_complete: true`.

────────────────────────────────
**OUTPUT SCHEMA**
You must return a JSON object with:
- `updated_profile`: The merged data from previous + new answer.
- `next_question`: Your smart, contextual follow-up question (or null if complete).
- `is_complete`: Set to true ONLY when you have Name AND Audience (Slogan is optional).
"""

class BrandingAgentOutput(BaseModel):
    updated_profile: CompanyProfile
    next_question: Optional[str] = None
    is_complete: bool

class BrandingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.3, 
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def run(self, current_profile: CompanyProfile, last_user_answer: str) -> BrandingAgentOutput:
        # 1. Serialize current state
        profile_json = current_profile.model_dump_json()
        
        # 2. Construct the Conversation Context
        messages = [
            SystemMessage(content=BRANDING_SYSTEM_PROMPT),
            HumanMessage(
                content=f"""
                **Current Known Profile:** {profile_json}
                
                **User's Latest Answer:** "{last_user_answer}"
                
                Based on the above, update the profile and generate the next dynamic question.
                """
            )
        ]

        # 3. Invoke AI
        response = self.llm.invoke(messages)
        
        # 4. Parse JSON Output
        return BrandingAgentOutput.model_validate_json(response.content)