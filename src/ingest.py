"""Ingesta: lee data/, fragmenta (chunking por tokens) y persiste en ChromaDB.

Uso:  python -m src.ingest [--force]
"""
import argparse
import hashlib

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (CHUNK_OVERLAP, CHUNK_SIZE, COLLECTION_NAME, DATA_DIR,
                        VECTORSTORE_DIR, get_embeddings)
from src.preprocess import clean_documents


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(VECTORSTORE_DIR),
    )


def load_documents() -> list[Document]:
    files = sorted([*DATA_DIR.glob("*.md"), *DATA_DIR.glob("*.txt")])
    if not files:
        raise FileNotFoundError(f"No hay .md/.txt en {DATA_DIR}")
    return [
        Document(page_content=f.read_text(encoding="utf-8"),
                 metadata={"source": f.name})
        for f in files
    ]


def split_documents(docs: list[Document]) -> list[Document]:
    # Chunking medido en TOKENS (tiktoken), no en caracteres.
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)
    counters: dict[str, int] = {}
    for c in chunks:
        src = c.metadata["source"]
        counters[src] = counters.get(src, 0) + 1
        c.metadata["chunk"] = counters[src]
    return chunks


def ingest(force: bool = False) -> int:
    """Indexa los documentos. Si la coleccion ya existe, no reindexa
    (salvo force=True). Devuelve la cantidad de fragmentos en la coleccion."""
    vs = get_vectorstore()
    existing = vs._collection.count()
    if existing and not force:
        print(f"[ingest] Coleccion ya poblada ({existing} fragmentos). Se omite.")
        return existing
    if existing:
        vs.delete_collection()
        vs = get_vectorstore()

    # Limpieza ANTES del chunking: quita ruido de extraccion de PDF.
    chunks = split_documents(clean_documents(load_documents()))
    # IDs deterministas: reingestar el mismo texto no duplica registros.
    ids = [hashlib.sha256(
        f"{c.metadata['source']}:{c.metadata['chunk']}:{c.page_content}".encode()
    ).hexdigest() for c in chunks]
    vs.add_documents(chunks, ids=ids)
    print(f"[ingest] {len(chunks)} fragmentos indexados en {VECTORSTORE_DIR}")
    return len(chunks)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="reconstruir la coleccion")
    ingest(force=ap.parse_args().force)
