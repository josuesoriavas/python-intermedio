"""Dashboard de la Tarea 2: documentos y voces peruanas convertidos en texto buscable.

    streamlit run app.py

Solo lee los CSV y JSON que generan los notebooks (no corre OCR, ASR ni LLM): es liviano y
funciona en Streamlit Community Cloud.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).resolve().parent
DATOS = BASE / "datos"
COLORES_TIPO = {"impreso": "#2a6f97", "foto": "#e9a03b", "manuscrito": "#a23b72"}
COLORES_HABLANTE = ["#2a6f97", "#c0392b", "#27ae60", "#8e44ad", "#d35400", "#16a085"]

st.set_page_config(page_title="Voces y documentos peruanos", page_icon="🎙️", layout="wide")


@st.cache_data
def cargar():
    docs = pd.read_csv(DATOS / "documentos.csv", keep_default_na=False)
    clips = pd.read_csv(DATOS / "transcripciones.csv", keep_default_na=False)
    llm = pd.read_csv(DATOS / "extraccion_llm.csv", keep_default_na=False) if (DATOS / "extraccion_llm.csv").exists() else pd.DataFrame(columns=["id", "campos_json", "modelo_llm"])
    ev_ocr = pd.read_csv(DATOS / "evaluacion_ocr.csv", keep_default_na=False) if (DATOS / "evaluacion_ocr.csv").exists() else pd.DataFrame()
    ev_asr = pd.read_csv(DATOS / "evaluacion_asr.csv", keep_default_na=False) if (DATOS / "evaluacion_asr.csv").exists() else pd.DataFrame()
    fuentes = pd.read_csv(DATOS / "fuentes.csv", keep_default_na=False)
    met = json.loads((DATOS / "metricas.json").read_text(encoding="utf-8")) if (DATOS / "metricas.json").exists() else {}
    for df in (docs, clips):
        df["texto_referencia"] = df["texto_referencia"].fillna("")
    clips["duracion_min"] = clips["duracion_seg"].astype(float) / 60
    return docs, clips, llm, ev_ocr, ev_asr, fuentes, met


docs, clips, llm, ev_ocr, ev_asr, fuentes, met = cargar()
campos_llm = {r.id: json.loads(r.campos_json) for r in llm.itertuples()} if len(llm) else {}


def resaltar(texto: str, termino: str) -> str:
    t = html.escape(texto or "")
    if termino:
        t = re.sub(f"({re.escape(html.escape(termino))})", r"<mark>\1</mark>", t, flags=re.I)
    return t.replace("\n", "<br>")


def con_hablantes(texto: str, termino: str = "") -> str:
    """Pinta cada turno [HABLANTE_n] de un color distinto."""
    partes = re.split(r"(\[HABLANTE_\d+\])", texto or "")
    if len(partes) == 1:
        return f"<p>{resaltar(texto, termino)}</p>"
    salida, color = [], "#444"
    for p in partes:
        m = re.match(r"\[HABLANTE_(\d+)\]", p)
        if m:
            color = COLORES_HABLANTE[(int(m.group(1)) - 1) % len(COLORES_HABLANTE)]
            salida.append(f"<br><b style='color:{color}'>Hablante {m.group(1)}:</b> ")
        elif p.strip():
            salida.append(f"<span style='color:{color}'>{resaltar(p.strip(), termino)}</span>")
    return "<p>" + "".join(salida).removeprefix("<br>") + "</p>"


def fragmento(texto: str, termino: str, ancho: int = 90) -> str:
    i = texto.lower().find(termino.lower())
    if i < 0:
        return ""
    a, b = max(0, i - ancho), min(len(texto), i + len(termino) + ancho)
    return ("…" if a else "") + texto[a:b] + ("…" if b < len(texto) else "")


# ───────────────────────────────────────────────────────── encabezado
st.title("🎙️ ¿Pueden convertirse documentos escaneados y entrevistas en audio en un archivo de texto estructurado y buscable?")
st.markdown(
    "**Tarea 2 · Voces y documentos peruanos.** Se leyeron con **PaddleOCR** 25 documentos peruanos "
    "(páginas impresas de Palma y Garcilaso, fotos de placas de Lima y manuscritos de Guaman Poma y del Acta de la Independencia) "
    "y se transcribieron con **faster-whisper large-v3-turbo + VAD** más de 30 minutos de español peruano "
    "(entrevistas reales de Wikimedia Commons y lecturas de OpenSLR 73), con diarización de hablantes y seudonimización. "
    "Un LLM local (**Ollama qwen2.5:3b**) extrajo campos estructurados y una auditoría humana revisó 20 extracciones. "
    "Los modelos se compararon con CER/WER sobre 10 documentos y 10 clips con transcripción hecha por personas. "
    "Todo se calculó en los notebooks: esta app solo explora los resultados."
)

# ───────────────────────────────────────────────────────── filtros
with st.sidebar:
    st.header("🔎 Filtros")
    termino = st.text_input("Buscar en los textos OCR y ASR", placeholder="p. ej. Lima, Perú, virrey…").strip()
    tipos = st.multiselect("Tipo de documento", ["impreso", "foto", "manuscrito"], default=["impreso", "foto", "manuscrito"])
    origenes = sorted(clips["origen"].unique())
    orig_sel = st.multiselect("Fuente del audio", origenes, default=origenes)
    dmin, dmax = float(clips["duracion_seg"].min()), float(clips["duracion_seg"].max())
    rango = st.slider("Duración del clip (s)", 0.0, float(round(dmax + 5)), (0.0, float(round(dmax + 5))), step=5.0)
    st.divider()
    mods_ocr = {k: v["nombre"] for k, v in met.get("ocr", {}).items()}
    mods_asr = {k: v["nombre"] for k, v in met.get("asr", {}).items()}
    mod_ocr = st.selectbox("Modelo OCR (evaluación)", list(mods_ocr), format_func=mods_ocr.get,
                           index=list(mods_ocr).index(met["elegidos"]["ocr"]) if mods_ocr else 0) if mods_ocr else None
    mod_asr = st.selectbox("Modelo ASR (evaluación)", list(mods_asr), format_func=mods_asr.get,
                           index=list(mods_asr).index(met["elegidos"]["asr"]) if mods_asr else 0) if mods_asr else None
    st.caption("Los filtros actualizan los indicadores de corpus, los gráficos y las tablas. "
               "El selector de modelo cambia las métricas, gráficos y textos de la evaluación.")

d_f = docs[docs["tipo"].isin(tipos)]
c_f = clips[clips["origen"].isin(orig_sel) & clips["duracion_seg"].astype(float).between(*rango)]
if termino:
    d_f = d_f[d_f["texto_ocr"].str.contains(termino, case=False, regex=False)]
    c_f = c_f[c_f["texto_asr"].str.contains(termino, case=False, regex=False)]

# ───────────────────────────────────────────────────────── indicadores
k = st.columns(5)
k[0].metric("Documentos procesados", f"{len(d_f)} / {len(docs)}", help="Documentos que pasan los filtros / total del corpus")
k[1].metric("Minutos de audio transcritos", f"{c_f['duracion_min'].sum():.1f}", help=f"{len(c_f)} de {len(clips)} clips; total {clips['duracion_min'].sum():.1f} min")
if met:
    base_o, base_a = met["ocr"]["paddle_base"]["cer"], met["asr"]["fw-small"]["wer"]
    k[2].metric(f"CER · {mods_ocr[mod_ocr]}", f"{met['ocr'][mod_ocr]['cer']:.3f}",
                delta=None if mod_ocr == "paddle_base" else f"{met['ocr'][mod_ocr]['cer'] - base_o:+.3f} vs. base", delta_color="inverse",
                help="Character Error Rate sobre los mismos 10 documentos con referencia humana (menor es mejor)")
    k[3].metric(f"WER · {mods_asr[mod_asr]}", f"{met['asr'][mod_asr]['wer']:.3f}",
                delta=None if mod_asr == "fw-small" else f"{met['asr'][mod_asr]['wer'] - base_a:+.3f} vs. base", delta_color="inverse",
                help="Word Error Rate sobre los mismos 10 clips con referencia humana (menor es mejor)")
    a = met["auditoria"]
    k[4].metric("Acuerdo LLM vs. auditoría humana", f"{a['correctas'] / a['total']:.0%}", help=f"{a['correctas']}/{a['total']} extracciones completamente correctas")

tab_res, tab_doc, tab_aud, tab_bus, tab_fue = st.tabs(["📊 Resultados", "📄 Documentos", "🎧 Audios", "🔍 Búsqueda", "📚 Fuentes y método"])

# ───────────────────────────────────────────────────────── resultados
with tab_res:
    c1, c2 = st.columns(2)
    por_tipo = d_f.groupby("tipo").agg(documentos=("id", "size"), caracteres=("n_caracteres", "mean")).reset_index()
    fig = px.bar(por_tipo, x="tipo", y="documentos", color="tipo", color_discrete_map=COLORES_TIPO, text="documentos",
                 hover_data={"caracteres": ":.0f"}, title="Documentos por tipo (caracteres OCR medios en el tooltip)",
                 category_orders={"tipo": ["impreso", "foto", "manuscrito"]})
    fig.update_layout(showlegend=False, xaxis_title="", height=380)
    c1.plotly_chart(fig, width="stretch")
    fig = px.bar(c_f.sort_values("duracion_seg", ascending=False), x="id", y="duracion_seg", color="origen",
                 hover_data=["descripcion", "n_hablantes"], title="Duración por clip",
                 color_discrete_sequence=["#e07a5f", "#3d405b"])
    fig.update_layout(xaxis_title="", yaxis_title="segundos", height=380, legend_title="")
    c2.plotly_chart(fig, width="stretch")

    if met and len(ev_ocr):
        st.subheader("Errores por modalidad y modelo (mismas muestras de 10 documentos y 10 clips)")
        c1, c2 = st.columns(2)
        g = pd.DataFrame([{"modelo": v["nombre"], "tipo": t, "CER": x} for v in met["ocr"].values() for t, x in v["cer_por_tipo"].items()])
        g = g[g["tipo"].isin(tipos)]
        fig = px.bar(g, x="tipo", y="CER", color="modelo", barmode="group", text_auto=".2f", title="CER por tipo de documento",
                     color_discrete_sequence=["#2a6f97", "#61a5c2", "#e9a03b"])
        fig.update_layout(xaxis_title="", height=400, legend_title="", legend=dict(orientation="h", y=-0.15))
        c1.plotly_chart(fig, width="stretch")
        g = pd.DataFrame([{"modelo": v["nombre"], "condición": c, "WER": x} for v in met["asr"].values() for c, x in v["wer_por_condicion"].items()])
        fig = px.bar(g, x="condición", y="WER", color="modelo", barmode="group", text_auto=".2f", title="WER por condición de grabación",
                     color_discrete_sequence=["#3d405b", "#81b29a", "#e07a5f"])
        fig.update_layout(xaxis_title="", height=400, legend_title="", legend=dict(orientation="h", y=-0.15))
        c2.plotly_chart(fig, width="stretch")
        tabla = pd.DataFrame([{"modalidad": "documentos", "modelo": v["nombre"], "error": round(v["cer"], 3), "métrica": "CER",
                               "latencia": f"{v['seg_por_doc']:.1f} s/doc", "elegido": "✅" if kk == met["elegidos"]["ocr"] else ""} for kk, v in met["ocr"].items()]
                             + [{"modalidad": "audio", "modelo": v["nombre"], "error": round(v["wer"], 3), "métrica": "WER",
                                 "latencia": f"RTF {v['rtf']:.2f}", "elegido": "✅" if kk == met["elegidos"]["asr"] else ""} for kk, v in met["asr"].items()])
        st.dataframe(tabla, hide_index=True, width="stretch")
        st.caption("RTF = segundos de cómputo / segundos de audio (CPU, sin GPU). Detalles y justificación en `02_evaluacion.ipynb`.")

# ───────────────────────────────────────────────────────── documentos
with tab_doc:
    st.subheader(f"Tabla de documentos ({len(d_f)})")
    cols = ["id", "tipo", "descripcion", "fuente", "n_caracteres", "confianza_ocr", "modelo_ocr", "texto_ocr", "texto_referencia"]
    st.dataframe(d_f[cols], hide_index=True, width="stretch", height=260)
    st.download_button("⬇️ Descargar CSV (textos seudonimizados)", d_f[cols].to_csv(index=False).encode("utf-8"),
                       "documentos_filtrados.csv", "text/csv")
    st.divider()
    st.subheader("Explorador de documentos")
    if len(d_f) == 0:
        st.info("Ningún documento cumple los filtros.")
    else:
        sel = st.selectbox("Documento", d_f["id"], format_func=lambda i: f"{i} · {docs.set_index('id').loc[i, 'tipo']} · {docs.set_index('id').loc[i, 'descripcion']}")
        r = docs.set_index("id").loc[sel]
        c1, c2 = st.columns([2, 3])
        with c1:
            if r["imagen_ejemplo"] and (BASE / r["imagen_ejemplo"]).exists():
                st.image(str(BASE / r["imagen_ejemplo"]), caption=f"{r['fuente']}", width="stretch")
            else:
                st.info("La imagen no se publica porque muestra nombres de personas que se seudonimizaron en el texto. "
                        "El texto y los metadatos siguen disponibles.")
            st.markdown(f"[Ficha de la fuente]({r['fuente_url']}) · licencia **{r['licencia']}**")
            st.caption(f"OCR: {r['n_lineas_ocr']} líneas · confianza media {float(r['confianza_ocr']):.2f} · {float(r['segundos_ocr']):.1f} s")
        with c2:
            st.markdown("**Texto OCR** (" + r["modelo_ocr"] + ")")
            st.markdown(f"<div style='max-height:300px;overflow-y:auto;border:1px solid #ddd;padding:8px;border-radius:6px'>{resaltar(r['texto_ocr'], termino)}</div>", unsafe_allow_html=True)
            st.markdown("**Campos extraídos por el LLM**")
            st.json(campos_llm.get(sel, {}), expanded=True)
        if r["texto_referencia"]:
            st.markdown("**Referencia humana y comparación de modelos** (documento de la muestra de evaluación)")
            e = ev_ocr[ev_ocr["id"] == sel]
            mc = st.columns(len(e) or 1)
            for col, f in zip(mc, e.itertuples()):
                col.metric(mods_ocr.get(f.modelo, f.modelo), f"CER {float(f.cer):.3f}")
            c3, c4 = st.columns(2)
            c3.markdown("*Referencia (transcripción humana)*")
            c3.markdown(f"<div style='max-height:220px;overflow-y:auto;background:#f6f8fa;padding:8px;border-radius:6px'>{resaltar(r['texto_referencia'], termino)}</div>", unsafe_allow_html=True)
            if mod_ocr is not None and len(e):
                h = e[e["modelo"] == mod_ocr]["hipotesis"].iloc[0]
                c4.markdown(f"*Salida de {mods_ocr[mod_ocr]}*")
                c4.markdown(f"<div style='max-height:220px;overflow-y:auto;background:#fff8e6;padding:8px;border-radius:6px'>{resaltar(h, termino)}</div>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────── audios
with tab_aud:
    st.subheader(f"Tabla de clips ({len(c_f)})")
    cols = ["id", "origen", "descripcion", "duracion_seg", "n_hablantes", "modelo_asr", "texto_asr", "texto_referencia", "licencia"]
    st.dataframe(c_f[cols], hide_index=True, width="stretch", height=260)
    st.download_button("⬇️ Descargar CSV (transcripciones seudonimizadas)", c_f[cols].to_csv(index=False).encode("utf-8"),
                       "transcripciones_filtradas.csv", "text/csv")
    st.divider()
    st.subheader("Explorador de audios")
    if len(c_f) == 0:
        st.info("Ningún clip cumple los filtros.")
    else:
        sel = st.selectbox("Clip", c_f["id"], format_func=lambda i: f"{i} · {clips.set_index('id').loc[i, 'descripcion']}")
        r = clips.set_index("id").loc[sel]
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown(f"**{r['descripcion']}**")
            st.caption(f"{float(r['duracion_seg']):.0f} s · {r['n_hablantes']} hablante(s) detectado(s) · {r['licencia']}")
            if r["audio_ejemplo"] and (BASE / r["audio_ejemplo"]).exists():
                st.audio(str(BASE / r["audio_ejemplo"]))
                st.caption("Lectura de un voluntario anónimo de OpenSLR 73 (CC BY-SA 4.0).")
            else:
                st.info("El audio no se reproduce aquí: es una entrevista real en la que se dicen nombres de personas, "
                        "que no se pueden seudonimizar en la voz. Se consulta la transcripción seudonimizada; el original está en la ficha de la fuente.")
            st.markdown(f"[Ficha de la fuente]({r['fuente_url']})")
            st.markdown("**Campos extraídos por el LLM**")
            st.json(campos_llm.get(sel, {}), expanded=True)
        with c2:
            st.markdown(f"**Transcripción ASR** ({r['modelo_asr']})")
            st.markdown(f"<div style='max-height:380px;overflow-y:auto;border:1px solid #ddd;padding:8px;border-radius:6px'>{con_hablantes(r['texto_asr'], termino)}</div>", unsafe_allow_html=True)
        if r["texto_referencia"]:
            st.markdown("**Referencia humana y comparación de modelos** (clip de la muestra de evaluación)")
            e = ev_asr[ev_asr["id"] == sel]
            mc = st.columns(len(e) or 1)
            for col, f in zip(mc, e.itertuples()):
                col.metric(mods_asr.get(f.modelo, f.modelo), f"WER {float(f.wer):.3f}", help=f"RTF {float(f.rtf):.2f}")
            c3, c4 = st.columns(2)
            c3.markdown("*Referencia (transcripción humana)*")
            c3.markdown(f"<div style='max-height:220px;overflow-y:auto;background:#f6f8fa;padding:8px;border-radius:6px'>{resaltar(r['texto_referencia'], termino)}</div>", unsafe_allow_html=True)
            if mod_asr is not None and len(e):
                h = e[e["modelo"] == mod_asr]["hipotesis"].iloc[0]
                c4.markdown(f"*Salida de {mods_asr[mod_asr]}*")
                c4.markdown(f"<div style='max-height:220px;overflow-y:auto;background:#fff8e6;padding:8px;border-radius:6px'>{resaltar(h, termino)}</div>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────── búsqueda
with tab_bus:
    if not termino:
        st.info("Escribe una palabra en el buscador de la barra lateral para encontrarla en todos los documentos y audios.")
    else:
        res = [{"id": r.id, "modalidad": "documento", "detalle": r.tipo, "apariciones": r.texto_ocr.lower().count(termino.lower()),
                "fragmento": fragmento(r.texto_ocr, termino)} for r in d_f.itertuples()] + \
              [{"id": r.id, "modalidad": "audio", "detalle": r.origen, "apariciones": r.texto_asr.lower().count(termino.lower()),
                "fragmento": fragmento(re.sub(r"\[HABLANTE_\d+\] ?", "", r.texto_asr), termino)} for r in c_f.itertuples()]
        res = pd.DataFrame(res, columns=["id", "modalidad", "detalle", "apariciones", "fragmento"]).sort_values("apariciones", ascending=False)
        st.markdown(f"**{len(res)}** registros contienen «{termino}» ({res['apariciones'].sum()} apariciones).")
        for r in res.itertuples():
            st.markdown(f"**{r.id}** · {r.modalidad} · {r.detalle} · {r.apariciones}×<br><span style='color:#555'>{resaltar(r.fragmento, termino)}</span>",
                        unsafe_allow_html=True)

# ───────────────────────────────────────────────────────── fuentes
with tab_fue:
    st.markdown("""
**Corpus.** 25 documentos (8 impresos de Wikisource, 8 fotos de Wikimedia Commons, 9 manuscritos de Commons) y 23 clips de audio
(8 entrevistas reales de Commons grabadas en Lima en 2022 y 15 clips de OpenSLR 73, incluida una entrevista simulada de 2 hablantes).
Fecha de extracción: 2026-10-25.

**Pipeline.** PaddleOCR 3.7 (`lang="es"`) · faster-whisper large-v3-turbo con VAD Silero · diarización con huellas WeSpeaker ·
seudonimización (NER + revisión humana + `voz.seudonimizar` + regex de DNI/teléfono/correo) · extracción JSON con Ollama qwen2.5:3b.

**Privacidad.** Los nombres de personas privadas se reemplazaron por `[PERSONA_nn]` en todos los textos publicados. No se publican
los audios de entrevistas reales ni las imágenes que muestran nombres de personas vivas.
""")
    st.dataframe(fuentes, hide_index=True, width="stretch", height=420)
    st.download_button("⬇️ Descargar fuentes.csv", fuentes.to_csv(index=False).encode("utf-8"), "fuentes.csv", "text/csv")
