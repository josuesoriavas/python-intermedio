"""Paso 1: descarga las fuentes originales del proyecto "El Niño y el agro peruano".

Fuentes (todas públicas, sin clave de API):
  - NOAA CPC, ERSSTv5: temperatura del mar mensual en las regiones Niño desde 1950,
    con anomalías respecto a 1991-2020. De aquí sale el ICEN (Niño 1+2), el índice
    que usa ENFEN para declarar El Niño costero en el Perú.
  - NOAA CPC, OISST v2: las mismas regiones con datos más recientes (para el estado actual).
  - FAOSTAT (FAO), dominio QCL: producción, área cosechada y rendimiento por cultivo,
    país y año (1961 en adelante). Se usa el archivo masivo (bulk) porque la API ahora pide token.

Uso:
    python scripts/obtener_datos.py          # descarga lo que falte
    python scripts/obtener_datos.py --forzar # vuelve a descargar todo
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"

FUENTES = {
    "ersst5_nino": {
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii",
        "archivo": "ersst5.nino.mth.91-20.ascii",
        "descripcion": "NOAA CPC - ERSSTv5, índices Niño mensuales 1950-hoy (anomalías base 1991-2020)",
        "pagina": "https://www.cpc.ncep.noaa.gov/data/indices/",
    },
    "oisst_nino": {
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices",
        "archivo": "sstoi.indices",
        "descripcion": "NOAA CPC - OISST v2, índices Niño mensuales 1982-hoy",
        "pagina": "https://www.cpc.ncep.noaa.gov/data/indices/",
    },
    "faostat_qcl": {
        "url": "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip",
        "archivo": "Production_Crops_Livestock_E_All_Data_(Normalized).zip",
        "descripcion": "FAOSTAT QCL - Producción de cultivos y ganadería, todos los países (formato largo)",
        "pagina": "https://www.fao.org/faostat/es/#data/QCL",
    },
}


def descargar(url: str, destino: Path) -> int:
    """Descarga en streaming (el zip de FAOSTAT pesa ~33 MB) y devuelve los bytes escritos."""
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        tmp = destino.with_suffix(destino.suffix + ".part")
        n = 0
        with open(tmp, "wb") as f:
            for bloque in r.iter_content(chunk_size=1 << 20):
                f.write(bloque)
                n += len(bloque)
        tmp.replace(destino)
    return n


def main(forzar: bool = False) -> None:
    ORIGINALES.mkdir(parents=True, exist_ok=True)
    registro_path = ORIGINALES / "fuentes.json"
    registro = json.loads(registro_path.read_text(encoding="utf-8")) if registro_path.exists() else {}

    for clave, f in FUENTES.items():
        destino = ORIGINALES / f["archivo"]
        if destino.exists() and not forzar:
            print(f"[ya existe] {destino.name}")
            continue
        print(f"[descargando] {f['url']}")
        n = descargar(f["url"], destino)
        registro[clave] = {
            **f,
            "bytes": n,
            "descargado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        }
        print(f"  -> {destino.name} ({n / 1e6:.1f} MB)")

    registro_path.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Registro de fuentes: {registro_path.relative_to(RAIZ)}")


if __name__ == "__main__":
    main(forzar="--forzar" in sys.argv)
