"""Consulta ponderada sobre la base limpia de la ENAHO: % de pobres (o media de una variable) por grupos y filtros.

    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py                                  # pobreza nacional
    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por area
    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por departamento --orden desc
    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por sexo --filtro "area == 'Rural'"
    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --indicador pobre_extremo --por region_natural
    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --media gasto_pc_mensual --por area
    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por departamento --metodo inei_hogares

Siempre pondera (facpob07 en personas; factor07 × mieperho en el método INEI) y da el IC 95 % de diseño.
Si no existe la base limpia, corre antes limpiar.py.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from estimacion import media, proporcion  # noqa: E402

PROYECTO = Path(__file__).resolve().parents[4]


def cargar(metodo, anio=2024):
    archivo = PROYECTO / "salidas" / f"{'personas' if metodo == 'personas' else 'hogares'}_{anio}.parquet"
    if not archivo.exists():
        print(f"No existe {archivo.relative_to(PROYECTO)}: corro limpiar.py primero...", file=sys.stderr)
        r = subprocess.run([sys.executable, str(Path(__file__).parent / "limpiar.py"), "--anio", str(anio)],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            sys.exit(f"ERROR: la limpieza falló; no hay cifras que reportar.\n{r.stdout[-1500:]}\n{r.stderr[-800:]}")
    return pd.read_parquet(archivo)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--indicador", default="pobre", help="variable 0/1: pobre (defecto) o pobre_extremo")
    p.add_argument("--media", help="en vez de un %, la media ponderada de esta variable (p. ej. gasto_pc_mensual)")
    p.add_argument("--por", help="columna para agrupar: area, sexo, grupo_edad, sexo_jefe, region_natural, "
                                 "nombre_dominio, departamento, ...")
    p.add_argument("--filtro", help="subconjunto con sintaxis de pandas.query, p. ej. \"area == 'Rural'\"")
    p.add_argument("--metodo", default="personas", choices=["personas", "inei_hogares"])
    p.add_argument("--orden", choices=["asc", "desc"])
    p.add_argument("--csv", help="guarda la tabla en este CSV")
    a = p.parse_args()

    df = cargar(a.metodo)
    if a.filtro:
        df = df.query(a.filtro)
        if df.empty:
            sys.exit(f"ERROR: el filtro {a.filtro!r} no deja observaciones.")
    peso = "facpob07" if a.metodo == "personas" else "peso_inei"
    if a.por and a.por not in df.columns:
        sys.exit(f"ERROR: la columna {a.por!r} no existe en la base {a.metodo}. Columnas: {', '.join(df.columns)}")
    t = media(df, a.media, peso=peso, por=a.por) if a.media else proporcion(df, a.indicador, peso=peso, por=a.por)
    if a.por == "departamento" and "nombre_departamento" in df.columns:
        nombres = df.drop_duplicates("departamento").set_index("departamento").nombre_departamento
        t.insert(1, "nombre", t.grupo.map(nombres))
    if a.orden:
        t = t.sort_values("valor_pct", ascending=a.orden == "asc")
    unidad = a.media if a.media else f"% de {'personas' if a.metodo == 'personas' else 'personas (método INEI)'}"
    t = t.rename(columns={"valor_pct": "valor", "ee_pct": "ee"})
    print(t.round({"valor": 2, "ee": 2, "ic95_inf": 2, "ic95_sup": 2, "poblacion_expandida": 0})
          .to_string(index=False))
    print(f"\nIndicador: {a.media or a.indicador} ({unidad}) · peso: {peso} · filtro: {a.filtro or 'ninguno'} · "
          f"n = {len(df):,} {'personas' if a.metodo == 'personas' else 'hogares'}\n"
          "Fuente: INEI, ENAHO 2024 (módulos 34 y 02), procesado con .claude/skills/limpiando-enaho")
    if a.csv:
        t.to_csv(a.csv, index=False)


if __name__ == "__main__":
    main()
