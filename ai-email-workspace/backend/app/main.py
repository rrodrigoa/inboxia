import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title="Inboxia API")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def validate_llm_configuration() -> None:
    provider_name = (settings.llm_provider or settings.provider).lower()
    if provider_name not in {"openai", "openai_compatible"}:
        return
    if not settings.openai_chat_model:
        raise RuntimeError("OPENAI_CHAT_MODEL is required for OpenAI-compatible providers.")
    if not settings.openai_embedding_model:
        raise RuntimeError("OPENAI_EMBEDDING_MODEL is required for OpenAI-compatible providers.")
    if settings.chat_model:
        logger.warning("CHAT_MODEL is deprecated for OpenAI providers. Use OPENAI_CHAT_MODEL instead.")
    if settings.embedding_model:
        logger.warning("EMBEDDING_MODEL is deprecated for OpenAI providers. Use OPENAI_EMBEDDING_MODEL instead.")
    chat_model = settings.openai_chat_model
    embedding_model = settings.openai_embedding_model
    if chat_model == embedding_model:
        raise RuntimeError(
            "Chat and embedding models must be different. Update OPENAI_EMBEDDING_MODEL."
        )
    logger.info("Configured LLM models: chat=%s embedding=%s", chat_model, embedding_model)


@app.get("/health")
def health():
    return {"status": "ok"}
