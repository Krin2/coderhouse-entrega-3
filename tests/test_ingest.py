"""Pruebas offline del modulo de ingesta (sin API ni red)."""
import tiktoken

from src.config import CHUNK_SIZE
from src.ingest import load_documents, split_documents
from src.preprocess import clean_documents


def _chunks():
    return split_documents(clean_documents(load_documents()))


def test_lee_todos_los_archivos_de_data():
    fuentes = {d.metadata["source"] for d in load_documents()}
    assert len(fuentes) >= 3 and all(f.endswith((".md", ".txt")) for f in fuentes)


def test_chunks_respetan_el_tamano_en_tokens():
    enc = tiktoken.get_encoding("cl100k_base")
    chunks = _chunks()
    assert chunks
    assert max(len(enc.encode(c.page_content)) for c in chunks) <= CHUNK_SIZE


def test_chunks_tienen_referencia_archivo_y_numero():
    for c in _chunks():
        assert c.metadata["source"] and c.metadata["chunk"] >= 1
