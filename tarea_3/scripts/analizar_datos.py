"""Paso 3: indicadores, prueba de significancia y exportación de datos para la web.

Compara el desvío de la producción (respecto a su tendencia) en años con El Niño costero
moderado o mayor (ICEN ene-jun > 1.0 °C) contra los años sin Niño (ICEN ene-jun <= 0.4 °C).
La significancia se estima con una prueba de permutación: se baraja 20 000 veces la etiqueta
"año Niño" entre los años del cultivo y se cuenta cuántas veces la diferencia es tan negativa
como la observada (p-valor unilateral).

Salidas:
  datos/procesados/vulnerabilidad_cultivos.csv
  datos/procesados/hallazgos.json
  web/data/datos.json   (todo lo que usa el dashboard, salvo el mapa)
  web/data/mapa.json    (desvío por país, cultivo y año)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "datos" / "procesados"
WEB = RAIZ / "web" / "data"
NINO = "Niño moderado o mayor"
SIN = "Sin Niño"
rng = np.random.default_rng(2026)


def permutacion(desvios: np.ndarray, es_nino: np.ndarray, n: int = 20_000) -> float:
    obs = desvios[es_nino].mean() - desvios[~es_nino].mean()
    k = es_nino.sum()
    difs = np.empty(n)
    for i in range(n):
        idx = rng.permutation(len(desvios))
        difs[i] = desvios[idx[:k]].mean() - desvios[idx[k:]].mean()
    return float((np.sum(difs <= obs) + 1) / (n + 1))


def tabla_vulnerabilidad(p: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for (cod, cultivo, grupo, zona), g in p.groupby(["cod_cultivo", "cultivo", "grupo", "zona"]):
        g = g.dropna(subset=["produccion_desvio"])
        g = g[g["tipo_anio"].isin([NINO, SIN])]
        es_nino = (g["tipo_anio"] == NINO).to_numpy()
        if es_nino.sum() < 3:
            continue
        d = g["produccion_desvio"].to_numpy()
        peor = g.loc[g["produccion_desvio"].idxmin()]
        filas.append({
            "cod_cultivo": cod, "cultivo": cultivo, "grupo": grupo, "zona": zona,
            "anios_nino": int(es_nino.sum()), "anios_sin_nino": int((~es_nino).sum()),
            "desvio_nino": d[es_nino].mean(), "desvio_sin_nino": d[~es_nino].mean(),
            "diferencia": d[es_nino].mean() - d[~es_nino].mean(),
            "p_valor": permutacion(d, es_nino),
            "correlacion_icen": np.corrcoef(g["icen_ene_jun"], d)[0, 1],
            "peor_anio": int(peor["anio"]), "peor_desvio": peor["produccion_desvio"],
        })
    return pd.DataFrame(filas).sort_values("diferencia").round(4)


def main() -> None:
    p = pd.read_csv(PROC / "cultivos_peru.csv")
    anios = pd.read_csv(PROC / "anios_nino.csv")
    icen = pd.read_csv(PROC / "icen_mensual.csv")
    eventos = pd.read_csv(PROC / "eventos_nino.csv")
    oi = pd.read_csv(PROC / "oisst_reciente.csv")
    mundo = pd.read_csv(PROC / "anomalias_mundo.csv")
    p = p.merge(anios[["anio", "icen_ene_jun", "tipo_anio"]], on="anio", how="left")

    vul = tabla_vulnerabilidad(p)
    vul.to_csv(PROC / "vulnerabilidad_cultivos.csv", index=False)
    print(vul[["cultivo", "desvio_nino", "desvio_sin_nino", "diferencia", "p_valor", "peor_anio"]].head(10).to_string())

    def fila(c: str) -> dict:
        return vul.set_index("cultivo").loc[c].to_dict()

    def desvio(c: str, a: int) -> float:
        return float(p[(p["cultivo"] == c) & (p["anio"] == a)]["produccion_desvio"].iloc[0])

    ultimo = oi.iloc[-1]
    ev_actual = eventos.iloc[-1]
    hallazgos = {
        "estado_actual": {
            "mes": ultimo["fecha"], "anomalia_nino12": float(ultimo["n12_anom"]),
            "anomalia_nino34": float(ultimo["n34_anom"]),
            "evento_inicio": ev_actual["inicio"], "icen_max": float(ev_actual["icen_max"]),
            "mes_icen_max": ev_actual["mes_pico"], "magnitud": ev_actual["magnitud"],
        },
        "mas_vulnerables": vul.head(5)[["cultivo", "zona", "desvio_nino", "desvio_sin_nino",
                                        "diferencia", "p_valor"]].to_dict("records"),
        "agroexportacion": vul[vul["cultivo"].isin(["Palta", "Uva", "Espárrago", "Café", "Cacao"])][
            ["cultivo", "desvio_nino", "desvio_sin_nino", "diferencia", "p_valor"]].to_dict("records"),
        "evento_2023": {c: {"2023": desvio(c, 2023), "2024": desvio(c, 2024)}
                        for c in ["Mango", "Limón", "Algodón", "Arroz", "Quinua"]},
        "evento_1983": {c: desvio(c, 1983) for c in ["Algodón", "Limón", "Mango", "Quinua", "Papa"]},
        "anios_nino_moderado": anios[anios["tipo_anio"] == NINO]["anio"].tolist(),
    }
    (PROC / "hallazgos.json").write_text(json.dumps(hallazgos, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- Datos para la web ----------
    WEB.mkdir(parents=True, exist_ok=True)
    r = lambda s, n=4: [None if pd.isna(x) else round(float(x), n) for x in s]
    cultivos = (p[["cod_cultivo", "cultivo", "grupo", "zona"]].drop_duplicates()
                .sort_values("cultivo").to_dict("records"))
    peru = {}
    for c, g in p.sort_values("anio").groupby("cultivo"):
        peru[c] = {
            "anio": g["anio"].tolist(),
            "flag": g["flag_produccion"].fillna("").tolist(),
            **{col: r(g[col], 3 if "desvio" in col else 2)
               for col in ["produccion", "area", "rendimiento", "produccion_tendencia", "area_tendencia",
                           "rendimiento_tendencia", "produccion_desvio", "area_desvio", "rendimiento_desvio"]},
        }
    ic = icen.dropna(subset=["icen"])
    datos = {
        "generado": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "icen": {"fecha": ic["fecha"].tolist(), "icen": r(ic["icen"], 2), "anom": r(ic["n12_anom"], 2)},
        "oisst": {"fecha": oi["fecha"].tail(36).tolist(), "anom": r(oi["n12_anom"].tail(36), 2),
                  "anom34": r(oi["n34_anom"].tail(36), 2)},
        "eventos": eventos.to_dict("records"),
        "anios": anios[["anio", "icen_ene_jun", "icen_max_anio", "categoria", "tipo_anio"]].to_dict("records"),
        "cultivos": cultivos,
        "peru": peru,
        "vulnerabilidad": vul.to_dict("records"),
        "hallazgos": hallazgos,
    }
    (WEB / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    mapa: dict = {"paises": dict(zip(mundo["iso3"], mundo["pais"])), "desvio": {}}
    for (c, a), g in mundo.groupby(["cultivo", "anio"]):
        mapa["desvio"].setdefault(c, {})[int(a)] = dict(zip(g["iso3"], (g["desvio"] * 100).round(1)))
    (WEB / "mapa.json").write_text(json.dumps(mapa, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for f in ["datos.json", "mapa.json"]:
        print(f"web/data/{f}: {(WEB / f).stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
