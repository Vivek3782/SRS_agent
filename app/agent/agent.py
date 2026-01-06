from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.prompt import SYSTEM_PROMPT
from app.agent.output_parser import AgentOutput
from app.agent.intent_handler import consume_intent
from app.config import settings
from fastapi import HTTPException

class RequirementAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0,
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "Requirement-Gathering-Agent"
            },
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )

    def run(
        self,
        *,
        phase: str,
        context: dict,
        answer,
        pending_intent,
        additional_questions_asked: int,
        last_question: str = None
    ) -> AgentOutput:

        # 1️ Apply pending intent BEFORE calling LLM
        updated_context = consume_intent(
            intent=pending_intent,
            context=context.copy(),
            answer=answer
        )

        user_payload = {
            "phase": phase,
            "original_context": context,
            "context": updated_context,
            "answer": answer,
            "last_question": last_question,
            "pending_intent": pending_intent,
            "additional_questions_asked": additional_questions_asked
        }

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=str(user_payload))
        ]

        try:
            response = self.llm.invoke(messages)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # OpenRouter returns JSON string → strict parse
        parsed = AgentOutput.model_validate_json(response.content)
        return parsed.root
