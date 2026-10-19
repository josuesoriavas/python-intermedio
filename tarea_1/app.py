"""Dashboard Tarea 1 – Clasificador de noticias peruanas (La República vs. El Comercio).

Ejecutar desde la carpeta tarea_1/:
    streamlit run app.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
DATOS = BASE / "datos"
MODELO = BASE / "modelo"
ETIQUETAS = ["politica", "economia", "deportes", "ciencia_tecnologia"]
NOMBRES = {"politica": "Política", "economia": "Economía", "deportes": "Deportes",
           "ciencia_tecnologia": "Ciencia y tecnología"}
COLORES = {"politica": "#C8102E", "economia": "#2E8B57", "deportes": "#E08E0B", "ciencia_tecnologia": "#1F4E79"}

st.set_page_config(page_title="Clasificador de noticias peruanas", page_icon="📰", layout="wide")


@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATOS / "noticias.csv").fillna({"bajada": ""})
    llm_path = DATOS / "etiquetas_llm.csv"
    if llm_path.exists():
        llm = pd.read_csv(llm_path)[["titular", "etiqueta_llm", "confianza"]]
        df = df.merge(llm, on="titular", how="left")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df


@st.cache_data
def cargar_metricas():
    p = MODELO / "metricas.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@st.cache_resource(show_spinner="Cargando el modelo fine-tuned…")
def cargar_clasificador():
    if not (MODELO / "config.json").exists() or not any(MODELO.glob("*.safetensors")):
        return None
    from transformers import pipeline
    return pipeline("text-classification", model=str(MODELO), tokenizer=str(MODELO), top_k=None, device=-1)


df = cargar_datos()
met = cargar_metricas()
MODELO_FINAL = met.get("modelo_final", "distilbert-base-multilingual-cased")
NOMBRE_MODELO = "BETO" if "spanish" in MODELO_FINAL else "DistilBERT"

# ---------------- Encabezado ----------------
st.title("📰 ¿Pueden los titulares peruanos convertirse en un clasificador de noticias?")
st.markdown(
    "Titulares reales de **La República** y **El Comercio** (opción C – comparada), etiquetados por sección editorial "
    f"y por un LLM local, usados para entrenar un Transformer (**{NOMBRE_MODELO}**) que clasifica cualquier titular nuevo en "
    "`politica`, `economia`, `deportes` o `ciencia_tecnologia`."
)
with st.expander("Resumen metodológico"):
    st.markdown(f"""
1. **Recolección** (`01_recoleccion.ipynb`): RSS, sitemaps y portadas de sección permitidos por `robots.txt`, pausa de 1.5 s y
   máximo 1 reintento. Limpieza de duplicados/vacíos y mapeo explícito `seccion_original → etiqueta`.
2. **Línea base zero-shot**: `Recognai/bert-base-spanish-wwm-cased-xnli` sobre 40 titulares.
3. **Supervisión débil**: `{met.get('llm_modelo', 'ollama/qwen2.5:3b')}` con prompt estructurado y salida JSON, auditado manualmente en 20 casos.
4. **Fine-tuning**: se compararon `distilbert-base-multilingual-cased` y BETO con split estratificado 70/15/15 (`random_state=42`);
   el elegido por F1 macro en validación fue `{MODELO_FINAL}`.
5. **Evaluación**: métricas finales calculadas **solo sobre el test reservado** ({met.get('n_test', '—')} titulares).
""")

# ---------------- Barra lateral ----------------
st.sidebar.header("Filtros")
medios = st.sidebar.multiselect("Medio", sorted(df["medio"].unique()), default=sorted(df["medio"].unique()))
cats = st.sidebar.multiselect("Categoría", ETIQUETAS, default=ETIQUETAS, format_func=NOMBRES.get)
fmin, fmax = df["fecha"].min().date(), df["fecha"].max().date()
rango = st.sidebar.date_input("Rango de fechas", (fmin, fmax), min_value=fmin, max_value=fmax)
texto = st.sidebar.text_input("Buscar en titulares", "")

f = df[df["medio"].isin(medios) & df["etiqueta"].isin(cats)]
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    f = f[(f["fecha"].dt.date >= rango[0]) & (f["fecha"].dt.date <= rango[1])]
if texto:
    f = f[f["titular"].str.contains(texto, case=False, na=False)]
st.sidebar.caption(f"{len(f)} de {len(df)} noticias seleccionadas")

# ---------------- Indicadores ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Noticias recolectadas", f"{len(df)}", delta=f"{len(f)} filtradas", delta_color="off")
c2.metric(f"F1 macro en test ({NOMBRE_MODELO})", f"{met['f1_macro_test']:.3f}" if met else "—",
          delta=f"{met['f1_macro_test'] - met['zero_shot_f1_40']:+.3f} vs zero-shot" if met else None)
if met.get("auditoria_total"):
    c3.metric("Concordancia LLM vs. auditoría humana", f"{met['auditoria_pct']:.0%}",
              delta=f"{met['auditoria_acuerdos']}/{met['auditoria_total']} casos", delta_color="off")
else:
    c3.metric("Concordancia LLM vs. auditoría humana", "—")
c4.metric("F1 macro zero-shot (piso)", f"{met['zero_shot_f1_40']:.3f}" if met else "—")

# ---------------- Visualizaciones ----------------
izq, der = st.columns([3, 2])
with izq:
    dist = f.groupby(["etiqueta", "medio"]).size().rename("noticias").reset_index()
    dist["categoria"] = dist["etiqueta"].map(NOMBRES)
    fig = px.bar(dist, x="categoria", y="noticias", color="medio", barmode="group", text="noticias",
                 color_discrete_map={"La Republica": "#C8102E", "El Comercio": "#1F4E79"},
                 title="Distribución de categorías en la selección actual",
                 labels={"categoria": "Categoría", "noticias": "Noticias", "medio": "Medio"},
                 category_orders={"categoria": [NOMBRES[e] for e in ETIQUETAS]})
    st.plotly_chart(fig, use_container_width=True)
with der:
    if "etiqueta_llm" in f and f["etiqueta_llm"].notna().any():
        acuerdo = (f.assign(coincide=f["etiqueta"] == f["etiqueta_llm"])
                     .groupby("etiqueta")["coincide"].mean().reindex(ETIQUETAS).dropna().rename("acuerdo").reset_index())
        acuerdo["categoria"] = acuerdo["etiqueta"].map(NOMBRES)
        fig2 = px.bar(acuerdo, x="acuerdo", y="categoria", orientation="h", text_auto=".0%",
                      color="etiqueta", color_discrete_map=COLORES, range_x=[0, 1],
                      title="¿Coincide el LLM con la sección del diario?",
                      labels={"acuerdo": "% de coincidencia", "categoria": ""})
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

# ---------------- Tabla ----------------
st.subheader("Explorar noticias")
tabla = f[["fecha", "medio", "etiqueta", "titular", "bajada", "seccion_original", "url"]
          + (["etiqueta_llm"] if "etiqueta_llm" in f else [])].sort_values("fecha", ascending=False)
st.dataframe(tabla, use_container_width=True, hide_index=True,
             column_config={"url": st.column_config.LinkColumn("url"),
                            "fecha": st.column_config.DateColumn("fecha", format="YYYY-MM-DD")})
st.download_button("⬇️ Descargar selección en CSV", tabla.to_csv(index=False).encode("utf-8"),
                   file_name="noticias_filtradas.csv", mime="text/csv")

# ---------------- Probador en vivo ----------------
st.divider()
st.header("🧪 Probador en vivo")
st.caption("Escribe o pega un titular peruano nuevo y el modelo fine-tuned predice su categoría.")
ejemplo = "BCR mantiene su tasa de referencia en 4.25% por quinto mes consecutivo"
titular = st.text_area("Titular", ejemplo, height=80)
if st.button("Clasificar titular", type="primary"):
    clf = cargar_clasificador()
    if clf is None:
        st.error("No se encontró el modelo en `modelo/`. Ejecuta `02_clasificacion.ipynb` para entrenarlo "
                 "(los pesos no se suben a GitHub por su tamaño).")
    elif not titular.strip():
        st.warning("Escribe un titular.")
    else:
        salida = clf(titular.strip())
        salida = salida[0] if isinstance(salida[0], list) else salida
        probs = pd.DataFrame(salida).rename(columns={"label": "etiqueta", "score": "probabilidad"})
        probs = probs.sort_values("probabilidad", ascending=False)
        top = probs.iloc[0]
        a, b = st.columns([1, 2])
        a.metric("Categoría predicha", NOMBRES[top["etiqueta"]])
        a.metric("Confianza", f"{top['probabilidad']:.1%}")
        if top["probabilidad"] < 0.6:
            a.warning("Confianza baja: el titular podría mezclar temas o no pertenecer a las 4 categorías.")
        probs["categoria"] = probs["etiqueta"].map(NOMBRES)
        fig3 = px.bar(probs, x="probabilidad", y="categoria", orientation="h", text_auto=".1%",
                      color="etiqueta", color_discrete_map=COLORES, range_x=[0, 1],
                      title="Probabilidad por categoría", labels={"categoria": ""})
        fig3.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
        b.plotly_chart(fig3, use_container_width=True)

# ---------------- Comparativa ----------------
if met.get("comparativa"):
    st.divider()
    st.subheader("Comparativa de modelos (mismo conjunto de test)")
    comp = pd.DataFrame(met["comparativa"])
    st.dataframe(comp, use_container_width=True, hide_index=True,
                 column_config={"accuracy_test": st.column_config.NumberColumn(format="%.3f"),
                                "f1_macro_test": st.column_config.NumberColumn(format="%.3f"),
                                "ms_por_titular_cpu": st.column_config.NumberColumn(format="%.0f ms")})
    if (MODELO / "matriz_confusion_test.png").exists():
        with st.expander("Matriz de confusión en test"):
            st.image(str(MODELO / "matriz_confusion_test.png"), width=520)

st.caption("Tarea 1 – Python Intermedio · Datos: larepublica.pe y elcomercio.pe (RSS/sitemaps oficiales).")
