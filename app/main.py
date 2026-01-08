from fastapi import FastAPI
from app.config import settings
from app.api.chat import router as chat_router
from app.api.export import router as export_router
from app.api.estimation import router as estimation_router
from app.api.branding import router as branding_router
from app.api.gen_prompts import router as gen_prompts_router
from app.database import engine, Base
from app.models.user import User
from app.api.user import router as user_router
import logging
import os
from app.api.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
)
logger = logging.getLogger(__name__)

# LangSmith Monitoring Setup
if settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    logger.info(
        f"LangSmith monitoring enabled for project: {settings.langchain_project}")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.include_router(chat_router)
app.include_router(export_router)
app.include_router(estimation_router)
app.include_router(branding_router)
app.include_router(gen_prompts_router)
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Requirement Agent API is running"
    }
