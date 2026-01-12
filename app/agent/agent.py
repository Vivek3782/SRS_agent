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
                "additional_questions_asked": additional_questions_asked
            },
            "HISTORY_OF_ASKED_QUESTIONS": asked_questions,
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
            agent_output = parsed.root

            # --- Internal Repetition & Fishing Guard ---
            if agent_output.status == "ASK":
                generated_q = agent_output.question.strip()
                q_lower = generated_q.lower()

                # Check for exact duplicates
                is_duplicate = generated_q in [
                    q.strip() for q in asked_questions]

                # Check for "Fishing" patterns
                is_fishing = any(pattern in q_lower for pattern in [
                                 "are there any other", "such as", "would you like to add", "common entities include"])

                if is_duplicate or is_fishing:
                    reason = "REPETITION" if is_duplicate else "FISHING/IDEA PITCHING"
                    logger.warning(
                        f"Loop/Fishing Detected ({reason}): AI generated '{generated_q}'. Retrying...")

                    retry_messages = messages + [
                        HumanMessage(content=f"STOP. You just generated: '{generated_q}'. This is forbidden because it is a {reason}. You are STRICTLY FORBIDDEN from 'fishing' for more entities or suggesting what the user might need. If you already have some data, MOVE TO THE NEXT TOPIC/INTENT IMMEDIATELY. Do not use phrases like 'Are there any other' or 'such as'. Ask a direct question about a MISSING area only.")
                    ]

                    response = call_llm_with_fallback(
                        retry_messages, temperature=0.3, response_format="json_object")
                    cleaned_content = clean_json_content(response.content)
                    parsed = AgentOutput.model_validate_json(cleaned_content)
                    agent_output = parsed.root

            return agent_output
        except Exception as parse_err:
            logger.error(
                f"JSON Parse Error: {str(parse_err)}\nRaw Content: {response.content}")
            raise HTTPException(
                status_code=500, detail=f"AI returned invalid JSON: {str(parse_err)}")
