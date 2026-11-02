"""Gráficos del reel (matplotlib, tema oscuro del video) y música de fondo generada por código.

Lee los mismos archivos procesados que el dashboard. Uso (desde tarea_3/):
    python reel/graficos_reel.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import wave

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "datos" / "procesados"
REC = RAIZ / "reel" / "recursos"
FONDO, TEXTO, SUAVE, ACENTO, FRIO, GRIS = "#1C1A17", "#F7F3EC", "#B8AE9F", "#F08A4B", "#5AA9E6", "#5E574E"

plt.rcParams.update({
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
    "text.color": TEXTO, "axes.labelcolor": SUAVE, "xtick.color": SUAVE, "ytick.color": SUAVE,
    "axes.edgecolor": GRIS, "font.size": 22, "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans",
})
TAM = (9, 6)  # 900 x 600 px a 100 dpi


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(REC / nombre, dpi=100)
    plt.close(fig)
    print("  ", nombre)


def main() -> None:
    REC.mkdir(parents=True, exist_ok=True)
    icen = pd.read_csv(PROC / "icen_mensual.csv").dropna(subset=["icen"])
    icen["f"] = pd.to_datetime(icen["fecha"])
    oi = pd.read_csv(PROC / "oisst_reciente.csv")
    oi["f"] = pd.to_datetime(oi["fecha"])
    p = pd.read_csv(PROC / "cultivos_peru.csv")
    vul = pd.read_csv(PROC / "vulnerabilidad_cultivos.csv")

    # 1. El mar hoy: anomalía mensual Niño 1+2 (OISST), últimos 36 meses
    o = oi.tail(36)
    fig, ax = plt.subplots(figsize=TAM)
    ax.fill_between(o["f"], o["n12_anom"], 0, where=o["n12_anom"] > 0, color=ACENTO, alpha=.85, interpolate=True)
    ax.fill_between(o["f"], o["n12_anom"], 0, where=o["n12_anom"] < 0, color=FRIO, alpha=.8, interpolate=True)
    ax.axhline(0, color=SUAVE, lw=1)
    u = o.iloc[-1]
    ax.annotate(f"{u['n12_anom']:+.1f} °C", (u["f"], u["n12_anom"]), xytext=(-230, -30), textcoords="offset points",
                fontsize=34, fontweight="bold", color=ACENTO, arrowprops=dict(arrowstyle="-", color=ACENTO))
    ax.set_ylabel("Anomalía del mar (°C)")
    ax.set_title("Mar frente al Perú (Niño 1+2), 2023-2026", fontsize=22, color=TEXTO, loc="left")
    fig.autofmt_xdate()
    guardar(fig, "esc1_mar_hoy.png")

    # 2. ICEN 1950-2026 con los grandes eventos
    fig, ax = plt.subplots(figsize=TAM)
    ax.fill_between(icen["f"], icen["icen"], 0, where=icen["icen"] > 0, color=ACENTO, alpha=.85, interpolate=True)
    ax.fill_between(icen["f"], icen["icen"], 0, where=icen["icen"] < 0, color=FRIO, alpha=.7, interpolate=True)
    for fecha, txt in [("1983-06", "1983"), ("1997-11", "1997-98"), ("2023-07", "2023"), ("2026-05", "2026")]:
        v = icen.loc[icen["fecha"] == fecha, "icen"].iloc[0]
        ax.annotate(txt, (pd.Timestamp(fecha), v), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=20, color=TEXTO)
    ax.set_ylabel("ICEN (°C)")
    ax.set_title("Índice Costero El Niño, 1950-2026", fontsize=22, color=TEXTO, loc="left")
    guardar(fig, "esc2_icen.png")

    # 3. Ranking: los 6 cultivos más golpeados en años Niño
    top = vul.head(6).iloc[::-1]
    fig, ax = plt.subplots(figsize=TAM)
    ax.barh(top["cultivo"], top["desvio_nino"] * 100, color=ACENTO)
    for y, v in enumerate(top["desvio_nino"] * 100):
        ax.text(v + 0.6, y, f"{v:.0f} %", va="center", ha="left", fontsize=22, color=FONDO, fontweight="bold")
    ax.axvline(0, color=SUAVE, lw=1)
    ax.set_xlim(-30, 2)
    ax.set_xlabel("Producción vs. tendencia en años Niño (%)")
    ax.set_title("Los cultivos que más pierden", fontsize=22, color=TEXTO, loc="left")
    guardar(fig, "esc3_ranking.png")

    # 4. Mango 2005-2024: dos campañas perdidas
    m = p[(p["cultivo"] == "Mango") & (p["anio"] >= 2005)]
    fig, ax = plt.subplots(figsize=TAM)
    ax.bar(m["anio"], m["produccion"] / 1000, color=[ACENTO if a in (2023, 2024) else GRIS for a in m["anio"]])
    ax.plot(m["anio"], m["produccion_tendencia"] / 1000, color=TEXTO, lw=2.5, label="Tendencia")
    ax.set_ylabel("Miles de toneladas")
    ax.legend(frameon=False, loc="upper left", fontsize=18)
    ax.set_title("Producción de mango en el Perú", fontsize=22, color=TEXTO, loc="left")
    guardar(fig, "esc4_mango.png")

    # 5. Altiplano: quinua y cebada en los años Niño moderados o mayores
    anios = [1983, 1987, 1992, 1998, 2016, 2023]
    fig, ax = plt.subplots(figsize=TAM)
    x = np.arange(len(anios))
    for k, (c, col) in enumerate([("Quinua", ACENTO), ("Cebada", "#E9C46A")]):
        d = p[(p["cultivo"] == c) & p["anio"].isin(anios)].set_index("anio").reindex(anios)["produccion_desvio"] * 100
        ax.bar(x + (k - .5) * .38, d, width=.38, color=col, label=c)
    ax.axhline(0, color=SUAVE, lw=1)
    ax.set_xticks(x, [str(a) for a in anios])
    ax.set_ylabel("Producción vs. tendencia (%)")
    ax.legend(frameon=False, fontsize=18, loc="lower right")
    ax.set_title("Quinua y cebada en años Niño", fontsize=22, color=TEXTO, loc="left")
    guardar(fig, "esc5_sierra.png")

    # 6. Agroexportación vs. los más golpeados
    sel = ["Palta", "Café", "Uva", "Mango", "Quinua", "Algodón"]
    v = vul.set_index("cultivo").loc[sel]
    fig, ax = plt.subplots(figsize=TAM)
    cols = [FRIO if c in ("Palta", "Café", "Uva") else ACENTO for c in sel]
    ax.barh(sel[::-1], (v["desvio_nino"] * 100).iloc[::-1], color=cols[::-1])
    ax.axvline(0, color=SUAVE, lw=1)
    for y, val in enumerate((v["desvio_nino"] * 100).iloc[::-1]):
        ax.text(val + (1 if val >= 0 else -1), y, f"{val:+.0f} %", va="center", ha="left" if val >= 0 else "right", fontsize=20, color=TEXTO)
    ax.set_xlim(-30, 10)
    ax.set_xlabel("Producción vs. tendencia en años Niño (%)")
    ax.set_title("Agroexportación (azul) vs. más golpeados", fontsize=22, color=TEXTO, loc="left")
    guardar(fig, "esc6_agroexport.png")

    musica(REC / "musica_fondo.wav")


def musica(ruta: Path, dur: float = 80.0, sr: int = 44100) -> None:
    """Pista ambiental suave (acordes La m - Fa - Do - Sol) sintetizada con numpy: sin derechos de terceros."""
    t = np.arange(int(dur * sr)) / sr
    acordes = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
    seg = 4.0
    y = np.zeros_like(t)
    for i in range(int(dur / seg) + 1):
        ini = i * seg
        m = (t >= ini) & (t < ini + seg + 1.0)
        tt = t[m] - ini
        env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - seg) * 3)
        for f in acordes[i % 4]:
            y[m] += env * (np.sin(2 * np.pi * f * tt) + .3 * np.sin(2 * np.pi * 2 * f * tt)) / 3
        # pulso grave suave en cada tiempo
        bajo = acordes[i % 4][0] / 2
        for b in range(4):
            mb = (tt >= b) & (tt < b + .9)
            y[np.where(m)[0][mb]] += .35 * np.exp(-(tt[mb] - b) * 4) * np.sin(2 * np.pi * bajo * (tt[mb] - b))
    y *= np.minimum(1, t / 2) * np.minimum(1, (dur - t) / 3)
    y = (y / np.abs(y).max() * .6 * 32767).astype(np.int16)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())
    print("  ", ruta.name)


if __name__ == "__main__":
    main()
