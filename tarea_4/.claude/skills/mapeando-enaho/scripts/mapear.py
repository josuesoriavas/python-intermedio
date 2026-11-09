"""Mapa coroplético de la pobreza monetaria por departamento (ENAHO 2024), unido por código y comparado con la referencia.

    uv run python .claude/skills/mapeando-enaho/scripts/mapear.py                       # residentes habituales, facpob07
    uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --metodo inei_hogares # método oficial del INEI
    uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --indicador pobre_extremo

Une ubigeo[:2] (departamento) con FIRST_IDDP del GeoJSON, nunca por nombre. Exige 25 unidades con dato y Lima (15) y
Callao (07) separados; si no, se detiene. Guarda en mapas/ el PNG, la tabla graficada y la comparación con
referencias/pobreza_departamento_2024.csv (Sesión 16).
"""
import argparse
import subprocess
import sys
import textwrap
from pathlib import Path

import geopandas as gpd
import httpx
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

SKILL = Path(__file__).resolve().parents[1]
PROYECTO = Path(__file__).resolve().parents[4]
LIMPIEZA = PROYECTO / ".claude" / "skills" / "limpiando-enaho" / "scripts"
sys.path.insert(0, str(LIMPIEZA))
from estimacion import proporcion  # noqa: E402

GEOJSON = PROYECTO / "datos" / "geo" / "peru_departamental_simple.geojson"
URL_GEOJSON = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/"
               "peru_departamental_simple.geojson")
REFERENCIA = SKILL / "referencias" / "pobreza_departamento_2024.csv"
MAPAS = PROYECTO / "mapas"
# Rampa secuencial de un solo tono (azul), de claro a oscuro, en clases de 10 puntos desde 0
CORTES = [0, 10, 20, 30, 40, 50]
COLORES = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
TINTA, TINTA2, FONDO = "#0b0b0b", "#52514e", "#fcfcfb"
INDICADOR = {"pobre": "pobreza monetaria", "pobre_extremo": "pobreza monetaria extrema"}


class ErrorDeUnion(Exception):
    pass


def cargar(metodo, anio=2024):
    archivo = PROYECTO / "salidas" / f"{'personas' if metodo == 'personas' else 'hogares'}_{anio}.parquet"
    if not archivo.exists():
        print(f"No existe {archivo.relative_to(PROYECTO)}: ejecuto primero limpiando-enaho (limpiar.py)...")
        r = subprocess.run([sys.executable, str(LIMPIEZA / "limpiar.py"), "--anio", str(anio)])
        if r.returncode != 0 or not archivo.exists():
            sys.exit("ERROR: la limpieza no produjo una base válida (ver salidas/validacion.txt). No mapeo nada.")
    return pd.read_parquet(archivo)


def geometrias():
    if not GEOJSON.exists():
        GEOJSON.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(URL_GEOJSON, timeout=120, follow_redirects=True)
        r.raise_for_status()
        GEOJSON.write_bytes(r.content)
    geo = gpd.read_file(GEOJSON)
    geo["FIRST_IDDP"] = geo.FIRST_IDDP.astype(str).str.zfill(2)
    return geo


def unir(geo, tabla):
    """Une por código oficial (FIRST_IDDP = ubigeo[:2]) y comprueba 25 unidades con dato."""
    if geo.FIRST_IDDP.duplicated().any() or tabla.departamento.duplicated().any():
        raise ErrorDeUnion("Hay códigos departamentales duplicados en el GeoJSON o en la tabla.")
    m = geo.merge(tabla, left_on="FIRST_IDDP", right_on="departamento", how="outer", validate="1:1", indicator=True)
    sin_geo = m.loc[m._merge == "right_only", "departamento"].tolist()
    sin_dato = m.loc[m._merge == "left_only", "FIRST_IDDP"].tolist()
    if sin_geo or sin_dato or len(m) != 25 or m.valor_pct.isna().any():
        raise ErrorDeUnion(f"Unión incompleta: {len(m)} filas; sin geometría {sin_geo}; sin dato {sin_dato}.")
    if not {"07", "15"} <= set(m.FIRST_IDDP):
        raise ErrorDeUnion("Lima (15) y Callao (07) deben estar como unidades separadas.")
    return gpd.GeoDataFrame(m.drop(columns="_merge"), geometry="geometry", crs=geo.crs)


def comparar(tabla_personas, tabla_inei):
    ref = pd.read_csv(REFERENCIA, dtype={"ccdd": str}).rename(columns={"departamento": "nombre_ref"})
    ref = ref.rename(columns={"ccdd": "departamento", "pobreza_pct": "referencia_s16"})
    c = ref.merge(tabla_personas[["departamento", "nombre", "valor_pct"]].rename(columns={"valor_pct": "personas"}),
                  on="departamento", validate="1:1")
    c = c.merge(tabla_inei[["departamento", "valor_pct"]].rename(columns={"valor_pct": "inei_hogares"}),
                on="departamento", validate="1:1")
    c["personas"], c["inei_hogares"] = c.personas.round(1), c.inei_hogares.round(1)
    c["dif_personas"] = (c.personas - c.referencia_s16).round(1)
    c["dif_inei"] = (c.inei_hogares - c.referencia_s16).round(1)
    return c[["departamento", "nombre", "referencia_s16", "personas", "dif_personas", "inei_hogares", "dif_inei"]]


def titulo_automatico(g, indicador):
    s = g.sort_values("valor_pct", ascending=False)
    a, b, z = s.iloc[0], s.iloc[1], s.iloc[-1]
    return (f"{a.nombre} ({a.valor_pct:.1f} %) y {b.nombre} ({b.valor_pct:.1f} %) tienen la mayor "
            f"{INDICADOR[indicador]}; {z.nombre} ({z.valor_pct:.1f} %), la menor")


def dibujar(g, indicador, metodo, titulo, nacional, png):
    cortes = CORTES if g.valor_pct.max() <= CORTES[-1] else CORTES[:-1] + [100]
    cmap, norm = ListedColormap(COLORES), BoundaryNorm(cortes, len(COLORES))
    fig, ax = plt.subplots(figsize=(8, 10), facecolor=FONDO)
    ax.set_facecolor(FONDO)
    g.plot(ax=ax, column="valor_pct", cmap=cmap, norm=norm, edgecolor="white", linewidth=0.8)
    for _, r in g.iterrows():
        oscuro = r.valor_pct >= cortes[3]
        p = r.geometry.representative_point()
        if r.FIRST_IDDP == "07":   # Callao es muy pequeño: etiqueta afuera, con guía
            ax.annotate(f"Callao\n{r.valor_pct:.1f}", xy=(p.x, p.y), xytext=(p.x - 2.6, p.y + 0.2), fontsize=7.5,
                        color=TINTA, ha="center", arrowprops={"arrowstyle": "-", "color": TINTA2, "lw": 0.7})
            continue
        ax.text(p.x, p.y, f"{r.nombre}\n{r.valor_pct:.1f}", ha="center", va="center", fontsize=6.8,
                color="white" if oscuro else TINTA, linespacing=1.1)
    conteo = pd.cut(g.valor_pct, cortes, right=False).value_counts().sort_index()
    etiquetas = [f"{a:g} a < {b:g} % ({n} dep.)" for (a, b), n in zip(zip(cortes[:-1], cortes[1:]), conteo)]
    ax.legend(handles=[Patch(facecolor=c, edgecolor="white", label=e) for c, e in zip(COLORES, etiquetas)],
              title=f"% de personas en\n{INDICADOR[indicador]}", loc="lower left", fontsize=8, title_fontsize=8.5,
              frameon=False)
    ax.set_axis_off()
    lineas = textwrap.wrap(titulo, 70)
    fig.text(0.03, 0.985, "\n".join(lineas), ha="left", va="top", fontsize=12, fontweight="bold", color=TINTA)
    metodo_txt = ("residentes habituales ponderados con facpob07" if metodo == "personas"
                  else "método INEI: sumaria ponderada con factor07 × mieperho")
    fig.text(0.03, 0.985 - 0.024 * len(lineas) - 0.006,
             f"{INDICADOR[indicador].capitalize()} por departamento, Perú 2024 (% de personas). Promedio nacional: "
             f"{nacional:.1f} %. Lima y Callao por separado.", ha="left", va="top", fontsize=9, color=TINTA2)
    fig.text(0.03, 0.012, f"Fuente: INEI, ENAHO 2024 (módulos 34 y 02), {metodo_txt}. Límites: GeoJSON departamental\n"
             "del repositorio del curso (d2cml-ai). Unión por código: ubigeo[:2] = FIRST_IDDP. Elaboración: skill "
             "mapeando-enaho.", fontsize=7, color=TINTA2)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.985 - 0.024 * len(lineas) - 0.04, bottom=0.05)
    fig.savefig(png, dpi=200, facecolor=FONDO)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--indicador", default="pobre", choices=list(INDICADOR))
    p.add_argument("--metodo", default="personas", choices=["personas", "inei_hogares"])
    p.add_argument("--titulo")
    p.add_argument("--archivo")
    a = p.parse_args()

    tablas = {}
    for metodo in ("personas", "inei_hogares"):
        df = cargar(metodo)
        peso = "facpob07" if metodo == "personas" else "peso_inei"
        t = proporcion(df, a.indicador, peso=peso, por="departamento").rename(columns={"grupo": "departamento"})
        nombres = df.drop_duplicates("departamento").set_index("departamento").nombre_departamento
        t["nombre"] = t.departamento.map(nombres)
        tablas[metodo] = (t, proporcion(df, a.indicador, peso=peso).valor_pct.iloc[0])
    tabla, nacional = tablas[a.metodo]

    try:
        g = unir(geometrias(), tabla)
    except ErrorDeUnion as e:
        sys.exit(f"ERROR: {e} No se genera el mapa.")
    MAPAS.mkdir(exist_ok=True)
    sufijo = ("" if a.indicador == "pobre" else "_extrema") + ("" if a.metodo == "personas" else "_inei")
    nombre = a.archivo or f"pobreza_departamento_2024{sufijo}"
    titulo = a.titulo or titulo_automatico(g, a.indicador)
    dibujar(g, a.indicador, a.metodo, titulo, nacional, MAPAS / f"{nombre}.png")
    cols = ["departamento", "nombre", "valor_pct", "ee_pct", "ic95_inf", "ic95_sup", "n_muestra", "poblacion_expandida"]
    g.sort_values("valor_pct", ascending=False)[cols].round(3).to_csv(MAPAS / f"{nombre}.csv", index=False)
    print(f"Mapa: mapas/{nombre}.png · {g.FIRST_IDDP.nunique()}/25 unidades con dato · unión por FIRST_IDDP = "
          f"ubigeo[:2] · Lima (15) y Callao (07) separados\nTítulo: {titulo}")

    if a.indicador == "pobre":   # la referencia de la Sesión 16 es de pobreza total
        c = comparar(tablas["personas"][0], tablas["inei_hogares"][0])
        c.to_csv(MAPAS / "comparacion_referencia.csv", index=False)
        resumen = (f"Comparación con referencias/pobreza_departamento_2024.csv (Sesión 16), redondeado a 1 decimal:\n"
                   f"  método INEI (factor07 × mieperho): {int((c.dif_inei == 0).sum())}/25 iguales, "
                   f"máx. |dif| = {c.dif_inei.abs().max():.1f} pp\n"
                   f"  residentes habituales (facpob07): {int((c.dif_personas == 0).sum())}/25 iguales, "
                   f"máx. |dif| = {c.dif_personas.abs().max():.1f} pp "
                   f"({', '.join(c.loc[c.dif_personas.abs() >= 0.3, 'nombre'])} con |dif| ≥ 0.3), "
                   f"correlación de rangos = {c.referencia_s16.rank().corr(c.personas.rank()):.3f}\n"
                   "  La diferencia viene de la población: residentes habituales frente a miembros del hogar (mieperho). "
                   "Ver salidas/validacion.txt.")
        (MAPAS / "comparacion_referencia.txt").write_text(resumen + "\n", encoding="utf-8")
        print(resumen)


if __name__ == "__main__":
    main()
