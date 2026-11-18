# RAG local con LangChain + ChromaDB

Sistema de recuperación semántica (RAG) end-to-end: ingesta de documentos → limpieza → chunking → base vectorial persistente (ChromaDB) → cadena LCEL asíncrona que responde **solo** con el contexto recuperado y devuelve un objeto Pydantic con el texto y las referencias.

## Estructura
```
data/                 dataset: 4 apuntes de Python (.md)
src/config.py         configuración y único objeto de embeddings
src/preprocess.py     limpieza de los documentos antes del chunking
src/ingest.py         chunking + persistencia en ChromaDB
src/rag.py            retriever + cadena LCEL + get_rag_response (async)
tests/                pruebas con pytest
pytest.ini            configuración de pytest
.env.example          plantilla de variables de entorno
vectorstore/          base vectorial local (ignorada por git)
```

## Instalación (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Usa `.env.example` como plantilla para crear tu archivo `.env` y completa ahí tu `OPENAI_API_KEY`. El `.env` está en `.gitignore`, por lo que la clave nunca se sube al repositorio.

## Uso
```powershell
python -m src.ingest            # indexa data/ (omite si ya existe; --force reconstruye)
python -m src.preprocess        # muestra el efecto de la limpieza sobre cada archivo
pytest                          # ejecuta todas las pruebas
```
```python
import asyncio
from src.rag import get_rag_response

respuesta = asyncio.run(get_rag_response("¿Qué es una variable en Python?"))
print(respuesta.answer, respuesta.sources)
```

## Decisiones de diseño
- **Limpieza previa (`src/preprocess.py`):** los `.md` provienen de una extracción de PDF. Antes del chunking, `clean_documents` une líneas cortadas a mitad de frase, compacta listas de una palabra por línea, repara palabras cortadas o pegadas, quita notas al pie (`mnemónico2`) y texto sin traducir, y numera los títulos (`2.4 …` → `# 2.4 …`). Los bloques de código no se tocan. Si cambias la limpieza o los documentos, reconstruye la base con `python -m src.ingest --force`.
- **Chunking:** `RecursiveCharacterTextSplitter.from_tiktoken_encoder` con `chunk_size=500` y `chunk_overlap=50`, medidos en **tokens**. El splitter respeta los límites de párrafo y sección, y como los documentos son cortos, los fragmentos quedan por debajo del tope (ver resultados).
- **Embeddings:** `text-embedding-3-small`, definido una sola vez en `config.py` y usado tanto para indexar como para consultar (evita el error de embeddings no coincidentes).
- **top_k = 4:** evita el "contexto infinito" y el *Lost in the Middle*.
- **Persistencia:** si la colección ya tiene datos no se reindexa; los IDs son hashes deterministas.
- **Grounding:** el prompt obliga a responder "No lo sé" si la respuesta no está en el contexto. La cadena termina en `PydanticOutputParser` y devuelve `RAGAnswer(answer, sources, found)`.
- **Referencias por número de bloque:** los fragmentos del contexto se numeran `[1]`, `[2]`, … y el LLM devuelve solo esos números (`source_ids`). El código los traduce a `archivo#fragmento`, descarta ids fuera de rango y duplicados, y devuelve `sources=[]` ante "No lo sé". Así el modelo no puede deformar la referencia (antes escribía `sentencias.md#2.8`, el número de sección del título, en vez del fragmento `#4`).
- **Cadena asíncrona:** `question → retriever → contexto numerado → prompt → ChatOpenAI → PydanticOutputParser → RAGAnswer`, con una sola recuperación por consulta e invocada con `ainvoke`.

## Resultados reales

**Ingesta del dataset** (4 archivos de `data/`): 21 fragmentos de entre 85 y 395 tokens (promedio 265), ninguno por encima de los 500 tokens configurados. Una segunda llamada a `ingest()` no reindexa.

**Prueba 1 — la respuesta está en los documentos:** `¿Qué es una variable en Python?`
```json
{
  "answer": "Una variable es un nombre que se refiere a un valor.",
  "sources": ["variables.md#1"],
  "found": true
}
```

**Prueba 2 — pregunta trampa (no está en los documentos):** `¿Cuál es la capital de Australia?`
```json
{
  "answer": "No lo sé",
  "sources": [],
  "found": false
}
```
El modelo no usa su conocimiento general ni inventa una respuesta: declara que no sabe y no devuelve referencias.

## Pruebas (pytest)
```powershell
pytest            # 18 pruebas
pytest -m "not integration"   # solo las offline (no llaman a la API)
```
| Archivo | Qué verifica |
|---|---|
| `tests/test_preprocess.py` | Limpieza: líneas REPL, reflujo de prosa y títulos, código intacto, notas al pie y listas. |
| `tests/test_ingest.py` | Lectura de `data/`, fragmentos ≤ 500 tokens y referencia `archivo#fragmento` en cada uno. |
| `tests/test_rag_refs.py` | Referencias (LLM y retriever simulados): bloques numerados, traducción de ids a `archivo#fragmento`, descarte de ids inválidos y cadena asíncrona con la trampa. |
| `tests/test_rag.py` (`integration`) | Persistencia de la ingesta, pregunta con respuesta (con referencias), regresión de la fuente principal (`¿Qué hace el operador módulo?` debe citar `sentencias.md`), pregunta trampa ("No lo sé" sin fuentes) y consultas concurrentes sin bloquear el event loop. |

Las pruebas de integración usan una base vectorial temporal (no tocan `./vectorstore`) y se omiten solas si no hay `OPENAI_API_KEY` en el entorno.

Resultado actual: `18 passed`.

## Historial
Cada paso se resolvió en su propia rama (`paso-01-…`, `paso-02-…`, …) y se integró a `master` con merge `--no-ff`: `git log --graph --oneline`.
