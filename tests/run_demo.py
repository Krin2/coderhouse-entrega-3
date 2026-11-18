"""Dos pruebas: pregunta con respuesta en los docs y pregunta trampa."""
import asyncio

from src.rag import get_rag_response

CASOS = [
    ("EN DOCS", "¿Qué es una variable en Python?", True),
    ("TRAMPA", "¿Cuál es la capital de Australia?", False),
]


async def main():
    for nombre, pregunta, esperado in CASOS:
        r = await get_rag_response(pregunta)
        print(f"\n[{nombre}] {pregunta}\n{r.model_dump_json(indent=2)}")
        assert r.found == esperado, f"{nombre}: found={r.found}, se esperaba {esperado}"
        if esperado:
            assert r.sources, "Respuesta sin referencias"
        else:
            assert r.answer.startswith("No lo sé") and not r.sources
    print("\nOK: ambas pruebas pasaron")


asyncio.run(main())
