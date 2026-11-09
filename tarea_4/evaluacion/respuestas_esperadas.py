"""Calcula las respuestas esperadas de la evaluación SIN usar el servidor MCP ni las skills del proyecto.

    uv run python evaluacion/respuestas_esperadas.py        # escribe evaluacion/preguntas.csv

Verificación independiente:
- BCRP: llamada directa a la API pública (https://estadisticas.bcrp.gob.pe/estadisticas/series/api/...) con httpx,
  sin importar mcp/server.py. Las cifras se pueden contrastar a mano en la web del BCRP (columna fuente_verificacion).
- ENAHO: lectura directa de los .dta del INEI con pandas, con un código mínimo escrito aparte del de las skills
  (no importa limpiar.py ni estimacion.py). Para las cifras que el INEI publica (27.6 %, 39.3 %, 24.8 %) se usa además
  la cifra oficial como referencia.
Las respuestas se fijan ANTES de correr el experimento (ver el historial de git de preguntas.csv) y no se cambian
después de ver lo que respondió el agente.
"""
import io
import zipfile
from pathlib import Path

import httpx
import pandas as pd

AQUI = Path(__file__).parent
DATOS = AQUI.parent / "datos" / "inei"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{desde}/{hasta}"
WEB = "https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/{codigo}/html"


def bcrp(codigo, desde, hasta):
    r = httpx.get(API.format(codigo=codigo, desde=desde, hasta=hasta), timeout=60)
    r.raise_for_status()
    js = r.json()
    return [(p["name"], float(p["values"][0])) for p in js["periods"] if p["values"][0] not in ("n.d.", "")]


def dta(zipname, interno, columnas):
    with zipfile.ZipFile(DATOS / zipname) as z:
        df = pd.read_stata(io.BytesIO(z.read(interno)), convert_categoricals=False)
    df.columns = [c.lower() for c in df.columns]
    return df[columnas]


def tasa(df, y, w):
    return 100 * (df[w] * df[y]).sum() / df[w].sum()


def main():
    # ------------------------------------------------------------------ BCRP (API directa)
    ipc_dic24 = dict(bcrp("PN01273PM", "2024-12", "2024-12"))["Dic.2024"]
    pbi_2024 = dict(bcrp("PM04923AA", "2024", "2024"))["2024"]
    tc_2024 = [v for _, v in bcrp("PN01206PM", "2024-1", "2024-12")]
    assert len(tc_2024) == 12
    tc_prom = sum(tc_2024) / 12
    alim = bcrp("PN09822PM", "2020-1", "2024-12")
    alim_dic24 = dict(alim)["Dic.2024"]
    pico_mes, pico = max(alim, key=lambda x: x[1])
    (mes_b4, alim_oct26), = bcrp("PN09822PM", "2026-10", "2026-10")   # el dato más reciente al 9/11/2026
    assert mes_b4 == "Oct.2026"

    # ------------------------------------------------------------------ ENAHO (lectura directa de los .dta)
    s = dta("966-Modulo34.zip", "966-Modulo34/sumaria-2024.dta",
            ["conglome", "vivienda", "hogar", "ubigeo", "estrato", "pobreza", "mieperho", "factor07", "gashog2d",
             "gru11hd", "gru12hd1", "gru12hd2", "gru13hd1", "gru13hd2", "gru13hd3", "sg23", "sig24", "gru14hd",
             "gru14hd1", "gru14hd2", "gru14hd3", "gru14hd4", "gru14hd5", "sg25", "sig26", "sg27", "sig28"])
    m = dta("966-Modulo02.zip", "966-Modulo02/enaho01-2024-200.dta",
            ["conglome", "vivienda", "hogar", "codperso", "p204", "p205", "p206", "p208a", "facpob07"])
    s["pobre"] = (s.pobreza <= 2).astype(int)
    s["w_inei"] = s.factor07 * s.mieperho
    s["rural"] = s.estrato >= 6
    s["dpto"] = s.ubigeo.str[:2]
    comida = [c for c in s.columns if c.startswith(("gru1", "sg2", "sig2"))]
    s["alim_pct"] = 100 * s[comida].fillna(0).sum(axis=1) / s.gashog2d
    res = m[((m.p204 == 1) & (m.p205 == 2)) | ((m.p204 == 2) & (m.p206 == 1))]
    p = res.merge(s, on=["conglome", "vivienda", "hogar"], validate="m:1")

    pob_inei = tasa(s, "pobre", "w_inei")
    pob_pers = tasa(p, "pobre", "facpob07")
    rural_inei, urb_inei = tasa(s[s.rural], "pobre", "w_inei"), tasa(s[~s.rural], "pobre", "w_inei")
    rural_pers, urb_pers = tasa(p[p.rural], "pobre", "facpob07"), tasa(p[~p.rural], "pobre", "facpob07")
    dep_inei = s.groupby("dpto").apply(lambda g: tasa(g, "pobre", "w_inei"), include_groups=False)
    dep_pers = p.groupby("dpto").apply(lambda g: tasa(g, "pobre", "facpob07"), include_groups=False)
    ninos = tasa(p[p.p208a <= 14], "pobre", "facpob07")
    ext = p[p.pobreza == 1]
    alim_ext = (ext.facpob07 * ext.alim_pct).sum() / ext.facpob07.sum()

    print(f"BCRP: IPC dic24 {ipc_dic24:.4f} | PBI 2024 {pbi_2024:.4f} | TC prom 2024 {tc_prom:.4f} | "
          f"alim dic24 {alim_dic24:.4f} | pico alim {pico_mes} {pico:.4f} | alim oct26 {alim_oct26:.4f}")
    print(f"ENAHO: pobreza INEI {pob_inei:.2f} / personas {pob_pers:.2f} | rural {rural_inei:.2f}/{rural_pers:.2f} | "
          f"urbana {urb_inei:.2f}/{urb_pers:.2f} | máx dpto {dep_inei.idxmax()} {dep_inei.max():.2f}/"
          f"{dep_pers.idxmax()} {dep_pers.max():.2f} | 0-14 {ninos:.2f} | alim pobres extremos {alim_ext:.2f}")
    assert dep_inei.idxmax() == dep_pers.idxmax() == "06"   # Cajamarca con los dos métodos

    ENAHO = "INEI, ENAHO 2024 (966-Modulo34 y 966-Modulo02), cálculo independiente en evaluacion/respuestas_esperadas.py"
    filas = [
        ("B1", "bcrp", "¿Cuál fue la inflación interanual (variación del IPC en 12 meses) de Lima Metropolitana en "
         "diciembre de 2024, en %?", ipc_dic24, None, 0.05, None, "%", "PN01273PM, 2024-12",
         WEB.format(codigo="PN01273PM"), ""),
        ("B2", "bcrp", "¿Cuánto creció el PBI real del Perú en 2024 según el BCRP (variación porcentual anual), en %?",
         pbi_2024, None, 0.05, None, "%", "PM04923AA, 2024",
         "https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/resultados/PM04923AA/html", ""),
        ("B3", "bcrp", "¿Cuál fue el tipo de cambio interbancario venta promedio de 2024 (promedio simple de los 12 "
         "promedios mensuales publicados por el BCRP), en soles por dólar?", tc_prom, None, 0.005, None,
         "S/ por US$", "PN01206PM, 2024-01 a 2024-12", WEB.format(codigo="PN01206PM"), ""),
        ("B4", "bcrp", "¿Cuál fue la variación en 12 meses del IPC de Alimentos y Bebidas de Lima Metropolitana en "
         "octubre de 2026, en %?", alim_oct26, None, 0.05, None, "%", "PN09822PM, 2026-10",
         WEB.format(codigo="PN09822PM"), ""),
        ("E1", "enaho", "Según la ENAHO 2024 del INEI, ¿qué porcentaje de la población del Perú estaba en pobreza "
         "monetaria en 2024?", 27.6, None, 0.15, None, "% de personas",
         f"Oficial INEI 27.6 %; independiente: {pob_inei:.2f} % (factor07×mieperho), {pob_pers:.2f} % (residentes)",
         ENAHO, ""),
        ("E2", "enaho", "Según la ENAHO 2024, ¿qué porcentaje de la población del área rural del Perú estaba en "
         "pobreza monetaria en 2024?", 39.3, None, 0.2, None, "% de personas",
         f"Oficial INEI 39.3 %; independiente: {rural_inei:.2f} % (factor07×mieperho), {rural_pers:.2f} % (residentes)",
         ENAHO, ""),
        ("E3", "enaho", "Según la ENAHO 2024, ¿qué departamento del Perú tuvo la mayor tasa de pobreza monetaria en "
         "2024 y cuál fue esa tasa, en %? (Lima y Callao cuentan por separado)", round(dep_inei.max(), 2), None, 0.3,
         None, "% de personas", f"Cajamarca (06): {dep_inei.max():.2f} % (factor07×mieperho), "
         f"{dep_pers.max():.2f} % (residentes)", ENAHO, "Debe nombrar a Cajamarca"),
        ("E4", "enaho", "Según la ENAHO 2024, ¿qué porcentaje de los niños y adolescentes de 0 a 14 años del Perú "
         "vivía en pobreza monetaria en 2024 (residentes habituales)?", round(ninos, 2), None, 0.5, None,
         "% de personas", f"{ninos:.2f} % (residentes habituales, facpob07)", ENAHO, ""),
        ("C1", "combinada", "Con la ENAHO 2024 y el BCRP: ¿cuántos puntos porcentuales superaba la pobreza monetaria "
         "rural a la urbana en 2024, y cuál fue la variación en 12 meses del IPC de Alimentos y Bebidas de Lima "
         "Metropolitana en diciembre de 2024? Interpreta en una frase si ambas cifras se relacionan.",
         round(rural_inei - urb_inei, 2), alim_dic24, 0.3, 0.05, "puntos porcentuales | %",
         f"brecha {rural_inei - urb_inei:.2f} pp (INEI) / {rural_pers - urb_pers:.2f} pp (residentes); PN09822PM "
         "2024-12", f"{ENAHO}; {WEB.format(codigo='PN09822PM')}",
         "Ambas cifras dentro de tolerancia y una interpretación sin afirmar causalidad (niveles de agregación "
         "distintos: IPC de Lima frente a pobreza nacional por área)"),
        ("C2", "combinada", "Con la ENAHO 2024 y el BCRP: ¿qué porcentaje de su gasto destinaban en promedio a alimentos "
         "las personas en pobreza extrema en 2024, y cuál fue el valor máximo de la variación en 12 meses del IPC de "
         "Alimentos y Bebidas de Lima Metropolitana entre enero de 2020 y diciembre de 2024 (y en qué mes)? "
         "Interpreta en una frase qué implica la combinación.", round(alim_ext, 2), pico, 1.0, 0.05,
         "% del gasto | %", f"{alim_ext:.2f} % (residentes, facpob07; gasto en alimentos grupo 1 / gashog2d); "
         f"pico PN09822PM {pico_mes} = {pico:.2f} %", f"{ENAHO}; {WEB.format(codigo='PN09822PM')}",
         f"Ambas cifras dentro de tolerancia, el mes del pico ({pico_mes}) y una interpretación coherente (mayor "
         "exposición del presupuesto de los pobres a los precios de alimentos) sin afirmar causalidad"),
    ]
    cols = ["id", "tipo", "pregunta", "valor_esperado", "valor_esperado_2", "tolerancia", "tolerancia_2", "unidad",
            "respuesta_esperada", "fuente_verificacion", "criterio_adicional"]
    df = pd.DataFrame(filas, columns=cols)
    for c in ("valor_esperado", "valor_esperado_2"):
        df[c] = df[c].astype(float).round(4)
    df.to_csv(AQUI / "preguntas.csv", index=False, encoding="utf-8")
    print(df[["id", "valor_esperado", "valor_esperado_2", "tolerancia", "respuesta_esperada"]].to_string(index=False))


if __name__ == "__main__":
    main()
