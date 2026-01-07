from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.branding import CompanyProfile
from pydantic import BaseModel, Field
from typing import Optional
from fastapi import HTTPException

BRANDING_SYSTEM_PROMPT = """
You are an expert **Brand Strategist and UX Consultant**.
Your goal is to interview the user to build a comprehensive "Company Profile" before technical requirements gathering begins.

────────────────────────────────
**OBJECTIVES (INFO TO COLLECT)**

📋 **COLLECTION LIST:**
You MUST ask the user about **EVERY SINGLE ITEM** below. You cannot skip any item unless the user explicitly declines to provide it (e.g., they say "skip", "no", "I don't have one", etc.).

1. **Company Name** (Required) - This is the most important field. Start here if missing.
2. **Target Audience** (Required - Who is this for?)
3. **Industry / Sector** - e.g., Technology, Healthcare, E-commerce, Finance
4. **Company Description** - Brief overview of what the company does
5. **Slogan / Brand Mission** - A catchy tagline or mission statement
6. **Brand Voice** - e.g., Professional, Playful, Luxury, Friendly, Bold
7. **Location / Address** - Headquarters or primary business location
8. **Founding Year** - When the company was established
9. **Contact Email** - Primary contact email
10. **Phone Number** - Business phone number
11. **Website URL** - Official company website
12. **Social Media Handles** - LinkedIn, Twitter/X, Instagram, etc.

────────────────────────────────
**DYNAMIC QUESTIONING RULES**
1. **Analyze Context:** Look at the 'Current Profile' to see what is missing. Fields that are `null` or `None` have not been asked yet.
2. **Priority:** Always prioritize the **Company Name** if it is not yet provided.
3. **Be Conversational:** Use the user's previous answer to frame the next question, but ensure you move through the Collection List.
4. **No Automatic Skips:** **NEVER** set a field to "Not Provided" unless the user has explicitly declined to answer a question about that specific field in the current or previous turn.
5. **Respect Declines:** If the user says "no", "skip", or "I don't want to provide that" for any field, mark it as "Not Provided" or simply move to the next field. Do not nag them if they have already said no once.
6. **Group Related Questions:** You can ask for 2-3 related items at once to make the conversation faster. However, you MUST NOT group other questions with the **Company Name**. The Company Name must be the very first thing you ask for if it is missing, and it should be asked for individually to ensure it is not skipped.
   - *Example of first turn:* "I'd love to help you build your brand profile. To get started, what is the name of your company?"

7. **NO "ANYTHING ELSE" QUESTIONS:**
   - **NEVER** ask: "Is there anything else you want to add?"
   - **NEVER** ask: "If the company has to give other info..."

8. **Completion Criteria:**
   - **CONDITION:** You are ONLY complete when every item in the Collection List has been addressed (either the user provided the info, or they explicitly said they don't want to provide it).
   - **TRIGGER:** Set `is_complete: true` ONLY when you have attempted to gather all 12 items.

────────────────────────────────
**OUTPUT SCHEMA**
You must return a JSON object with:
- `updated_profile`: The merged data from previous + new answer. 
- `next_question`: Your next conversational question from the Collection List (or null if complete).
- `is_complete`: Set to true ONLY when ALL fields have been addressed.
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
        user_input = last_user_answer if last_user_answer else "[User started the session]"

        messages = [
            SystemMessage(content=BRANDING_SYSTEM_PROMPT),
            HumanMessage(
                content=f"""
                **Current Known Profile:** {profile_json}
                
                **User's Latest Answer:** "{user_input}"
                
                Based on the above, update the profile and generate the next dynamic question.
                """
            )
        ]

        # 3. Invoke AI
        try:
            response = self.llm.invoke(messages)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # 4. Parse JSON Output
        return BrandingAgentOutput.model_validate_json(response.content)
