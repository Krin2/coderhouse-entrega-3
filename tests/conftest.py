"""Configuracion comun de pytest.

Las pruebas offline (chunking, limpieza) no necesitan API; si no hay
OPENAI_API_KEY se usa una clave ficticia solo para poder importar src.config
y las pruebas de integracion se omiten (RAG_OFFLINE=1).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-offline-ficticia"
    os.environ["RAG_OFFLINE"] = "1"
