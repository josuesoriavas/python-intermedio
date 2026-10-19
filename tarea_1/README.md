# Tarea 1 – Noticias peruanas: del titular al clasificador

## 1. Pregunta del proyecto
**¿Pueden convertirse titulares peruanos en un clasificador de noticias?**

Se recolectaron titulares reales de dos diarios peruanos, se etiquetaron con la sección editorial del diario y con un LLM local (supervisión débil), y se entrenó un Transformer ligero (se compararon DistilBERT multilingüe y BETO; ganó BETO por validación) que clasifica cualquier titular nuevo en `politica`, `economia`, `deportes` o `ciencia_tecnologia`. Un dashboard en Streamlit permite explorar el corpus y probar el clasificador en vivo.

| Resultado (conjunto de test reservado) | Valor |
|---|---|
| F1 macro Transformer fine-tuned (BETO) | **0.865** |
| F1 macro zero-shot (40 titulares, piso) | 0.638 |
| Acuerdo LLM vs. auditoría humana | 19/20 (95 %) |

## 2. Medios y fechas de extracción
* **Opción C – Comparada:** La República (`larepublica.pe`) y El Comercio (`elcomercio.pe`).
* **Fecha de descarga:** 2026-10-18. Noticias publicadas entre **2026-03-19** y **2026-10-18**.
* **Corpus final:** 400 noticias (73 de La República y 327 de El Comercio) en `datos/noticias.csv`.
* **Fuentes (todas permitidas por `robots.txt`):** RSS por sección y `home.xml` de La República, sitemaps `/sitemap/web/…` de ambos medios, feeds RSS de Google News de El Comercio y portadas de sección de La República **sin paginar** (su `robots.txt` prohíbe `/*/pag/`). User-Agent descriptivo, pausa de 1.5 s entre solicitudes y máximo 1 reintento. Respaldo crudo en `datos/raw/`.

## 3. Hallazgos analíticos
1. **`deportes` es la categoría más fácil y `economia` la más difícil, porque en el Perú la frontera entre economía y política es difusa.** BETO obtiene F1 0.968 en deportes (clubes, marcadores y "Liga 1" son un léxico casi exclusivo) pero solo 0.759 en economía. Sus errores son noticias como *"Gobierno designa presidenta del directorio del Fonafe"*: El Comercio la publica en economía, pero su lenguaje es político, y en la auditoría humana también se le asignó `politica`. Parte del error es ambigüedad de la propia etiqueta editorial.
2. **Un LLM pequeño y local etiqueta casi tan bien como un humano, pero con un sesgo hacia `politica`.** `qwen2.5:3b` coincide con la sección del diario en el 87.5 % de las 400 noticias y con la auditoría humana en 19 de 20 casos. Su error típico es mandar noticias a `politica` (recall 0.99 pero precision 0.78): ahí terminaron 17 de las 27 noticias de economía que etiquetó mal y 9 de las 20 de ciencia y tecnología. Aun así, el modelo fine-tuned lo supera en test (0.865 vs. 0.827) y es más de 100 veces más rápido (~20 ms vs. ~3.5–4 s por titular en CPU).
3. *(Comparación de medios)* Los titulares de La República son algo más largos (mediana 104 caracteres) que los de El Comercio (99). En El Comercio, los más cortos son columnas de opinión económica con títulos tipo eslogan.

## 4. Limitaciones técnicas
1. **Cobertura desigual por medio y test pequeño.** La República prohíbe la paginación en su `robots.txt`, así que solo expone ~73 noticias recientes de estas secciones; el corpus quedó 18 % / 82 % (no 200/200), lo que limita la comparación entre medios. Además, el test tiene 60 titulares: cada error mueve el F1 en ~0.017, así que diferencias menores a ~0.04 entre modelos no son concluyentes.
2. **La etiqueta de referencia es la sección editorial y es temporalmente acotada.** Las secciones contienen ruido (la sección tecnología de El Comercio incluye notas sobre conciertos o videojuegos; economía, designaciones de funcionarios) y el 88 % de las noticias es de la última semana, así que el modelo aprende la agenda del momento (gobierno de turno, Torneo Clausura) y podría degradarse con el tiempo (*concept drift*). Por otro lado, los pesos del modelo (~420 MB) no se suben a GitHub: para usar el probador en otra máquina hay que ejecutar `02_clasificacion.ipynb`, y por eso no se desplegó en Streamlit Community Cloud.

## 5. Cómo ejecutar en local
Requisitos: Python 3.14 (probado en Windows 11, solo CPU) y, para re-etiquetar con el LLM, [Ollama](https://ollama.com).

```bash
git clone https://github.com/josuesoriavas/python-intermedio.git
cd python-intermedio/tarea_1
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

**Dashboard** (necesita el modelo entrenado en `modelo/`; los pesos no se suben a GitHub por su tamaño, se generan al ejecutar el notebook 02):
```bash
streamlit run app.py
```
Se abre en `http://localhost:8501`. Sin pesos, todo el dashboard funciona excepto el probador en vivo, que muestra cómo generarlos.

**Reproducir los notebooks:**
```bash
ollama pull qwen2.5:3b            # LLM para la supervisión débil (solo si se quiere re-etiquetar)
jupyter nbconvert --to notebook --execute --inplace 01_recoleccion.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_clasificacion.ipynb
```
`01_recoleccion.ipynb` reutiliza la caché `datos/raw/articulos_raw.jsonl`, y `02_clasificacion.ipynb` reutiliza `datos/etiquetas_llm.csv`, así que no se repiten descargas ni consultas al LLM.

## Estructura
```
tarea_1/
├── 01_recoleccion.ipynb      # Scraping (RSS/sitemaps), limpieza, mapeo y EDA
├── 02_clasificacion.ipynb    # Zero-shot, LLM débil, auditoría, fine-tuning y evaluación
├── app.py                    # Dashboard Streamlit
├── requirements.txt
├── .streamlit/config.toml    # Configuración del dashboard
├── datos/
│   ├── noticias.csv          # Corpus final (7 columnas)
│   ├── etiquetas_llm.csv     # Etiquetas del LLM (titular, etiqueta_llm, confianza, modelo_llm, fecha)
│   ├── auditoria_humana.csv  # Revisión manual de 20 etiquetas del LLM
│   ├── split.csv             # Asignación train/val/test de cada URL
│   └── raw/                  # robots.txt, RSS, sitemaps y metadata cruda de artículos
└── modelo/                   # config, tokenizer, métricas y matriz de confusión (pesos excluidos en .gitignore)
```
