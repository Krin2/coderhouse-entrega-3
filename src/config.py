"""Configuracion central. Embeddings y rutas se definen UNA sola vez para
que indexacion y consulta usen siempre el mismo modelo."""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Falta OPENAI_API_KEY: defínela en el archivo .env")

DATA_DIR = ROOT / "data"
VECTORSTORE_DIR = ROOT / "vectorstore"
COLLECTION_NAME = "apuntes_python"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

CHUNK_SIZE = 500      # tokens
CHUNK_OVERLAP = 50    # tokens
TOP_K = 4             # entre 3 y 5 para evitar "Lost in the Middle"


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)
