"""Estimaciones ponderadas de la ENAHO con su error estándar de diseño (lo usan las tres skills).

proporcion(df, "pobre", peso="facpob07", por="area") devuelve, para cada grupo, el % ponderado, el error estándar
por linealización de Taylor (diseño: conglomerado `conglome` dentro de estrato `estrato`, como en el svyset del INEI),
el intervalo de confianza al 95 %, el n muestral y la población expandida. Nunca un promedio simple.
"""
import numpy as np
import pandas as pd

Z95 = 1.959964


def _varianza_diseno(z, psu, estrato):
    """Varianza con reemplazo de un total linealizado z: sum_h n_h/(n_h-1) * sum_i (z_hi - zbar_h)^2."""
    t = pd.DataFrame({"z": z, "psu": psu, "h": estrato}).groupby(["h", "psu"], observed=True).z.sum().reset_index()
    var = 0.0
    for _, g in t.groupby("h", observed=True):
        n = len(g)
        if n > 1:
            var += n / (n - 1) * ((g.z - g.z.mean()) ** 2).sum()
    return var


def media(df, variable, peso="facpob07", por=None, psu="conglome", estrato="estrato"):
    """Media ponderada de una variable continua (p. ej. gasto_pc_mensual), con EE de diseño. Columnas *_pct en
    las unidades de la variable (escala 1)."""
    return proporcion(df, variable, peso, por, psu, estrato, escala=1.0)


def proporcion(df, variable, peso="facpob07", por=None, psu="conglome", estrato="estrato", escala=100.0):
    """% ponderado de `variable` (0/1) en toda la base o por grupos, con EE de diseño e IC 95 %."""
    df = df[df[variable].notna()]
    if df[peso].isna().any() or (df[peso] <= 0).any():
        raise ValueError(f"El factor {peso} tiene valores nulos o no positivos.")
    y = df[variable].astype(float).to_numpy()
    w = df[peso].astype(float).to_numpy()
    grupos = [("Total", np.ones(len(df), dtype=bool))] if por is None else \
        [(g, (df[por] == g).to_numpy()) for g in sorted(df[por].dropna().unique())]
    filas = []
    for g, d in grupos:
        wd = w * d
        W = wd.sum()
        p = (wd * y).sum() / W
        z = wd * (y - p) / W          # linealización del cociente; cero fuera del dominio
        ee = np.sqrt(_varianza_diseno(z, df[psu].to_numpy(), df[estrato].to_numpy()))
        filas.append({"grupo": g, "valor_pct": escala * p, "ee_pct": escala * ee,
                      "ic95_inf": escala * (p - Z95 * ee), "ic95_sup": escala * (p + Z95 * ee),
                      "n_muestra": int(d.sum()), "poblacion_expandida": W})
    return pd.DataFrame(filas)


def promedio_simple(df, variable, por=None):
    """Solo para mostrar en la validación cuánto se equivoca no ponderar. No usar para reportar."""
    if por is None:
        return 100 * df[variable].mean()
    return 100 * df.groupby(por)[variable].mean()
