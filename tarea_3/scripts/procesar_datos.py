"""Paso 2: limpia las fuentes y construye los indicadores.

Salidas en datos/procesados/:
  icen_mensual.csv       ICEN reconstruido (Niño 1+2, ERSSTv5) y su categoría ENFEN, 1950-hoy
  eventos_nino.csv       Eventos El Niño costero: >= 3 meses seguidos con ICEN > 0.4 °C
  anios_nino.csv         Intensidad por año: ICEN promedio de enero a junio y su categoría
  oisst_reciente.csv     Anomalía mensual Niño 1+2 (OISST), para el estado más reciente
  cultivos_peru.csv      Producción, área y rendimiento de 27 cultivos del Perú, 1961-2024,
                         con su desvío respecto a la tendencia
  anomalias_mundo.csv    Desvío de la producción por país, cultivo y año (para el mapa)

Indicador central (desvío respecto a la tendencia):
    desvío(t) = valor(t) / mediana(valores de t-3..t-1 y t+1..t+3) - 1
La mediana de los 3 años anteriores y 3 posteriores (sin el propio año) aísla el golpe de un año
malo sin confundirlo con el crecimiento de largo plazo (p. ej., el boom del arándano).
Se exige al menos 3 vecinos con dato.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry

RAIZ = Path(__file__).resolve().parents[1]
ORIG = RAIZ / "datos" / "originales"
PROC = RAIZ / "datos" / "procesados"

# Umbrales del ICEN según ENFEN (Nota Técnica 01-2012), en °C
CATEGORIAS = [
    (-np.inf, -1.4, "Fría fuerte"),
    (-1.4, -1.2, "Fría moderada"),
    (-1.2, -1.0, "Fría débil"),
    (-1.0, 0.4, "Neutra"),
    (0.4, 1.0, "Cálida débil"),
    (1.0, 1.7, "Cálida moderada"),
    (1.7, 3.0, "Cálida fuerte"),
    (3.0, np.inf, "Cálida extraordinaria"),
]

# Cultivos analizados: código FAOSTAT -> (nombre, grupo, zona principal de producción)
CULTIVOS = {
    571: ("Mango", "Agroexportación", "Costa norte"),
    497: ("Limón", "Consumo interno", "Costa norte"),
    27: ("Arroz", "Consumo interno", "Costa norte y selva"),
    328: ("Algodón", "Industrial", "Costa"),
    486: ("Plátano y banano", "Consumo interno", "Selva y costa norte"),
    156: ("Caña de azúcar", "Industrial", "Costa norte"),
    56: ("Maíz grano", "Consumo interno", "Costa, sierra y selva"),
    446: ("Choclo", "Consumo interno", "Sierra y costa"),
    116: ("Papa", "Consumo interno", "Sierra"),
    92: ("Quinua", "Consumo interno", "Sierra sur"),
    44: ("Cebada", "Consumo interno", "Sierra"),
    15: ("Trigo", "Consumo interno", "Sierra"),
    125: ("Yuca", "Consumo interno", "Selva"),
    122: ("Camote", "Consumo interno", "Costa"),
    176: ("Frijol", "Consumo interno", "Costa, sierra y selva"),
    403: ("Cebolla", "Consumo interno", "Costa sur"),
    388: ("Tomate", "Consumo interno", "Costa"),
    490: ("Naranja", "Consumo interno", "Selva central y costa"),
    495: ("Mandarina", "Agroexportación", "Costa central"),
    574: ("Piña", "Consumo interno", "Selva central"),
    560: ("Uva", "Agroexportación", "Costa"),
    572: ("Palta", "Agroexportación", "Costa y sierra"),
    367: ("Espárrago", "Agroexportación", "Costa"),
    552: ("Arándano", "Agroexportación", "Costa norte"),
    656: ("Café", "Agroexportación", "Selva"),
    661: ("Cacao", "Agroexportación", "Selva"),
    689: ("Ají y páprika secos", "Agroexportación", "Costa"),
}

ELEMENTOS = {"Production": "produccion", "Area harvested": "area", "Yield": "rendimiento"}


def categoria(x: float) -> str | None:
    if pd.isna(x):
        return None
    for lo, hi, nombre in CATEGORIAS:
        if lo < x <= hi:
            return nombre
    return None


def leer_indices_cpc(path: Path) -> pd.DataFrame:
    """Lee los archivos de texto de NOAA CPC (columnas: año, mes y 4 regiones con su anomalía)."""
    cols = ["anio", "mes", "n12", "n12_anom", "n3", "n3_anom", "n4", "n4_anom", "n34", "n34_anom"]
    df = pd.read_csv(path, sep=r"\s+", skiprows=1, names=cols)
    df["fecha"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))
    return df


def construir_icen() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    e = leer_indices_cpc(ORIG / "ersst5.nino.mth.91-20.ascii")
    # ICEN = media móvil centrada de 3 meses de la anomalía Niño 1+2 (definición ENFEN)
    e["icen"] = e["n12_anom"].rolling(3, center=True).mean().round(2)
    e["categoria"] = e["icen"].map(categoria)
    e["calida"] = e["icen"] > 0.4

    # Eventos El Niño costero: al menos 3 meses consecutivos en condición cálida
    bloque = (e["calida"] != e["calida"].shift()).cumsum()
    eventos = []
    for _, b in e[e["calida"]].groupby(bloque[e["calida"]]):
        if len(b) < 3:
            continue
        pico = b.loc[b["icen"].idxmax()]
        eventos.append({
            "inicio": b["fecha"].iloc[0].strftime("%Y-%m"),
            "fin": b["fecha"].iloc[-1].strftime("%Y-%m"),
            "meses": len(b),
            "icen_max": pico["icen"],
            "mes_pico": pico["fecha"].strftime("%Y-%m"),
            "magnitud": categoria(pico["icen"]).replace("Cálida ", ""),
        })
    eventos = pd.DataFrame(eventos)
    e["en_evento"] = False
    for _, ev in eventos.iterrows():
        e.loc[(e["fecha"] >= ev["inicio"]) & (e["fecha"] <= ev["fin"] + "-28"), "en_evento"] = True

    # Intensidad anual: ICEN promedio de enero a junio (lluvias en la costa norte y grueso de cosechas)
    sem = e[e["mes"] <= 6].groupby("anio").agg(icen_ene_jun=("icen", "mean"), meses=("icen", "count"))
    sem = sem[sem["meses"] == 6].drop(columns="meses").round(2)
    sem["icen_max_anio"] = e.groupby("anio")["icen"].max().round(2)
    sem["categoria"] = sem["icen_ene_jun"].map(categoria)
    sem["tipo_anio"] = np.select(
        [sem["icen_ene_jun"] > 1.0, sem["icen_ene_jun"] > 0.4],
        ["Niño moderado o mayor", "Niño débil"],
        "Sin Niño",
    )
    sem = sem.reset_index()

    icen = e[["fecha", "anio", "mes", "n12", "n12_anom", "icen", "categoria", "en_evento"]].copy()
    icen["fecha"] = icen["fecha"].dt.strftime("%Y-%m")
    return icen, eventos, sem


def desvio_tendencia(ancho: pd.DataFrame, k: int = 3, min_vecinos: int = 3) -> pd.DataFrame:
    """Desvío de cada año respecto a la mediana de sus k vecinos a cada lado (sin el propio año).

    `ancho` tiene una serie por fila y un año por columna (consecutivos)."""
    v = ancho.to_numpy(dtype=float)
    v = np.where(v > 0, v, np.nan)
    n_filas, n_anios = v.shape
    vecinos = np.full((n_filas, n_anios, 2 * k), np.nan)
    j = 0
    for d in [*range(-k, 0), *range(1, k + 1)]:
        desplazado = np.full_like(v, np.nan)
        if d < 0:
            desplazado[:, -d:] = v[:, :d]
        else:
            desplazado[:, :-d] = v[:, d:]
        vecinos[:, :, j] = desplazado
        j += 1
    validos = np.sum(~np.isnan(vecinos), axis=2)
    with np.errstate(all="ignore"):
        tendencia = np.nanmedian(vecinos, axis=2)
    tendencia[validos < min_vecinos] = np.nan
    desvio = v / tendencia - 1
    return pd.DataFrame(desvio, index=ancho.index, columns=ancho.columns), \
        pd.DataFrame(tendencia, index=ancho.index, columns=ancho.columns)


def iso3(m49: str) -> str | None:
    """'604 -> PER. Los agregados regionales (Mundo, América...) no tienen ISO-3 y se descartan."""
    try:
        c = pycountry.countries.get(numeric=str(m49).strip("'").zfill(3))
    except (KeyError, LookupError):
        return None
    return c.alpha_3 if c else None


def procesar_faostat() -> tuple[pd.DataFrame, pd.DataFrame]:
    zpath = ORIG / "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
    with zipfile.ZipFile(zpath) as z:
        nombre = next(n for n in z.namelist() if n.endswith("(Normalized).csv"))
        df = pd.read_csv(
            z.open(nombre), encoding="latin-1",
            usecols=["Area Code (M49)", "Area", "Item Code", "Element", "Year", "Unit", "Value", "Flag"],
            dtype={"Area Code (M49)": str},
        )
    df = df[df["Item Code"].isin(CULTIVOS) & df["Element"].isin(ELEMENTOS)]
    df = df.rename(columns={"Area Code (M49)": "m49", "Area": "pais", "Item Code": "cod_cultivo",
                            "Element": "elemento", "Year": "anio", "Unit": "unidad",
                            "Value": "valor", "Flag": "flag"})
    df["elemento"] = df["elemento"].map(ELEMENTOS)
    # Limpieza: sin dato (flag M), valores no positivos y duplicados exactos
    antes = len(df)
    df = df[(df["flag"] != "M") & (df["valor"] > 0)].drop_duplicates(["m49", "cod_cultivo", "elemento", "anio"])
    print(f"FAOSTAT: {antes:,} filas de los cultivos elegidos -> {len(df):,} tras limpiar")

    # Rendimiento en t/ha (FAOSTAT lo publica en kg/ha)
    rend = df["elemento"] == "rendimiento"
    if (df.loc[rend, "unidad"] == "kg/ha").all():
        df.loc[rend, "valor"] = df.loc[rend, "valor"] / 1000
        df.loc[rend, "unidad"] = "t/ha"

    anios = list(range(int(df["anio"].min()), int(df["anio"].max()) + 1))
    ancho = df.pivot_table(index=["m49", "pais", "cod_cultivo", "elemento"], columns="anio",
                           values="valor", aggfunc="first").reindex(columns=anios)
    desvio, tendencia = desvio_tendencia(ancho)

    largo = (ancho.stack(future_stack=True).rename("valor").to_frame()
             .join(tendencia.stack(future_stack=True).rename("tendencia"))
             .join(desvio.stack(future_stack=True).rename("desvio"))
             .reset_index().dropna(subset=["valor"]))
    largo = largo.merge(df[["m49", "cod_cultivo", "elemento", "anio", "flag"]],
                        on=["m49", "cod_cultivo", "elemento", "anio"], how="left")
    largo["cultivo"] = largo["cod_cultivo"].map(lambda c: CULTIVOS[c][0])

    # --- Perú: formato ancho por elemento ---
    pe = largo[largo["pais"] == "Peru"]
    peru = pe.pivot_table(index=["cod_cultivo", "cultivo", "anio"], columns="elemento",
                          values=["valor", "tendencia", "desvio"], aggfunc="first")
    peru.columns = [f"{el}" if v == "valor" else f"{el}_{v}" for v, el in peru.columns]
    flags = pe[pe["elemento"] == "produccion"].set_index(["cod_cultivo", "cultivo", "anio"])["flag"]
    peru = peru.join(flags.rename("flag_produccion")).reset_index()
    peru["grupo"] = peru["cod_cultivo"].map(lambda c: CULTIVOS[c][1])
    peru["zona"] = peru["cod_cultivo"].map(lambda c: CULTIVOS[c][2])

    # --- Mundo: desvío de la producción por país (para el mapa) ---
    mundo = largo[(largo["elemento"] == "produccion") & largo["desvio"].notna()].copy()
    mundo["iso3"] = mundo["m49"].map(iso3)
    mundo = mundo.dropna(subset=["iso3"])
    mundo = mundo[mundo["tendencia"] >= 500]  # productores muy pequeños: demasiado ruido
    mundo = mundo[["iso3", "pais", "cod_cultivo", "cultivo", "anio", "valor", "tendencia", "desvio"]]
    return peru, mundo


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    icen, eventos, anios = construir_icen()
    icen.to_csv(PROC / "icen_mensual.csv", index=False)
    eventos.to_csv(PROC / "eventos_nino.csv", index=False)
    anios.to_csv(PROC / "anios_nino.csv", index=False)
    print(f"ICEN: {icen['fecha'].iloc[0]} a {icen.dropna(subset=['icen'])['fecha'].iloc[-1]}, "
          f"{len(eventos)} eventos El Niño costero")

    oi = leer_indices_cpc(ORIG / "sstoi.indices")
    oi["fecha"] = oi["fecha"].dt.strftime("%Y-%m")
    oi[["fecha", "n12", "n12_anom", "n34_anom"]].to_csv(PROC / "oisst_reciente.csv", index=False)
    print(f"OISST: último mes {oi['fecha'].iloc[-1]}, anomalía Niño 1+2 = {oi['n12_anom'].iloc[-1]:+.2f} °C")

    peru, mundo = procesar_faostat()
    peru.round(4).to_csv(PROC / "cultivos_peru.csv", index=False)
    mundo.round(4).to_csv(PROC / "anomalias_mundo.csv", index=False)
    print(f"Perú: {peru['cultivo'].nunique()} cultivos, {peru['anio'].min()}-{peru['anio'].max()}, {len(peru):,} filas")
    print(f"Mundo: {mundo['iso3'].nunique()} países, {len(mundo):,} filas")


if __name__ == "__main__":
    main()
