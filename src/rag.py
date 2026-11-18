"""Cadena RAG asincrona (LCEL): retriever -> prompt -> LLM -> PydanticOutputParser.

Referencias: el LLM NO escribe referencias de texto libre (se confundia con los
numeros de seccion de los titulos, p. ej. "#2.8" en vez de "#4"). Los bloques
del contexto se numeran [1], [2], ... y el modelo devuelve solo esos numeros
(`source_ids`); el codigo los traduce a "archivo#fragmento".
"""
import asyncio
from operator import itemgetter

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.config import LLM_MODEL, TOP_K
from src.ingest import get_vectorstore, ingest

NO_SE = "No lo sé"


class RAGAnswer(BaseModel):
    """Resultado publico de get_rag_response."""
    answer: str = Field(description="Respuesta basada solo en el contexto, o 'No lo sé'.")
    sources: list[str] = Field(
        default_factory=list,
        description="Referencias archivo#fragmento usadas. Vacio si no hay respuesta.")
    found: bool = Field(description="True si la respuesta esta en el contexto.")


class LLMAnswer(BaseModel):
    """Lo que devuelve el LLM: referencias como numeros de bloque, no como texto."""
    answer: str = Field(description="Respuesta basada solo en el contexto, o 'No lo sé'.")
    source_ids: list[int] = Field(
        default_factory=list,
        description="Numeros (enteros) de los bloques [n] del contexto que se usaron. "
                    "Vacio si no hay respuesta.")
    found: bool = Field(description="True si la respuesta esta en el contexto.")


parser = PydanticOutputParser(pydantic_object=LLMAnswer)

SYSTEM_PROMPT = f"""Eres un asistente técnico. Responde SOLO con la información del CONTEXTO.
Reglas:
- No uses conocimiento externo ni inventes datos, aunque conozcas la respuesta.
- Si la respuesta no está en el CONTEXTO, responde exactamente "{NO_SE}", \
pon found=false y source_ids=[].
- Cada bloque del CONTEXTO empieza con su número entre corchetes: [1], [2], ...
- Si respondes, pon found=true y en source_ids los números de los bloques que usaste \
(solo enteros, p. ej. [1, 3]). Nunca uses títulos ni números de sección del texto.
- Responde en español.

{{format_instructions}}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "CONTEXTO:\n{context}\n\nPREGUNTA: {question}"),
]).partial(format_instructions=parser.get_format_instructions())


def ref(doc: Document) -> str:
    return f"{doc.metadata['source']}#{doc.metadata['chunk']}"


def format_docs(docs: list[Document]) -> str:
    """Numera los bloques desde 1 para que el LLM los cite por numero."""
    return "\n\n".join(f"[{i}]\n{d.page_content}" for i, d in enumerate(docs, start=1))


def build_answer(inputs: dict) -> RAGAnswer:
    """Traduce los numeros de bloque del LLM a referencias reales.
    Descarta ids fuera de rango (anti-alucinacion) y duplicados."""
    docs: list[Document] = inputs["docs"]
    result: LLMAnswer = inputs["result"]
    if not result.found:
        return RAGAnswer(answer=NO_SE, sources=[], found=False)
    sources: list[str] = []
    for i in result.source_ids:
        if 1 <= i <= len(docs) and ref(docs[i - 1]) not in sources:
            sources.append(ref(docs[i - 1]))
    return RAGAnswer(answer=result.answer, sources=sources, found=True)


def build_chain(retriever: Runnable | None = None, llm=None) -> Runnable:
    """Cadena LCEL: {"question"} -> retriever -> contexto numerado -> prompt -> LLM
    -> parser -> RAGAnswer. Una sola recuperacion por consulta."""
    if retriever is None:
        ingest()  # no reindexa si la coleccion ya existe
        retriever = get_vectorstore().as_retriever(search_kwargs={"k": TOP_K})
    llm = llm or ChatOpenAI(model=LLM_MODEL, temperature=0)
    return (
        RunnablePassthrough.assign(docs=itemgetter("question") | retriever)
        | RunnablePassthrough.assign(
            context=itemgetter("docs") | RunnableLambda(format_docs))
        | RunnablePassthrough.assign(result=prompt | llm | parser)
        | RunnableLambda(build_answer)
    )


_chain: Runnable | None = None


async def get_rag_response(query: str) -> RAGAnswer:
    global _chain
    if _chain is None:
        _chain = await asyncio.to_thread(build_chain)
    return await _chain.ainvoke({"question": query})
