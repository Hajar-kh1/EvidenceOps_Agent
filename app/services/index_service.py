"""Knowledge ingestion, persistence, reload, and query-engine services."""

from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.callbacks import CallbackManager
from llama_index.core.node_parser import SentenceSplitter

from app.config import AppConfig, get_config
from app.services.llm import configure_models


def build_index(config: AppConfig | None = None) -> dict[str, int]:
    config = config or get_config()
    if not config.data_dir.is_dir():
        raise RuntimeError(f"Data directory does not exist: {config.data_dir}")
    configure_models(config)
    documents = SimpleDirectoryReader(
        input_dir=str(config.data_dir), recursive=True
    ).load_data()
    if not documents:
        raise RuntimeError(f"No documents found in {config.data_dir}")
    for document in documents:
        file_name = document.metadata.get("file_name", "unknown")
        document.metadata.update(
            source_type=Path(file_name).suffix.lower(),
            collection="first_aid_knowledge",
            trust_level="untrusted_reference",
        )
    nodes = SentenceSplitter(
        chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
    ).get_nodes_from_documents(documents)
    index = VectorStoreIndex(nodes, show_progress=True)
    config.storage_dir.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(config.storage_dir))
    return {"documents": len(documents), "nodes": len(nodes)}


def load_index(
    config: AppConfig | None = None,
    callback_manager: CallbackManager | None = None,
) -> VectorStoreIndex:
    config = config or get_config()
    if not (config.storage_dir / "index_store.json").is_file():
        raise RuntimeError("Index is missing. Run: uv run python -m app.ingest")
    configure_models(config, callback_manager)
    context = StorageContext.from_defaults(persist_dir=str(config.storage_dir))
    return load_index_from_storage(context)


def load_query_engine(
    config: AppConfig | None = None,
    callback_manager: CallbackManager | None = None,
) -> BaseQueryEngine:
    config = config or get_config()
    return load_index(config, callback_manager).as_query_engine(
        similarity_top_k=config.top_k
    )
