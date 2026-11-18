"""Pruebas offline de las referencias del RAG (retriever y LLM simulados).

Reproducen el bug original: el LLM citaba "sentencias.md#2.8" (numero de
seccion del titulo) en vez del fragmento real, y el filtro dejaba solo una
referencia secundaria.
"""
import json

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from src.rag import LLMAnswer, NO_SE, build_answer, build_chain, format_docs, ref

DOCS = [
    Document(page_content="# 2.8 Operador módulo\nObtiene el resto de la división.",
             metadata={"source": "sentencias.md", "chunk": 4}),
    Document(page_content="*operador módulo* Un operador representado por %.",
             metadata={"source": "glosario.md", "chunk": 1}),
]


def _chain(llm_json: dict, capturado: list | None = None):
    def fake_llm(prompt_value):
        if capturado is not None:
            capturado.append(prompt_value.to_string())
        return json.dumps(llm_json)

    return build_chain(retriever=RunnableLambda(lambda q: DOCS),
                       llm=RunnableLambda(fake_llm))


def test_format_docs_numera_los_bloques_desde_1():
    ctx = format_docs(DOCS)
    assert ctx.startswith("[1]\n# 2.8") and "\n\n[2]\n*operador" in ctx
    assert "sentencias.md" not in ctx          # el LLM no ve nombres que pueda deformar


def test_build_answer_traduce_ids_a_referencias():
    r = build_answer({"docs": DOCS, "result": LLMAnswer(
        answer="x", source_ids=[1, 2], found=True)})
    assert r.sources == ["sentencias.md#4", "glosario.md#1"]


def test_build_answer_descarta_ids_invalidos_y_duplicados():
    r = build_answer({"docs": DOCS, "result": LLMAnswer(
        answer="x", source_ids=[1, 9, 0, -1, 1], found=True)})
    assert r.sources == ["sentencias.md#4"]


def test_build_answer_no_se_sin_fuentes():
    r = build_answer({"docs": DOCS, "result": LLMAnswer(
        answer="inventado", source_ids=[1], found=False)})
    assert (r.answer, r.sources, r.found) == (NO_SE, [], False)


def test_cadena_cita_el_fragmento_principal_aunque_el_titulo_tenga_numero():
    prompts: list[str] = []
    chain = _chain({"answer": "Obtiene el resto.", "source_ids": [1, 2], "found": True},
                   prompts)
    r = chain.invoke({"question": "¿Qué hace el operador módulo?"})
    assert r.sources == [ref(DOCS[0]), ref(DOCS[1])]
    assert "sentencias.md#4" in r.sources and not any("2.8" in s for s in r.sources)
    assert "[1]" in prompts[0] and "source_ids" in prompts[0]


def test_cadena_asincrona_pregunta_trampa():
    chain = _chain({"answer": "Canberra", "source_ids": [], "found": False})
    import asyncio

    r = asyncio.run(chain.ainvoke({"question": "¿Capital de Australia?"}))
    assert r.found is False and r.answer == NO_SE and r.sources == []
