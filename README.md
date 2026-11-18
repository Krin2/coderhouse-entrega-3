# RAG local con LangChain + ChromaDB

Sistema de recuperación semántica (RAG) end-to-end: ingesta de documentos → base vectorial persistente (ChromaDB) → cadena LCEL asíncrona que responde **solo** con el contexto recuperado y devuelve un objeto Pydantic.

## Estructura
```
data/            dataset: apuntes de Python (.md)
src/config.py    configuración y único objeto de embeddings
src/ingest.py    chunking + persistencia en ChromaDB
src/rag.py       retriever + cadena LCEL + get_rag_response (async)
tests/run_demo.py  pregunta con respuesta y pregunta trampa
vectorstore/     base vectorial local (ignorada por git)
```

## Instalación (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # y editar OPENAI_API_KEY
```
El archivo `.env` está en `.gitignore`: nunca se sube la clave.

## Uso
```powershell
python -m src.ingest            # indexa data/ (omite si ya existe; --force reconstruye)
python -m tests.run_demo        # ejecuta las dos pruebas
```
```python
import asyncio
from src.rag import get_rag_response
print(asyncio.run(get_rag_response("¿Qué es una variable?")))
```

## Decisiones de diseño
- **Chunking:** `RecursiveCharacterTextSplitter.from_tiktoken_encoder` con `chunk_size=500` y `chunk_overlap=50` **tokens**. Los fragmentos resultantes miden hasta 500 tokens (el splitter respeta límites de párrafo, por lo que algunos son más cortos).
- **Limpieza previa (`src/preprocess.py`):** antes del chunking, `clean_documents` normaliza el ruido de extracción de PDF: une líneas cortadas a mitad de frase, compacta listas de una palabra por línea, repara palabras cortadas/pegadas, quita notas al pie (`mnemónico2`) y texto sin traducir, y numera los títulos (`2.4 …` → `# 2.4 …`). Los bloques de código no se tocan. Si cambias la limpieza o los documentos, reconstruye la base con `python -m src.ingest --force`. Para ver el efecto: `python -m src.preprocess`.
- **Embeddings:** `text-embedding-3-small`, definido una sola vez en `config.py` y usado tanto para indexar como para consultar (evita el error de embeddings no coincidentes).
- **top_k = 4:** evita el "contexto infinito" y el *Lost in the Middle*.
- **Persistencia:** si la colección ya tiene datos, no se reindexa; los IDs son hashes deterministas.
- **Grounding:** el prompt obliga a responder "No lo sé" si la respuesta no está en el contexto; la cadena termina en `PydanticOutputParser` → `RAGAnswer(answer, sources, found)`, y se descartan referencias que no provengan de los fragmentos recuperados.
- **Cadena:** `{"context": retriever | format_docs, "question": passthrough} | prompt | ChatOpenAI | parser`, invocada con `ainvoke`.

## Pruebas
`tests/run_demo.py` ejecuta:
1. Pregunta con respuesta en los documentos ("¿Qué es una variable en Python?") → `found=true` con referencias.
2. Pregunta trampa ("¿Cuál es la capital de Australia?") → "No lo sé", `found=false`, sin referencias.

> **Estado de verificación:** el cableado de la cadena (async, parser, filtrado de referencias, rama "No lo sé") se verificó con modelos simulados, y el chunking sobre el dataset real (21 fragmentos ≤ 500 tokens). La ejecución real contra OpenAI está pendiente porque la API key del `.env` devolvió `401 expired`. Tras actualizarla, ejecutar `python -m tests.run_demo` y pegar aquí la salida.

## Historial
Cada paso se resolvió en su propia rama (`paso-01-…` a `paso-06-…`) y se integró a `master` con merge `--no-ff`: `git log --graph --oneline`.
