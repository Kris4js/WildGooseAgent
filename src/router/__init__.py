"""FastAPI router for Wild Goose Agent."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .chat import router as chat_router
from .tools import router as tools_router
from .skills import router as skills_router
from .sessions import router as sessions_router

app = FastAPI(title="Wild Goose Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(skills_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
