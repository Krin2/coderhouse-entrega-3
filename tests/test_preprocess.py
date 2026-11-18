"""Pruebas de la limpieza determinista (sin API ni red)."""
from src.preprocess import clean_text


def test_no_une_lineas_repl_fuera_de_fences():
    raw = "Si escribes una expresión, el intérprete la evalúa y muestra el\nresultado:\n>>> 1 + 1\n2\nSin embargo, en un script no hace nada.\n"
    out = clean_text(raw)
    assert ">>> 1 + 1\n2\nSin embargo" in out
    assert "muestra el resultado:" in out        # la prosa si se une


def test_une_prosa_partida_y_titulos():
    out = clean_text("2.4 Sentencias\nUna sentencia es una unidad de\ncódigo ejecutable.\n")
    assert out.startswith("# 2.4 Sentencias\n")
    assert "unidad de código ejecutable." in out


def test_conserva_codigo_y_quita_notas_al_pie():
    out = clean_text("La palabra mnemónico2 ayuda.\n```python\nx1q3z9ahd = 35.0\n```\n")
    assert "mnemónico ayuda" in out and "mnemónico2" not in out
    assert "```python\nx1q3z9ahd = 35.0\n```" in out


def test_lista_de_una_palabra_por_linea():
    words = "\n".join(["and", "as", "assert", "break", "class", "del", "elif",
                       "else", "except", "finally"])
    out = clean_text(f"Palabras reservadas:\n{words}\nFin de la lista.\n")
    assert "Lista: and, as, assert" in out and "Fin de la lista." in out
