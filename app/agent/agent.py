from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.prompt_3 import SYSTEM_PROMPT
from app.agent.output_parser import AgentOutput
from app.agent.intent_handler import consume_intent
from app.config import settings
from fastapi import HTTPException
from app.utils.llm_utils import call_llm_with_fallback, clean_json_content
import logging

logger = logging.getLogger(__name__)


class RequirementAgent:
    def __init__(self):
        pass

    def run(
        self,
        *,
        phase: str,
        context: dict,
        answer,
        pending_intent,
        additional_questions_asked: int,
        last_question: str = None,
        asked_questions: list = [],  # Added this
        company_profile: dict = None
    ) -> AgentOutput:

        # 1️ Apply pending intent BEFORE calling LLM
        updated_context = consume_intent(
            intent=pending_intent,
            context=context.copy(),
            answer=answer
        )

        user_payload = {
            "metadata": {
                "current_phase": phase,
                "user_answer": answer,
                "last_question_asked": last_question,
                "pending_intent": pending_intent,
                "asked_questions": asked_questions,  # Added this
                "additional_questions_asked": additional_questions_asked
            },
            "requirements_registry": updated_context,
            "original_registry": context,
            "company_profile": company_profile
        }

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=str(user_payload))
        ]

        try:
            response = call_llm_with_fallback(
                messages, temperature=0, response_format="json_object")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # 4️ Clean and Parse JSON
        raw_content = response.content
        cleaned_content = clean_json_content(raw_content)

        # Extra safety: Ensure it starts and ends with {}
        cleaned_content = cleaned_content.strip()

        # If the content contains markdown JSON blocks, clean_json_content should handle it,
        # but let's be extremely safe with raw string stripping
        if "```json" in cleaned_content:
            cleaned_content = cleaned_content.split(
                "```json")[-1].split("```")[0].strip()
        elif "```" in cleaned_content:
            cleaned_content = cleaned_content.split(
                "```")[-1].split("```")[0].strip()

        if not cleaned_content.startswith("{"):
            idx = cleaned_content.find("{")
            if idx != -1:
                cleaned_content = cleaned_content[idx:]

        if not cleaned_content.endswith("}"):
            idx = cleaned_content.rfind("}")
            if idx != -1:
                cleaned_content = cleaned_content[:idx+1]

        try:
            parsed = AgentOutput.model_validate_json(cleaned_content)
            return parsed.root
        except Exception as parse_err:
            logger.error(
                f"JSON Parse Error: {str(parse_err)}\nRaw Content: {response.content}")
            raise HTTPException(
                status_code=500, detail=f"AI returned invalid JSON: {str(parse_err)}")
