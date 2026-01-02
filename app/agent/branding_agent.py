from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.branding import CompanyProfile
from pydantic import BaseModel, Field
from typing import Optional

BRANDING_SYSTEM_PROMPT = """
You are a Brand Strategist Interviewer. 
Your goal is to gather a "Company Profile" from the user.

FIELDS TO COLLECT:
- Company Name
- Target Audience (Who are they serving?)
- Slogan / Mission Statement (Optional but good to ask)

RULES:
1. Look at the "Current Profile".
2. If important fields are missing, ask the next logical question.
3. If the user provided an answer, UPDATE the profile fields.
4. If you have enough info (Name + Audience at minimum), set "is_complete": true.
5. Return strictly JSON.

OUTPUT FORMAT:
{
  "updated_profile": { ... },
  "next_question": "Your question here (or null if complete)",
  "is_complete": boolean
}
"""

class BrandingAgentOutput(BaseModel):
    updated_profile: CompanyProfile
    next_question: Optional[str]
    is_complete: bool

class BrandingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.2,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def run(self, current_profile: CompanyProfile, last_user_answer: str) -> BrandingAgentOutput:
        context_str = current_profile.model_dump_json()
        
        messages = [
            SystemMessage(content=BRANDING_SYSTEM_PROMPT),
            HumanMessage(content=f"Current Profile: {context_str}\n\nUser just said: {last_user_answer}")
        ]

        response = self.llm.invoke(messages)
        return BrandingAgentOutput.model_validate_json(response.content)