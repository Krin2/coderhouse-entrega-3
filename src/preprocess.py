"""Limpieza de documentos ANTES del chunking.

Los .md del dataset provienen de una extraccion de PDF y traen ruido que
degrada los embeddings: saltos de linea duros en mitad de frases, palabras
cortadas o pegadas, marcas de nota al pie, texto sin traducir y listas
partidas en una palabra por linea. `clean_text` lo normaliza sin tocar el
contenido de los bloques de codigo.

Uso (ver el efecto sobre cada archivo):  python -m src.preprocess
"""
import re

from langchain_core.documents import Document

FENCE = "```"
TERMINAL = (".", ":", "?", "!", ";")

# Artefactos conocidos del dataset, aplicados sobre el texto ORIGINAL
# (todavia con los saltos de linea duros).
RAW_FIXES = [
    ("\ncon\nEl carácter guión-bajo", "\nEl carácter guión-bajo"),
    ("nombres\nmúltiples\npalabras,\ncomo\nen\nmi_nombre\no\n",
     "nombres con múltiples palabras, como en mi_nombre o\n"),
    # el texto en prosa quedo dentro del bloque de codigo: se cierra el bloque
    ("producelasalida\n", f"{FENCE}\nproduce la salida:\n{FENCE}\n"),
]

# Palabras cortadas / pegadas, aplicadas sobre el texto ya reflujado.
TEXT_FIXES = [
    ("frac cionaria", "fraccionaria"),
    ("mul tiplicación", "multiplicación"),
    ("consis tente", "consistente"),
    ("evaluación de pende de", "evaluación depende de"),
    ("tepermitan", "te permitan"),
    ("Lasentencia", "La sentencia"),
    ("dedivisión", "de división"),
    ("valoresa los", "valores a los"),
    ("Apesar de", "A pesar de"),
    ("L Multiplicación", "La Multiplicación"),
    ("evaluar 1 2π", "evaluar 1/(2π)"),
]

ENGLISH_WORDS = {
    "the", "to", "and", "of", "is", "are", "in", "because", "these", "this",
    "that", "with", "belong", "type", "called", "not", "less", "numbers",
    "format", "represented",
}

HEADING_NUM_RE = re.compile(r"^\d+\.\d+\s+[A-ZÁÉÍÓÚÑ][^.!?:]{0,60}$")
BLOCK_START_RE = re.compile(r"^(#|\d+\.\d+\s|•|\*[^*\s][^*]*\*\s|>>>)")
# nota al pie pegada a una palabra: "mnemónico2 significa", "elegidos3."
FOOTNOTE_WORD_RE = re.compile(r"\b([a-záéíóúñ]{4,})\d(?=\s|[.,;:])")
# nota al pie tras un numero: "1,000,000 1. Eso"
FOOTNOTE_NUM_RE = re.compile(r"(\d,\d{3}(?:,\d{3})+) \d(?=\.)")


def _is_english(line: str) -> bool:
    """Linea sin traducir (restos del texto original en ingles)."""
    if not line.isascii():
        return False
    words = re.findall(r"[A-Za-z']+", line)
    if len(words) < 8:
        return False
    hits = sum(w.lower() in ENGLISH_WORDS for w in words)
    return hits / len(words) >= 0.3


def _is_list_item(line: str) -> bool:
    tokens = line.split()
    return 0 < len(tokens) <= 3 and re.fullmatch(r"[\w ]+", line) is not None


def _split_segments(lines: list[str]) -> list[tuple[bool, list[str]]]:
    """Separa en segmentos (es_codigo, lineas) segun los bloques ```."""
    segments: list[tuple[bool, list[str]]] = []
    current: list[str] = []
    in_code = False
    for line in lines:
        if line.startswith(FENCE):
            if in_code:
                current.append(line)
                segments.append((True, current))
                current, in_code = [], False
            else:
                if current:
                    segments.append((False, current))
                current, in_code = [line], True
        else:
            current.append(line)
    if current:
        segments.append((in_code, current))
    return segments


def _compact_lists(lines: list[str]) -> list[tuple[str, bool]]:
    """Convierte rachas de >=10 lineas cortas (una palabra por linea, como la
    lista de palabras clave) en una sola linea atomica. Devuelve (linea, atomica)."""
    out: list[tuple[str, bool]] = []
    i = 0
    while i < len(lines):
        j = i
        while j < len(lines) and _is_list_item(lines[j].strip()):
            j += 1
        if j - i >= 10:
            items = [t for l in lines[i:j] for t in l.split()]
            out.append(("Lista: " + ", ".join(items) + ".", True))
            i = j
        else:
            out.append((lines[i], False))
            i += 1
    return out


def _reflow(lines: list[str]) -> list[str]:
    """Une lineas partidas a mitad de frase. Una linea se une con la siguiente
    solo si es prosa larga (>=4 palabras) que no termina en puntuacion final."""
    out: list[str] = []
    prev_open = False
    for line, atomic in _compact_lists(lines):
        line = line.strip()
        if not line:
            out.append("")
            prev_open = False
            continue
        if prev_open and not atomic and not BLOCK_START_RE.match(line):
            out[-1] += " " + line
        else:
            out.append(HEADING_NUM_RE.sub(r"# \g<0>", line)
                       if HEADING_NUM_RE.match(line) else line)
        last = out[-1]
        prev_open = (not atomic and not last.endswith(TERMINAL)
                     and len(last.split()) >= 4
                     and not last.startswith(("#", ">>>")))   # titulos y lineas REPL
    return out


def _clean_prose(lines: list[str]) -> list[str]:
    text = "\n".join(_reflow(lines))
    for old, new in TEXT_FIXES:
        text = text.replace(old, new)
    text = FOOTNOTE_NUM_RE.sub(r"\1", text)
    text = FOOTNOTE_WORD_RE.sub(r"\1", text)
    return text.split("\n")


def clean_text(text: str) -> str:
    """Limpia el texto de un documento y devuelve solo contenido util."""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    for old, new in RAW_FIXES:
        text = text.replace(old, new)
    lines = [l.rstrip() for l in text.split("\n") if not _is_english(l)]

    cleaned: list[str] = []
    for is_code, seg in _split_segments(lines):
        cleaned.extend(seg if is_code else _clean_prose(seg))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip() + "\n"


def clean_documents(docs: list[Document]) -> list[Document]:
    """Aplica clean_text a cada Document y descarta los que queden vacios."""
    cleaned = [Document(page_content=clean_text(d.page_content),
                        metadata=dict(d.metadata)) for d in docs]
    return [d for d in cleaned if d.page_content.strip()]


if __name__ == "__main__":
    from src.ingest import load_documents

    raw = load_documents()
    for before, after in zip(raw, clean_documents(raw)):
        print(f"{before.metadata['source']:<20} "
              f"{len(before.page_content):>6} -> {len(after.page_content):>6} caracteres")
