"""Oculta correos, claves, tokens y la carpeta personal del usuario en los archivos de texto ya generados.

    uv run python scripts/ocultar_evidencias.py                 # evidencias_ia/ y salidas/
    uv run python scripts/ocultar_evidencias.py evidencias_ia   # una carpeta

Usa los mismos patrones que scripts/exportar_conversacion.py y reescribe solo los archivos que cambian.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from exportar_conversacion import ocultar  # noqa: E402

PROYECTO = Path(__file__).resolve().parents[1]
TEXTO = {".md", ".jsonl", ".txt", ".csv", ".json"}

if __name__ == "__main__":
    cambiados = 0
    for carpeta in sys.argv[1:] or ["evidencias_ia", "salidas"]:
        for archivo in sorted((PROYECTO / carpeta).rglob("*")):
            if archivo.suffix not in TEXTO or not archivo.is_file():
                continue
            texto = archivo.read_text(encoding="utf-8")
            limpio = ocultar(texto)
            if limpio != texto:
                archivo.write_text(limpio, encoding="utf-8")
                cambiados += 1
                print(f"oculto: {archivo.relative_to(PROYECTO)}")
    print(f"{cambiados} archivos modificados")
