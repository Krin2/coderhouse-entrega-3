"""Pruebas de integracion del RAG (usan embeddings y LLM reales de OpenAI).

Se ejecutan contra una base vectorial temporal (no tocan ./vectorstore).
Se omiten automaticamente si no hay OPENAI_API_KEY.
"""
import asyncio
import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(bool(os.getenv("RAG_OFFLINE")), reason="sin OPENAI_API_KEY"),
]


@pytest.fixture(scope="module")
def vectorstore_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("vectorstore")


@pytest.fixture(scope="module")
def rag(vectorstore_dir):
    import src.ingest as ingest
    import src.rag as rag_module

    ingest.VECTORSTORE_DIR = vectorstore_dir   # base temporal, no toca ./vectorstore
    return rag_module


@pytest.fixture(scope="module")
def run():
    """Un unico event loop para todo el modulo: el cliente HTTP async de
    langchain-openai se cachea y queda atado al loop donde se creo."""
    loop = asyncio.new_event_loop()
    yield loop.run_until_complete
    loop.close()


def test_ingesta_es_persistente(rag):
    import src.ingest as ingest

    n = ingest.ingest()
    assert n > 0
    assert ingest.ingest() == n              # 2a llamada: no reindexa


def test_pregunta_con_respuesta_en_los_documentos(rag, run):
    r = run(rag.get_rag_response("¿Qué es una variable en Python?"))
    assert isinstance(r, rag.RAGAnswer)
    assert r.found is True
    assert r.sources, "la respuesta debe traer referencias"
    assert all("#" in s for s in r.sources)  # formato archivo#fragmento


def test_pregunta_trampa_no_alucina(rag, run):
    r = run(rag.get_rag_response("¿Cuál es la capital de Australia?"))
    assert r.found is False
    assert r.answer.startswith("No lo sé")
    assert r.sources == []


def test_consultas_concurrentes_no_bloquean_el_event_loop(rag, run):
    async def main():
        ticks = 0

        async def heartbeat():
            nonlocal ticks
            while True:
                await asyncio.sleep(0.05)
                ticks += 1

        hb = asyncio.create_task(heartbeat())
        await asyncio.gather(
            rag.get_rag_response("¿Qué es una variable en Python?"),
            rag.get_rag_response("¿Cuál es la capital de Australia?"))
        hb.cancel()
        return ticks

    assert run(main()) > 5
