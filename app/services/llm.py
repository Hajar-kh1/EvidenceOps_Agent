"""Shared LLM and embedding-model configuration."""

import logging

from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from app.config import AppConfig, get_config

logger = logging.getLogger(__name__)


def configure_models(
    config: AppConfig | None = None,
    callback_manager: CallbackManager | None = None,
) -> None:
    config = config or get_config()
    config.require_model_credentials()
    logger.info(
        "Configuring model provider=%s llm=%s embedding=%s",
        config.model_provider,
        config.llm_model,
        config.embedding_model,
    )
    Settings.llm = OpenAI(
        model=config.llm_model,
        temperature=0.1,
        api_key=config.openai_api_key,
        callback_manager=callback_manager,
    )
    Settings.embed_model = OpenAIEmbedding(
        model=config.embedding_model,
        api_key=config.openai_api_key,
        callback_manager=callback_manager,
    )
