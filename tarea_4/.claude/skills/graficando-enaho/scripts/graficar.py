"""Gráficos de pobreza monetaria con la ENAHO 2024, siempre ponderados y con IC 95 %, título analítico y fuente.

    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por area
    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por sexo
    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por departamento
    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por grupo_edad --dividir area
    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por sexo --filtro "area == 'Rural'"
    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --indicador pobre_extremo --por region_natural
    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --todos      # área, sexo, departamento y edad

Cada gráfico se guarda en figuras/<nombre>.png (200 dpi) junto con figuras/<nombre>.csv, la tabla exacta que se graficó.
Si no existe la base limpia, corre antes la skill limpiando-enaho (scripts/limpiar.py).
"""
import argparse
import textwrap
import re
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

PROYECTO = Path(__file__).resolve().parents[4]
LIMPIEZA = PROYECTO / ".claude" / "skills" / "limpiando-enaho" / "scripts"
sys.path.insert(0, str(LIMPIEZA))
from estimacion import media, proporcion  # noqa: E402

FIGURAS = PROYECTO / "figuras"
AZUL, NARANJA, GRIS, TINTA, TINTA2, FONDO = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b", "#52514e", "#fcfcfb"
ORDEN = {"grupo_edad": ["0-14", "15-29", "30-44", "45-64", "65 y más"], "area": ["Urbana", "Rural"],
         "region_natural": ["Lima Metropolitana", "Costa", "Sierra", "Selva"],
         "condicion_pobreza": ["Pobre extremo", "Pobre no extremo", "No pobre"]}
ETIQUETA = {"area": "área de residencia", "sexo": "sexo", "grupo_edad": "grupo de edad",
            "sexo_jefe": "sexo del jefe de hogar", "region_natural": "región natural", "nombre_dominio": "dominio",
            "departamento": "departamento", "condicion_pobreza": "condición de pobreza"}
# Qué se grafica: un % de personas (pobreza) o la media ponderada de una variable continua.
META = {
    "pobre": {"nombre": "Pobreza monetaria", "eje": "% de personas en pobreza monetaria",
              "unidad": "% de personas", "fmt": "{:.1f} %", "media": False},
    "pobre_extremo": {"nombre": "Pobreza monetaria extrema", "eje": "% de personas en pobreza monetaria extrema",
                      "unidad": "% de personas", "fmt": "{:.1f} %", "media": False},
    "participacion_alimentos": {"nombre": "Participación de los alimentos en el gasto del hogar",
                                "eje": "% del gasto total del hogar destinado a alimentos",
                                "unidad": "% del gasto del hogar, promedio por persona", "fmt": "{:.1f} %",
                                "media": True},
    "gasto_pc_mensual": {"nombre": "Gasto per cápita mensual", "eje": "soles por persona al mes",
                         "unidad": "soles corrientes por persona al mes", "fmt": "S/ {:,.0f}", "media": True},
}
INDICADOR = {k: v["nombre"] for k, v in META.items()}


def fmt(indicador, v):
    return META[indicador]["fmt"].format(v)


def estimador(indicador):
    return media if META[indicador]["media"] else proporcion


def cargar_base(anio=2024):
    archivo = PROYECTO / "salidas" / f"personas_{anio}.parquet"
    if not archivo.exists():
        print("No existe salidas/personas_2024.parquet: ejecuto primero limpiando-enaho (limpiar.py)...")
        r = subprocess.run([sys.executable, str(LIMPIEZA / "limpiar.py"), "--anio", str(anio)])
        if r.returncode != 0 or not archivo.exists():
            sys.exit("ERROR: la limpieza no produjo una base válida (ver salidas/validacion.txt). No grafico nada.")
    return pd.read_parquet(archivo)


def estimar(df, indicador, por, dividir=None):
    if dividir:
        partes = []
        for g in ORDEN.get(dividir, sorted(df[dividir].dropna().unique())):
            t = estimador(indicador)(df[df[dividir] == g], indicador, por=por)
            t["serie"] = g
            partes.append(t)
        t = pd.concat(partes, ignore_index=True)
    else:
        t = estimador(indicador)(df, indicador, por=por)
        t["serie"] = "Total"
    if por == "departamento":
        t["grupo"] = t.grupo.map(df.drop_duplicates("departamento").set_index("departamento").nombre_departamento)
    return t


FRASE = {"Hombre": "los hombres", "Mujer": "las mujeres", "Urbana": "el área urbana", "Rural": "el área rural",
         "Jefe hombre": "los hogares con jefe hombre", "Jefa mujer": "los hogares con jefa mujer",
         "Pobre extremo": "las personas en pobreza extrema", "Pobre no extremo": "las personas en pobreza no extrema",
         "No pobre": "las personas no pobres"}


def frase(grupo, por):
    if grupo in FRASE:
        return FRASE[grupo]
    if por == "grupo_edad":
        return f"el grupo de {grupo} años".replace("de 65 y más años", "de 65 años y más")
    return str(grupo)


def titulo_automatico(t, indicador, por):
    """Un título que dice el hallazgo, calculado con los mismos números del gráfico."""
    nombre = INDICADOR[indicador].lower().replace("pobreza monetaria", "pobreza")
    series = list(dict.fromkeys(t.serie))
    if META[indicador]["media"]:   # variable continua: comparación neutra entre el valor más alto y el más bajo
        s0 = t[t.serie == series[0]].sort_values("valor_pct", ascending=False)
        alto, bajo = s0.iloc[0], s0.iloc[-1]
        extra = " (diferencia no concluyente)" if alto.ic95_inf <= bajo.ic95_sup else ""
        donde = f" en {frase(series[0], '')}" if len(series) > 1 else ""
        return (f"{INDICADOR[indicador]}{donde}: {fmt(indicador, alto.valor_pct)} en {frase(alto.grupo, por)} frente a "
                f"{fmt(indicador, bajo.valor_pct)} en {frase(bajo.grupo, por)}{extra}")
    if len(series) == 2:   # barras agrupadas: ¿una serie supera a la otra en todos los grupos?
        a = t[t.serie == series[0]].set_index("grupo")
        b = t[t.serie == series[1]].set_index("grupo")
        dif = (b.valor_pct - a.valor_pct).dropna()
        g = dif.abs().idxmax()
        mayor, menor = (series[1], series[0]) if dif[g] > 0 else (series[0], series[1])
        todos = "en todos los grupos" if (dif > 0).all() or (dif < 0).all() else "en la mayoría de grupos"
        return (f"La {nombre} en {frase(mayor, '')} supera a la de {frase(menor, '')} {todos}; la brecha mayor está "
                f"en {frase(g, por)} ({max(a.valor_pct[g], b.valor_pct[g]):.1f} % frente a "
                f"{min(a.valor_pct[g], b.valor_pct[g]):.1f} %)")
    t = t.sort_values("valor_pct", ascending=False)
    alto, bajo = t.iloc[0], t.iloc[-1]
    if len(t) == 2:
        if alto.ic95_inf <= bajo.ic95_sup:
            return (f"Sin diferencia concluyente en la {nombre} entre {frase(alto.grupo, por)} ({alto.valor_pct:.1f} %) "
                    f"y {frase(bajo.grupo, por)} ({bajo.valor_pct:.1f} %)")
        return (f"La {nombre} en {frase(alto.grupo, por)} ({alto.valor_pct:.1f} %) supera en "
                f"{alto.valor_pct - bajo.valor_pct:.1f} puntos a la de {frase(bajo.grupo, por)} ({bajo.valor_pct:.1f} %)")
    veces = alto.valor_pct / bajo.valor_pct if bajo.valor_pct else float("nan")
    primero = frase(alto.grupo, por)
    return (f"{primero[0].upper() + primero[1:]} tiene la mayor {nombre} ({alto.valor_pct:.1f} %), {veces:.1f} veces "
            f"la de {frase(bajo.grupo, por)} ({bajo.valor_pct:.1f} %)")


def graficar(t, indicador, por, dividir, filtro, titulo, nacional, archivo):
    series = list(dict.fromkeys(t.serie))
    if por in ORDEN:
        grupos = [g for g in ORDEN[por] if g in set(t.grupo)]
    else:
        base = t[t.serie == series[0]].sort_values("valor_pct", ascending=True)
        grupos = list(base.grupo)   # de menor a mayor: la mayor queda arriba
    if por in ORDEN:
        grupos = grupos[::-1]       # orden natural de arriba hacia abajo
    lineas_titulo = textwrap.wrap(titulo.replace(" %", " %"), 88)   # «27.4 %» no se parte
    sub = (f"{INDICADOR[indicador]} según {ETIQUETA.get(por, por)}"
           + (f" y {ETIQUETA.get(dividir, dividir)}" if dividir else "")
           + f", Perú 2024 ({META[indicador]['unidad']}; líneas grises: IC 95 %)"
           + (f". Filtro: {filtro}" if filtro else ""))
    lineas_sub = textwrap.wrap(sub, 118)
    cabecera = 0.32 + 0.24 * len(lineas_titulo) + 0.18 * len(lineas_sub) + 0.12   # pulgadas para título y subtítulo
    alto_fig = max(3.2, 0.34 * len(grupos) * len(series) + 1.2) + cabecera
    fig, ax = plt.subplots(figsize=(9, alto_fig), facecolor=FONDO)
    ax.set_facecolor(FONDO)
    colores = [AZUL, NARANJA]
    ancho = 0.8 / len(series)
    for i, (s, color) in enumerate(zip(series, colores)):
        d = t[t.serie == s].set_index("grupo").reindex(grupos)
        y = [k - (i - (len(series) - 1) / 2) * ancho for k in range(len(grupos))]   # la 1.ª serie arriba
        ax.barh(y, d.valor_pct, height=ancho * 0.9, color=color, label=None if s == "Total" else s, zorder=2)
        ax.errorbar(d.valor_pct, y, xerr=[d.valor_pct - d.ic95_inf, d.ic95_sup - d.valor_pct], fmt="none",
                    ecolor=GRIS, elinewidth=1, capsize=2, zorder=3)
        for yy, v, sup in zip(y, d.valor_pct, d.ic95_sup):
            ax.text(sup + 0.01 * t.ic95_sup.max(), yy, fmt(indicador, v), va="center", ha="left", fontsize=8.5, color=TINTA, zorder=4,
                    bbox={"facecolor": FONDO, "edgecolor": "none", "pad": 0.5})
    ax.set_yticks(range(len(grupos)))
    ax.set_yticklabels(grupos, fontsize=9, color=TINTA)
    ax.axvline(nacional, color=TINTA2, lw=1, ls="--", zorder=1)
    ax.text(nacional, len(grupos) - 0.4, f" Perú: {fmt(indicador, nacional)}", fontsize=8, color=TINTA2, va="bottom")
    ax.set_xlim(0, max(t.ic95_sup.max() * 1.15, nacional * 1.2))
    ax.set_ylim(-0.6, len(grupos) - 0.2)
    ax.set_xlabel(META[indicador]["eje"], fontsize=9, color=TINTA2)
    ax.grid(axis="x", color="#e4e3df", lw=0.8, zorder=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=TINTA2, labelsize=8)
    if len(series) > 1:
        ax.legend(title=ETIQUETA.get(dividir, dividir).capitalize(), fontsize=8, title_fontsize=8, frameon=False,
                  loc="lower right")
    pulg = 1 / alto_fig   # una pulgada en coordenadas de figura
    fig.text(0.015, 1 - 0.22 * pulg, "\n".join(lineas_titulo), ha="left", va="top", fontsize=11.5,
             fontweight="bold", color=TINTA, linespacing=1.25)
    fig.text(0.015, 1 - (0.3 + 0.24 * len(lineas_titulo)) * pulg, chr(10).join(lineas_sub), ha="left", va="top", fontsize=9,
             color=TINTA2)
    fig.text(0.015, 0.12 * pulg, "Fuente: INEI, ENAHO 2024 (módulos 34 y 02). Residentes habituales ponderados con "
             "facpob07; IC de diseño (conglome dentro de estrato). Elaboración: skill graficando-enaho.",
             fontsize=7, color=TINTA2)
    fig.tight_layout(rect=(0, 0.35 * pulg, 1, 1 - cabecera * pulg))
    FIGURAS.mkdir(exist_ok=True)
    png = FIGURAS / f"{archivo}.png"
    fig.savefig(png, dpi=200, facecolor=FONDO)
    plt.close(fig)
    t.round(3).to_csv(FIGURAS / f"{archivo}.csv", index=False)
    return png


def un_grafico(df, indicador, por, dividir=None, filtro=None, titulo=None, archivo=None):
    if por not in df.columns:
        sys.exit(f"ERROR: no existe la columna {por!r}. Opciones: {', '.join(ETIQUETA)}")
    sub = df.query(filtro) if filtro else df
    if sub.empty:
        sys.exit(f"ERROR: el filtro {filtro!r} no deja observaciones.")
    t = estimar(sub, indicador, por, dividir)
    nacional = estimador(indicador)(sub, indicador).valor_pct.iloc[0]
    titulo = titulo or re.sub(r"\bde el\b", "del", titulo_automatico(t, indicador, por))
    archivo = archivo or "_".join(x for x in [indicador.replace("pobre", "pobreza"), por, dividir,
                                                re.sub(r"\W+", "_", filtro or "").strip("_").lower()] if x)
    png = graficar(t, indicador, por, dividir, filtro, titulo, nacional, archivo)
    print(f"Guardado {png.relative_to(PROYECTO)} (+ .csv). Título: {titulo}")
    cols = ["serie", "grupo", "valor_pct", "ic95_inf", "ic95_sup", "n_muestra"]
    print(t[cols].round(2).to_string(index=False))
    return png


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--por", default="area", help=f"agrupación: {', '.join(ETIQUETA)}")
    p.add_argument("--dividir", help="segunda dimensión para barras agrupadas (p. ej. area o sexo)")
    p.add_argument("--indicador", default="pobre", choices=list(INDICADOR),
                   help="pobre, pobre_extremo (% de personas) o una media: participacion_alimentos, gasto_pc_mensual")
    p.add_argument("--filtro", help="subconjunto con sintaxis de pandas.query, p. ej. \"area == 'Rural'\"")
    p.add_argument("--titulo", help="título analítico; si no se da, se genera con el hallazgo principal")
    p.add_argument("--archivo", help="nombre del archivo sin extensión (en figuras/)")
    p.add_argument("--todos", action="store_true", help="genera los gráficos básicos: área, sexo, departamento, edad")
    a = p.parse_args()
    df = cargar_base()
    if a.todos:
        for por, div in (("area", None), ("sexo", None), ("departamento", None), ("grupo_edad", "area")):
            un_grafico(df, a.indicador, por, div)
    else:
        un_grafico(df, a.indicador, a.por, a.dividir, a.filtro, a.titulo, a.archivo)


if __name__ == "__main__":
    main()
