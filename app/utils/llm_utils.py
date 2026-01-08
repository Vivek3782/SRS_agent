from langchain_openai import ChatOpenAI
from app.config import settings
from typing import List, Any
import logging

logger = logging.getLogger(__name__)


def call_llm_with_fallback(messages: List[Any], temperature: float = 0.3, response_format: str = "json_object") -> Any:
    """
    Attempt to call the primary LLM model. If it fails, fallback to the specified fallback model.
    """
    # 1. Try Primary Model
    primary_llm = ChatOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        model=settings.openrouter_model,
        temperature=temperature,
        model_kwargs={"response_format": {"type": response_format}}
    )

    try:
        logger.info(
            f"Attempting call with primary model: {settings.openrouter_model}")
        return primary_llm.invoke(messages)
    except Exception as e:
        logger.error(
            f"Primary model failed: {str(e)}. Falling back to: {settings.openrouter_fallback_model}")

        # 2. Try Fallback Model
        fallback_llm = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_fallback_model,
            temperature=temperature,
            model_kwargs={"response_format": {"type": response_format}}
        )

        try:
            return fallback_llm.invoke(messages)
        except Exception as fallback_err:
            logger.error(f"Fallback model also failed: {str(fallback_err)}")
            raise fallback_err
