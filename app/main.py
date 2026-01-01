from fastapi import FastAPI
from app.config import settings
from app.api.chat import router as chat_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Requirement Agent API is running"
    }
