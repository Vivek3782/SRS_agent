from langchain_openai import ChatOpenAI
from app.config import settings
from typing import List, Any
import logging
import json
import re

logger = logging.getLogger(__name__)


def clean_json_content(content: str) -> str:
    """
    Clean LLM response content to ensure it's valid JSON.
    Removes markdown backticks and common syntax errors like trailing commas.
    """
    # 1. Remove markdown code blocks if present
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"```\s*", "", content)
    content = content.strip()

    # 2. Remove C-style comments (/* ... */)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    # 3. Remove single-line comments (// ...)
    # Be careful not to match // inside a URL string (http://)
    content = re.sub(r"(?<!:)//.*", "", content)

    # 4. Relaxed trailing comma removal (handles ,} and ,])
    content = re.sub(r",\s*([}\]])", r"\1", content)

    return content


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
