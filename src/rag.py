"""Cadena RAG asincrona (LCEL): retriever -> prompt -> LLM -> PydanticOutputParser."""
import asyncio

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.config import LLM_MODEL, TOP_K
from src.ingest import get_vectorstore, ingest

NO_SE = "No lo sé"


class RAGAnswer(BaseModel):
    answer: str = Field(description="Respuesta basada solo en el contexto, o 'No lo sé'.")
    sources: list[str] = Field(
        default_factory=list,
        description="Referencias [archivo#fragmento] usadas. Vacio si no hay respuesta.")
    found: bool = Field(description="True si la respuesta esta en el contexto.")


parser = PydanticOutputParser(pydantic_object=RAGAnswer)

SYSTEM_PROMPT = f"""Eres un asistente técnico. Responde SOLO con la información del CONTEXTO.
Reglas:
- No uses conocimiento externo ni inventes datos, aunque conozcas la respuesta.
- Si la respuesta no está en el CONTEXTO, responde exactamente "{NO_SE}", \
pon found=false y sources=[].
- Si respondes, pon found=true y cita en sources las referencias [archivo#fragmento] \
de los fragmentos que usaste.
- Responde en español.

{{format_instructions}}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "CONTEXTO:\n{context}\n\nPREGUNTA: {question}"),
]).partial(format_instructions=parser.get_format_instructions())


def ref(doc: Document) -> str:
    return f"{doc.metadata['source']}#{doc.metadata['chunk']}"


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(f"[{ref(d)}]\n{d.page_content}" for d in docs)


def build_chain():
    ingest()  # no reindexa si la coleccion ya existe
    retriever = get_vectorstore().as_retriever(search_kwargs={"k": TOP_K})
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    return (
        {"context": retriever | RunnableLambda(format_docs),
         "question": RunnablePassthrough()}
        | prompt | llm | parser
    ), retriever


_chain = None


async def get_rag_response(query: str) -> RAGAnswer:
    global _chain
    if _chain is None:
        _chain = await asyncio.to_thread(build_chain)
    chain, retriever = _chain
    answer: RAGAnswer = await chain.ainvoke(query)
    # Anti-alucinacion: solo se aceptan referencias realmente recuperadas.
    retrieved = {ref(d) for d in await retriever.ainvoke(query)}
    answer.sources = [s for s in answer.sources if s in retrieved]
    if not answer.found:
        answer.answer, answer.sources = NO_SE, []
    return answer
