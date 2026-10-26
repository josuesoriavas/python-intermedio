# Tarea 2 – Voces y documentos peruanos: del archivo escaneado al texto buscable

**Dashboard público:** se publica en Streamlit Community Cloud desde `tarea_2/app.py` (enlace en el Issue de entrega)

## 1. Pregunta del proyecto
**¿Pueden convertirse documentos escaneados y entrevistas en audio en un archivo de texto estructurado y buscable?**

Se armó un pipeline 100 % local y con modelos abiertos que lee documentos peruanos con **PaddleOCR**, transcribe audio en español peruano con **faster-whisper + VAD**, separa hablantes, **seudonimiza** a las personas privadas, extrae campos estructurados con un **LLM local (Ollama)** y publica todo en un **dashboard de Streamlit** para buscar y comparar. Los modelos se evaluaron con CER/WER contra transcripciones hechas por personas.

| Resultado (muestra de evaluación: 10 documentos y 10 clips) | Valor |
|---|---|
| CER línea base (PaddleOCR sin personalización) | 0.399 |
| CER PaddleOCR + preprocesamiento / EasyOCR | 0.465 / 0.480 |
| WER línea base (faster-whisper small, CPU) | 0.112 (RTF 0.14) |
| **WER elegido (faster-whisper large-v3-turbo)** | **0.094** (RTF 0.20) |
| WER Qwen3-ASR 0.6B | 0.125 (RTF 0.57) |
| **Acuerdo LLM vs. auditoría humana** | **17/20** |

## 2. Corpus, fuentes y licencias
**Fecha de extracción:** 2026-10-25 (`descargar_datos.py`, API de Wikimedia con User-Agent descriptivo y pausas de 1,5–3 s; OpenSLR leído por partes con HTTP Range). El detalle por archivo está en [`datos/fuentes.csv`](datos/fuentes.csv).

**A. Documentos (25):**

| Tipo | N | Fuente | Licencia |
|---|---|---|---|
| Impresos nítidos | 8 | Escaneos de Wikisource: *Tradiciones peruanas* (Ricardo Palma, 1893), *Historia General del Perú* (Inca Garcilaso, ed. 1800) y Decreto Ley 17716 de Reforma Agraria (1969) | Dominio público |
| Fotos con inclinación, brillo o sombras | 8 | Placas de Lima y el *Estado General* de Miguel Grau enmarcado, fotografiados por usuarios de Wikimedia Commons (AlejandroFC, Omar Vega Ramos, TheLimean, Dtarazona, Ministerio de Defensa del Perú) | CC BY-SA 4.0, CC BY-SA 3.0, CC BY 2.0, dominio público |
| Manuscritos | 9 | *Nueva corónica y buen gobierno* de Guaman Poma (1615), Acta de la Independencia del Perú (1821, original y facsímil fotografiado) y Capitulación de Ayacucho (1824), Wikimedia Commons | Dominio público; facsímil CC BY-SA 3.0 (Murillo Perú) |

**B. Audio (37,8 min, 23 clips):**

| Fuente | Clips | Descripción | Licencia |
|---|---|---|---|
| Wikimedia Commons | 8 | Entrevistas reales grabadas en Lima en 2022 (El Agustino, Fiestas Patrias, conferencia de prensa, medio tiempo del Perú–Australia). Autores: JorgeFlores-pe (Wikimedia Perú), QM Keen, Gianpier Yair Venegas Ambia, Ariana Lucero De La Cruz Guerrero | CC BY-SA 4.0 |
| OpenSLR 73 | 14 | *Crowdsourced high-quality Peruvian Spanish speech data set* (Google; Guevara-Rukoz et al., 2020): 11 frases leídas seguidas por cada hablante (7 mujeres, 7 hombres) | CC BY-SA 4.0 |
| OpenSLR 73 | 1 | Entrevista simulada de 2 hablantes armada con frases de OpenSLR (verdad conocida para medir la diarización) | CC BY-SA 4.0 |

**Descartes:** 7 imágenes candidatas se descartaron al revisar el corpus (una pintura, un grabado sin texto, una imagen ilegible de 227 px, una placa casi sin texto y 3 documentos con datos personales de personas vivas). No hubo duplicados por hash ni audios sin voz (regla: <20 % de voz según Silero VAD). Detalle en `01_extraccion.ipynb`.

**Ética y privacidad:**
* **Seudonimización:** el NER `mrm8488/bert-spanish-cased-finetuned-ner` propone candidatos, una revisión humana decide, y `voz.seudonimizar` (coincidencia difusa) reemplaza a las personas privadas o contemporáneas por `[PERSONA_nn]`; además se reemplazan DNI, teléfonos y correos. Los personajes históricos en su rol público (Grau, Garcilaso, Atahualpa…) no se tocan. Se reemplazaron 15 personas privadas en 10 registros y se verificó que no quedara ningún nombre real. La tabla de correspondencias queda fuera de Git (`datos/raw/`).
* **Qué se publica:** solo textos seudonimizados. En `datos/ejemplos/` hay imágenes de dominio público o CC sin nombres de personas vivas y audios de OpenSLR (voluntarios anónimos). Los audios de las entrevistas reales **no** se publican porque en ellos se dicen nombres que no se pueden seudonimizar en la voz: en el dashboard se consultan como texto y metadatos, con enlace a su ficha de Commons.
* Los audios crudos, las imágenes completas, las salidas SRT/TXT y los pesos de los modelos están en `.gitignore`.

## 3. Pipeline
1. **OCR** (`01_extraccion.ipynb`): PaddleOCR 3.7.0 (PP-OCRv6 medium det + rec, `lang="es"`), respaldo crudo (JSON, imagen anotada y un recorte por línea) en `datos/raw/documentos/paddle/`.
2. **ASR**: faster-whisper 1.2.1 con Whisper large-v3-turbo (int8, CPU), VAD Silero, `language="es"`; diarización con huellas WeSpeaker + clustering (`voz.py` de la Sesión 13); exportación a CSV, SRT y TXT.
3. **Seudonimización, limpieza y EDA** (3 gráficos Plotly con títulos analíticos).
4. **Evaluación** (`02_evaluacion.ipynb`): CER/WER sobre la misma muestra para 3 OCR (PaddleOCR base, PaddleOCR con preprocesamiento, EasyOCR) y 3 ASR (faster-whisper small, large-v3-turbo, Qwen3-ASR 0.6B).
5. **Extracción estructurada**: Ollama `qwen2.5:3b` con salida JSON → `datos/extraccion_llm.csv`, y auditoría humana de 20 casos (`datos/auditoria_llm.csv`).

## 4. Hallazgos analíticos
1. **El tipo de documento importa más que el modelo de OCR.** Con PaddleOCR el CER va de 0.42 en impresos a 0.16 en fotos y 0.63 en manuscritos: los tres OCR fallan en Guaman Poma (letra del siglo XVII; sobre los dibujos el reconocedor hasta inventa caracteres chinos). Además, el decreto de 1969 a dos columnas tiene CER alto por **orden de lectura**, no por letras mal leídas. El preprocesamiento de PaddleOCR (corrección de deformación) **empeora** las placas fotografiadas.
2. **En audio el modelo grande gana, pero la condición de grabación pesa más.** large-v3-turbo tiene el menor WER y corre a RTF 0.20 en CPU; la lectura limpia de OpenSLR queda cerca de WER 0,02, mientras las entrevistas reales en la calle (ruido de tránsito y de estadio, habla espontánea) multiplican el error. La diarización acertó el 100 % en la entrevista simulada. El LLM local acertó 17/20 extracciones; sus errores están en textos OCR ilegibles.

## 5. Limitaciones técnicas
1. **Muestra de evaluación pequeña y referencias heterogéneas:** 10 documentos y 10 clips; un solo documento largo (el decreto) pesa mucho en el CER agregado, y las referencias de las placas vienen de transcripciones de Commons que modernizan la ortografía (por eso se normalizan tildes y u/v). Una de las 20 auditorías quedó sin juicio y se contó como no confirmada.
2. **Cómputo solo en CPU y modelos genéricos:** sin GPU, PaddleOCR tarda ~45 s por página y no hay un modelo de escritura a mano (HTR) para manuscritos ni análisis de diseño para páginas a dos columnas; la diarización usa un umbral fijo que partió en dos a un lector de OpenSLR. Los audios de entrevistas reales no se publican en el dashboard porque contienen nombres dichos en voz.

## 6. Cómo ejecutar en local
**Dashboard** (solo lee CSV; Python 3.12+):
```bash
git clone https://github.com/josuesoriavas/python-intermedio.git
cd python-intermedio/tarea_2
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```
Se abre en `http://localhost:8501`.

**Reproducir los notebooks** (Python 3.12, CPU; baja ~3 GB de modelos la primera vez):
```bash
uv venv .venv --python 3.12
uv pip install --python .venv -r requirements-notebooks.txt --index-strategy unsafe-best-match
ollama pull qwen2.5:3b
.venv\Scripts\python descargar_datos.py          # corpus a datos/raw/ (no versionado)
.venv\Scripts\jupyter nbconvert --to notebook --execute --inplace 01_extraccion.ipynb
.venv\Scripts\jupyter nbconvert --to notebook --execute --inplace 02_evaluacion.ipynb
```
Los notebooks guardan cada inferencia en `datos/raw/cache/`, así que una re-ejecución no repite OCR, ASR ni LLM. Dos archivos locales no se versionan porque contienen nombres reales: `datos/raw/seudonimizacion/revision.json` (decisiones de la revisión humana) y `datos/raw/referencias_manuales.csv` (transcripción manual de 2 entrevistas).

## Estructura
```
tarea_2/
├── 01_extraccion.ipynb        # OCR, ASR + VAD + diarización, seudonimización, limpieza y EDA
├── 02_evaluacion.ipynb        # CER/WER, comparación de modelos, LLM y auditoría
├── app.py                     # Dashboard Streamlit (solo lee datos/)
├── descargar_datos.py         # Descarga reproducible del corpus con su atribución
├── herramientas.py            # OCR, ASR, seudonimización, métricas y caché
├── voz.py                     # Módulo de la Sesión 13 (ASR, VAD, diarización, SRT, seudonimización)
├── requirements.txt           # Solo para la app
├── requirements-notebooks.txt # Entorno exacto de los notebooks
├── evidencias_ia/             # Capturas de la conversación con Claude Code
├── datos/
│   ├── documentos.csv         # 25 documentos (OCR seudonimizado + referencia en la muestra)
│   ├── transcripciones.csv    # 23 clips (ASR con hablantes + referencia en la muestra)
│   ├── extraccion_llm.csv     # Campos JSON extraídos por el LLM
│   ├── auditoria_llm.csv      # Revisión humana de 20 extracciones
│   ├── fuentes.csv            # Fuente, licencia y acceso de cada archivo
│   ├── evaluacion_ocr.csv / evaluacion_asr.csv / metricas.json   # Resultados de la Parte 2
│   └── ejemplos/              # Imágenes y audios publicables para el dashboard
└── modelos/                   # (vacío: los pesos se descargan de Hugging Face / PaddleX)
```

## Uso de IA
El desarrollo se hizo con apoyo de Claude Code; las capturas de la conversación están en `evidencias_ia/`. Las transcripciones de referencia, la revisión de la seudonimización y la auditoría del LLM son trabajo humano.
