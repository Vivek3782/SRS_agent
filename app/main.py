from fastapi import FastAPI
from app.config import settings
from app.api.chat import router as chat_router
from app.api.export import router as export_router
from app.api.estimation import router as estimation_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.include_router(chat_router)
app.include_router(export_router)
app.include_router(estimation_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Requirement Agent API is running"
    }
