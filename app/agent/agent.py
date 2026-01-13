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
        asked_questions: list = [],
        company_profile: dict = None
    ) -> AgentOutput:

        # ------------------------------------------------------------------
        # STRIKE SYSTEM LOGIC (SOLUTION C)
        # Prevents getting stuck in a loop on the same intent.
        # ------------------------------------------------------------------

        # 1. Retrieve or initialize the strike counter from context
        # We use a hidden key '_meta' to store agent state without polluting requirements
        meta_state = context.get(
            "_meta", {"last_intent_type": None, "strike_count": 0})

        current_intent_type = pending_intent.get(
            "type") if pending_intent else None

        # Check if we are looping on the same intent
        if current_intent_type and current_intent_type == meta_state["last_intent_type"]:
            meta_state["strike_count"] += 1
        else:
            meta_state["strike_count"] = 1  # Reset on new intent
            meta_state["last_intent_type"] = current_intent_type

        # 2. If strikes > 2, FORCE KILL the pending intent
        effective_intent = pending_intent
        force_move_message = None

        if meta_state["strike_count"] > 2:
            logger.warning(
                f"STRIKE LIMIT REACHED for {current_intent_type}. Forcing move.")
            # Remove intent so LLM isn't forced to ask about it by the prompt
            effective_intent = None
            force_move_message = SystemMessage(
                content="SYSTEM OVERRIDE: You are stuck on the previous topic. MOVE IMMEDIATELY to the next logical phase or topic. Do not ask about the previous topic again."
            )

        # ------------------------------------------------------------------
        # APPLY INTENT & CONSTRUCT PAYLOAD
        # ------------------------------------------------------------------

        # 3. Apply intent (use effective_intent)
        updated_context = consume_intent(
            intent=effective_intent,  # Use the potentially cleared intent
            context=context.copy(),
            answer=answer
        )

        # Save meta state back to updated_context so it persists to next turn
        updated_context["_meta"] = meta_state

        user_payload = {
            "metadata": {
                "current_phase": phase,
                "user_answer": answer,
                "last_question_asked": last_question,
                "pending_intent": effective_intent,  # Send the cleared intent if stuck
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

        # Inject the override message if we are forcing a move
        if force_move_message:
            messages.append(force_move_message)

        try:
            response = call_llm_with_fallback(
                messages, temperature=0, response_format="json_object")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # ------------------------------------------------------------------
        # CLEAN & PARSE JSON
        # ------------------------------------------------------------------
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

            # ------------------------------------------------------------------
            # INTERNAL REPETITION & FISHING GUARD (LOOPED)
            # ------------------------------------------------------------------
            max_retries = 3
            current_retry = 0

            def is_semantic_duplicate(new_q: str, history: list) -> bool:
                """Check if the new question is semantically similar to any in history."""
                new_q_lower = new_q.lower()

                # Extract key entities/roles from the new question
                # Look for patterns like 'for the X role' or 'for X'
                import re
                role_match = re.search(
                    r"for (?:the )?['\"]?([^'\"?]+)['\"]?(?: role)?", new_q_lower)
                entity_match = re.search(
                    r"(?:data fields?|entities?|features?) (?:for|of|required for) ['\"]?([^'\"?]+)['\"]?", new_q_lower)

                extracted_subject = None
                if role_match:
                    extracted_subject = role_match.group(1).strip()
                elif entity_match:
                    extracted_subject = entity_match.group(1).strip()

                for hist_q in history:
                    hist_q_lower = hist_q.lower().strip()

                    # Exact match
                    if new_q_lower == hist_q_lower:
                        return True

                    # Check if same subject/entity is mentioned in both
                    if extracted_subject and extracted_subject in hist_q_lower:
                        # Check if both are asking about data fields/entities/features
                        if any(kw in new_q_lower for kw in ["data field", "entities", "workflow", "features"]) and \
                           any(kw in hist_q_lower for kw in ["data field", "entities", "workflow", "features"]):
                            return True

                return False

            while agent_output.status == "ASK" and current_retry < max_retries:
                generated_q = agent_output.question.strip()
                q_lower = generated_q.lower()

                # Check for exact and semantic duplicates
                is_duplicate = is_semantic_duplicate(
                    generated_q, asked_questions)

                # Check for "Fishing" patterns
                is_fishing = any(pattern in q_lower for pattern in [
                                 "are there any other", "such as", "would you like to add", "common entities include"])

                if is_duplicate or is_fishing:
                    current_retry += 1
                    reason = "REPETITION" if is_duplicate else "FISHING/IDEA PITCHING"
                    logger.warning(
                        f"Loop/Fishing Detected ({reason}) [Try {current_retry}/{max_retries}]: AI generated '{generated_q}'. Retrying...")

                    retry_instruction = f"STOP. You just generated: '{generated_q}'. This is forbidden because it is a {reason}. You are STRICTLY FORBIDDEN from 'fishing' for more entities or suggesting what the user might need. If you already have some data, MOVE TO THE NEXT TOPIC/INTENT IMMEDIATELY. Do not use phrases like 'Are there any other' or 'such as'. Ask a direct question about a MISSING area only."

                    # Create a new message list for the retry to avoid accumulating STOP messages in the main 'messages' list if we don't want to
                    # Actually, keeping them might help the LLM see what NOT to do.
                    messages.append(HumanMessage(content=retry_instruction))

                    response = call_llm_with_fallback(
                        messages, temperature=0.3 + (current_retry * 0.1), response_format="json_object")
                    cleaned_content = clean_json_content(response.content)
                    parsed = AgentOutput.model_validate_json(cleaned_content)
                    agent_output = parsed.root
                else:
                    break  # Not a duplicate/fishing

            # Final check: if we exhausted retries and it's still a duplicate, reject it
            if agent_output.status == "ASK":
                generated_q = agent_output.question.strip()

                if is_semantic_duplicate(generated_q, asked_questions):
                    logger.error(
                        "CRITICAL: Agent still repeating after max retries. Forcing REJECT.")
                    # Return a REJECT output
                    agent_output.status = "REJECT"
                    agent_output.question = "I apologize, I seem to be repeating myself. Could you please provide more details about your requirements or skip to the next topic?"

            return agent_output
        except Exception as parse_err:
            logger.error(
                f"JSON Parse Error: {str(parse_err)}\nRaw Content: {response.content}")
            raise HTTPException(
                status_code=500, detail=f"AI returned invalid JSON: {str(parse_err)}")
