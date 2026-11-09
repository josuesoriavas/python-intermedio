"""Verifica, por un camino independiente, cifras del informe final (informes/informe_final.md).

    uv run python scripts/verificar_informe.py      # escribe informes/verificacion_cifras.csv

No importa el servidor MCP (mcp/server.py) ni los scripts de las skills (limpiar.py, estimacion.py, consultar.py):
- BCRP: llamada directa a la API pública con httpx y cálculo con Python puro.
- ENAHO: lectura directa de los .dta del INEI con pandas y tasas ponderadas escritas aquí.
Cada fila compara la cifra del informe (tal como aparece, redondeada) con el valor recalculado.
"""
import io
import zipfile
from pathlib import Path

import httpx
import pandas as pd

PROYECTO = Path(__file__).resolve().parents[1]
DATOS = PROYECTO / "datos" / "inei"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{desde}/{hasta}"


def bcrp(codigo, desde, hasta):
    r = httpx.get(API.format(codigo=codigo, desde=desde, hasta=hasta), timeout=60)
    r.raise_for_status()
    return [(p["name"], float(p["values"][0])) for p in r.json()["periods"] if p["values"][0] not in ("n.d.", "")]


def dta(zipname, interno, columnas):
    with zipfile.ZipFile(DATOS / zipname) as z:
        df = pd.read_stata(io.BytesIO(z.read(interno)), convert_categoricals=False)
    df.columns = [c.lower() for c in df.columns]
    return df[columnas]


def tasa(df, y, w):
    return 100 * (df[w] * df[y]).sum() / df[w].sum()


def main():
    filas = []

    def anotar(fuente, afirmacion, informe, calculado, tolerancia, detalle):
        filas.append({"fuente": fuente, "afirmacion": afirmacion, "valor_informe": informe,
                      "valor_recalculado": round(calculado, 4), "diferencia": round(calculado - informe, 4),
                      "coincide": "sí" if abs(calculado - informe) <= tolerancia else "NO",
                      "tolerancia_redondeo": tolerancia, "procedimiento": detalle})

    # ------------------------------------------------------------------ BCRP
    pbi = dict(bcrp("PM04923AA", "2019", "2024"))
    anotar("BCRP", "PBI real 2024, var. % anual (PM04923AA)", 3.5, pbi["2024"], 0.05, "API directa, año 2024")
    anotar("BCRP", "PBI real 2020, var. % anual (PM04923AA)", -10.9, pbi["2020"], 0.05, "API directa, año 2020")
    alim = bcrp("PN09822PM", "2019-1", "2024-12")
    mes, pico = max(alim, key=lambda x: x[1])
    assert mes == "Feb.2023", mes
    anotar("BCRP", "Máximo IPC Alimentos y Bebidas 2019-2024, var. % 12m (PN09822PM), en feb-2023", 13.2, pico, 0.05,
           f"API directa; máximo de {len(alim)} meses en {mes}")
    prom = {a: sum(v for n, v in alim if n.endswith(str(a))) / 12 for a in (2022, 2024)}
    anotar("BCRP", "Promedio 2022 IPC Alimentos y Bebidas (PN09822PM)", 10.8, prom[2022], 0.05,
           "API directa; promedio simple de los 12 meses de 2022")
    anotar("BCRP", "Caída del promedio 2022→2024 de la inflación de alimentos, pp", -8.8, prom[2024] - prom[2022],
           0.05, "promedio 2024 menos promedio 2022")
    ipc = bcrp("PN01273PM", "2019-1", "2024-12")
    mes_g, pico_g = max(ipc, key=lambda x: x[1])
    assert mes_g == "Jun.2022", mes_g
    anotar("BCRP", "Máximo IPC general 2019-2024, var. % 12m (PN01273PM), en jun-2022", 8.8, pico_g, 0.05,
           f"API directa; máximo en {mes_g}")

    # ------------------------------------------------------------------ ENAHO 2024
    s = dta("966-Modulo34.zip", "966-Modulo34/sumaria-2024.dta",
            ["conglome", "vivienda", "hogar", "ubigeo", "estrato", "dominio", "pobreza", "mieperho", "factor07",
             "gashog2d", "gru11hd", "gru12hd1", "gru12hd2", "gru13hd1", "gru13hd2", "gru13hd3", "sg23", "sig24",
             "gru14hd", "gru14hd1", "gru14hd2", "gru14hd3", "gru14hd4", "gru14hd5", "sg25", "sig26", "sg27", "sig28"])
    m = dta("966-Modulo02.zip", "966-Modulo02/enaho01-2024-200.dta",
            ["conglome", "vivienda", "hogar", "codperso", "p204", "p205", "p206", "facpob07"])
    s["pobre"] = (s.pobreza <= 2).astype(int)
    s["w_inei"] = s.factor07 * s.mieperho
    comida = [c for c in s.columns if c.startswith(("gru1", "sg2", "sig2"))]
    s["alim_pct"] = 100 * s[comida].fillna(0).sum(axis=1) / s.gashog2d
    res = m[((m.p204 == 1) & (m.p205 == 2)) | ((m.p204 == 2) & (m.p206 == 1))]
    p = res.merge(s, on=["conglome", "vivienda", "hogar"], validate="m:1")
    p["rural"] = p.estrato >= 6
    p["dpto"] = p.ubigeo.str[:2]
    p["sierra"] = p.dominio.isin([4, 5, 6])

    anotar("ENAHO", "Pobreza nacional, residentes habituales (facpob07)", 27.5, tasa(p, "pobre", "facpob07"), 0.05,
           f"{len(p):,} residentes; filtro p204/p205/p206; peso facpob07")
    anotar("ENAHO", "Pobreza nacional, método INEI (factor07×mieperho)", 27.6, tasa(s, "pobre", "w_inei"), 0.05,
           f"{len(s):,} hogares de la sumaria; cifra oficial INEI 27.6 %")
    anotar("ENAHO", "Pobreza rural (facpob07)", 39.4, tasa(p[p.rural], "pobre", "facpob07"), 0.05, "estrato 6-8")
    anotar("ENAHO", "Pobreza urbana (facpob07)", 24.7, tasa(p[~p.rural], "pobre", "facpob07"), 0.05, "estrato 1-5")
    anotar("ENAHO", "Pobreza en la Sierra (facpob07)", 31.1, tasa(p[p.sierra], "pobre", "facpob07"), 0.05,
           "dominio 4-6")
    dep = p.groupby("dpto").apply(lambda g: tasa(g, "pobre", "facpob07"), include_groups=False)
    assert dep.idxmax() == "06" and dep.idxmin() == "11", (dep.idxmax(), dep.idxmin())
    anotar("ENAHO", "Departamento con más pobreza: Cajamarca (06)", 45.0, dep["06"], 0.05, "ubigeo[:2] == '06'")
    anotar("ENAHO", "Departamento con menos pobreza: Ica (11)", 5.9, dep["11"], 0.05, "ubigeo[:2] == '11'")
    for cod, nombre, valor in [(1, "pobres extremos", 51.7), (3, "no pobres", 33.6)]:
        g = p[p.pobreza == cod]
        anotar("ENAHO", f"Participación de alimentos en el gasto, {nombre}", valor,
               (g.facpob07 * g.alim_pct).sum() / g.facpob07.sum(), 0.05,
               "18 rubros de alimentos de la sumaria / gashog2d, promedio ponderado con facpob07")

    df = pd.DataFrame(filas)
    df.to_csv(PROYECTO / "informes" / "verificacion_cifras.csv", index=False, encoding="utf-8")
    print(df[["fuente", "afirmacion", "valor_informe", "valor_recalculado", "coincide"]].to_string(index=False))
    print(f"\n{(df.coincide == 'sí').sum()} de {len(df)} cifras coinciden")


if __name__ == "__main__":
    main()
