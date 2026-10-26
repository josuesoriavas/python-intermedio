"""Funciones de la Tarea 2 que usan los dos notebooks: OCR, ASR, seudonimización, métricas y caché.

El ASR, la diarización y la seudonimización vienen de `voz.py` (Sesión 13). Aquí se agregan el
OCR (Sesión 10), la caché de resultados (para no repetir inferencias al re-ejecutar los notebooks)
y la normalización común para CER/WER.
"""
from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path

# Descargas de modelos: HTTP simple (Xet se trababa en esta red) y sin el chequeo de conectividad de PaddleX
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

import torch  # noqa: F401  (en Windows, importar torch antes que paddle evita un error de DLL)
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "datos" / "raw"
CACHE = RAW / "cache"


# ───────────────────────────────────────────────────────── caché
def en_cache(nombre: str, funcion, *args, **kwargs):
    """Guarda en datos/raw/cache/<nombre>.json lo que devuelve `funcion` y lo reutiliza después."""
    ruta = CACHE / f"{nombre}.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    salida = funcion(*args, **kwargs)
    ruta.write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    return salida


# ───────────────────────────────────────────────────────── OCR
CONFIG_OCR = {
    # Línea base: PaddleOCR 3.x "tal cual" (PP-OCRv5, modelo latino para español), sin preprocesamiento
    "paddle_base": dict(lang="es", enable_mkldnn=False, use_doc_orientation_classify=False, use_doc_unwarping=False,
                        use_textline_orientation=False),
    # Misma red con el preprocesamiento de documentos que trae PaddleOCR: orientación de página,
    # corrección de deformación (UVDoc) y orientación de cada línea. Pensado para fotos inclinadas.
    "paddle_prepro": dict(lang="es", enable_mkldnn=False, use_doc_orientation_classify=True, use_doc_unwarping=True,
                          use_textline_orientation=True),
}
_paddle: dict = {}
_easy = None


def ocr_paddle(ruta, config: str = "paddle_base", salida: Path | None = None) -> dict:
    """Texto de una imagen con PaddleOCR. Si se da `salida`, guarda el JSON crudo, la imagen anotada
    y un recorte por cada línea detectada (respaldo crudo para revisar errores)."""
    from paddleocr import PaddleOCR
    if config not in _paddle:
        _paddle[config] = PaddleOCR(**CONFIG_OCR[config])
    t0 = time.perf_counter()
    r = _paddle[config].predict(str(ruta))[0]
    segundos = time.perf_counter() - t0
    textos = [t for t in r["rec_texts"]]
    scores = [float(s) for s in r["rec_scores"]]
    polys = [np.asarray(p).astype(int).tolist() for p in r["rec_polys"]]
    if salida is not None:
        from PIL import Image
        salida.mkdir(parents=True, exist_ok=True)
        r.save_to_json(str(salida))
        r.save_to_img(str(salida))
        img = Image.open(ruta).convert("RGB")
        (salida / "recortes").mkdir(exist_ok=True)
        for i, p in enumerate(polys):
            xs, ys = [q[0] for q in p], [q[1] for q in p]
            img.crop((min(xs), min(ys), max(xs), max(ys))).save(salida / "recortes" / f"linea_{i:03d}.png")
    return {"texto": "\n".join(textos), "n_lineas": len(textos), "confianza_media": float(np.mean(scores)) if scores else None,
            "segundos": round(segundos, 3)}


def _ordenar_lineas(cajas: list[tuple[list, str]]) -> str:
    """Ordena cajas de texto en lectura natural: de arriba abajo por renglón y de izquierda a derecha."""
    if not cajas:
        return ""
    items = []
    for caja, texto in cajas:
        ys, xs = [p[1] for p in caja], [p[0] for p in caja]
        items.append(((min(ys) + max(ys)) / 2, max(ys) - min(ys), min(xs), texto))
    items.sort()
    renglones, actual = [], [items[0]]
    for it in items[1:]:
        if abs(it[0] - actual[-1][0]) < 0.5 * max(it[1], actual[-1][1]):
            actual.append(it)
        else:
            renglones.append(actual)
            actual = [it]
    renglones.append(actual)
    return "\n".join(" ".join(t for *_, t in sorted(r, key=lambda z: z[2])) for r in renglones)


def ocr_easyocr(ruta) -> dict:
    """OCR alternativo: EasyOCR (detector CRAFT + reconocedor CRNN, modelo 'es'). Se instala con pip y
    corre en CPU; reemplaza a Tesseract, que en Windows exige instalar un binario con permisos de administrador."""
    global _easy
    import easyocr
    if _easy is None:
        _easy = easyocr.Reader(["es"], gpu=False, verbose=False)
    t0 = time.perf_counter()
    r = _easy.readtext(str(ruta), paragraph=False)
    segundos = time.perf_counter() - t0
    texto = _ordenar_lineas([(np.asarray(c).tolist(), t) for c, t, _ in r])
    return {"texto": texto, "n_lineas": len(r), "confianza_media": float(np.mean([s for *_, s in r])) if r else None,
            "segundos": round(segundos, 3)}


# ───────────────────────────────────────────────────────── ASR
_transcriptores: dict = {}

MODELOS_ASR = {
    # clave propia: (clave en voz.MODELOS o ruta de faster-whisper, descripción)
    "fw-small": "faster-whisper small (CPU int8, beam 5, VAD Silero on, idioma=es)",
    "fw-turbo": "faster-whisper large-v3-turbo (CPU int8, beam 5, VAD Silero on, idioma=es)",
    "qwen3-asr-0.6b": "Qwen3-ASR 0.6B (CPU float32, VAD Silero de voz.py, idioma=es)",
}


def transcriptor(clave: str):
    import voz
    if clave not in _transcriptores:
        if clave == "fw-small":  # misma interfaz de voz.py, pero con los pesos de Whisper small
            import os
            from faster_whisper import WhisperModel
            t = voz.Transcriptor.__new__(voz.Transcriptor)
            t.clave, t.device, t.idioma_mms = "faster-whisper", "cpu", "spa"
            t.info = dict(voz.MODELOS["faster-whisper"], nombre="faster-whisper small", hf="Systran/faster-whisper-small")
            t0 = time.perf_counter()
            t.modelo = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=min(8, os.cpu_count() or 4))
            t.segundos_carga = time.perf_counter() - t0
        elif clave == "fw-turbo":
            t = voz.Transcriptor("faster-whisper")
        else:
            t = voz.Transcriptor(clave)
        _transcriptores[clave] = t
    return _transcriptores[clave]


def transcribir(ruta, clave: str) -> dict:
    """Audio -> segmentos con tiempos + latencia. El factor de tiempo real (RTF) = segundos / duración."""
    import voz
    audio = voz.cargar_audio(ruta)
    t = transcriptor(clave)
    t0 = time.perf_counter()
    segs = t.segmentos(audio, idioma="es")
    segundos = time.perf_counter() - t0
    dur = len(audio) / voz.SR
    return {"segmentos": [s.__dict__ for s in segs], "duracion_seg": round(dur, 2), "segundos": round(segundos, 2),
            "rtf": round(segundos / dur, 3)}


def diarizar(ruta, segmentos: list[dict], n_hablantes: int | None = None, umbral: float = 0.7) -> list[dict]:
    import voz
    audio = voz.cargar_audio(ruta)
    segs = [voz.Segmento(s["inicio"], s["fin"], s["texto"]) for s in segmentos]
    return [s.__dict__ for s in voz.diarizar(audio, segs, n_hablantes=n_hablantes, umbral=umbral, device="cpu")]


def texto_con_hablantes(segmentos: list[dict]) -> str:
    """Une segmentos seguidos del mismo hablante: '[HABLANTE_1] ... [HABLANTE_2] ...'."""
    turnos = []
    for s in segmentos:
        h = s.get("hablante")
        if turnos and turnos[-1][0] == h:
            turnos[-1][1].append(s["texto"])
        else:
            turnos.append([h, [s["texto"]]])
    return " ".join((f"[HABLANTE_{h[1:]}] " if h else "") + " ".join(x) for h, x in turnos).strip()


# ───────────────────────────────────────────────────────── seudonimización
DNI = re.compile(r"\b\d{8}\b")
TELEFONO = re.compile(r"\b9\d{2}[\s-]?\d{3}[\s-]?\d{3}\b")
CORREO = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")

_ner = None


def personas_ner(texto: str, umbral: float = 0.85) -> list[str]:
    """Candidatos a nombre de persona (NER en español, mrm8488/bert-spanish-cased-finetuned-ner).
    Es solo una lista para revisar a mano: el modelo no distingue personas privadas de personajes históricos."""
    global _ner
    from transformers import pipeline
    if _ner is None:
        _ner = pipeline("ner", model="mrm8488/bert-spanish-cased-finetuned-ner", aggregation_strategy="simple", device=-1)
    nombres = []
    for i in range(0, len(texto), 1500):  # el modelo acepta ~512 tokens
        for e in _ner(texto[i:i + 1500]):
            nombre = re.sub(r"\s+", " ", re.sub(r"^[#\W]+", "", e["word"])).strip()  # quita restos de subpalabras (##)
            if e["entity_group"] == "PER" and e["score"] >= umbral and len(nombre) > 3:
                nombres.append(nombre)
    return nombres


def seudonimizar(texto: str, reemplazos: dict[str, str]) -> tuple[str, int]:
    """Nombres (con coincidencia difusa de voz.py), DNI, teléfonos y correos -> marcadores.
    Devuelve el texto y el número de entidades reemplazadas."""
    import voz
    if not isinstance(texto, str) or not texto:
        return texto, 0
    salida = voz.seudonimizar(texto, reemplazos) if reemplazos else texto
    n = sum(salida.count(s) - texto.count(s) for s in set(reemplazos.values()))
    for patron, marca in [(DNI, "[DNI]"), (TELEFONO, "[TELEFONO]"), (CORREO, "[CORREO]")]:
        salida, k = patron.subn(marca, salida)
        n += k
    return salida, n


# ───────────────────────────────────────────────────────── métricas
MARCA_HABLANTE = re.compile(r"\[HABLANTE_\d+\]|\[H\d+\]")


def normalizar(texto: str) -> str:
    """Mismo criterio para referencia e hipótesis: sin marcas de hablante, minúsculas, sin puntuación,
    ſ (s larga) como s y espacios simples. Las tildes se conservan (son parte de la ortografía)."""
    texto = MARCA_HABLANTE.sub(" ", texto or "")
    texto = unicodedata.normalize("NFC", texto.replace("ſ", "s").lower())
    texto = re.sub(r"[^\w\s]", " ", texto).replace("_", " ")
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_doc(texto: str) -> str:
    """Para el CER de documentos: normalizar() + sin tildes ni diéresis y u/v como una misma letra.

    Las placas están en mayúsculas sin tildes y escriben V por U (CIRCVLO, PERV), pero sus
    transcripciones en Commons modernizan la ortografía; Guaman Poma también alterna u/v. Sin esto,
    el CER castigaría al OCR por leer bien una convención gráfica. La ñ se conserva."""
    t = normalizar(texto).replace("ñ", "\0")
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return t.replace("\0", "ñ").replace("v", "u")


def cer(ref: str, hip: str) -> float:
    import jiwer
    return float(jiwer.cer(normalizar_doc(ref), normalizar_doc(hip) or "∅"))


def wer(ref: str, hip: str) -> float:
    import jiwer
    return float(jiwer.wer(normalizar(ref), normalizar(hip) or "∅"))


def cer_corpus(refs, hips) -> float:
    """CER agregado (errores totales / caracteres totales), no el promedio de CER por documento."""
    import jiwer
    return float(jiwer.cer([normalizar_doc(r) for r in refs], [normalizar_doc(h) or "∅" for h in hips]))


def wer_corpus(refs, hips) -> float:
    import jiwer
    return float(jiwer.wer([normalizar(r) for r in refs], [normalizar(h) or "∅" for h in hips]))


# ───────────────────────────────────────────────────────── extracción estructurada con LLM
MODELO_LLM = "qwen2.5:3b"  # Ollama local: nada sale de la computadora

_REGLAS = """Reglas:
- Responde SOLO con un objeto JSON válido, sin texto adicional.
- Usa null cuando el dato no aparece explícitamente en el texto. No inventes ni completes con conocimiento externo.
- El texto viene de {origen} y puede tener errores de lectura: no los corrijas en los campos copiados.
- Los marcadores [PERSONA_01], [PERSONA_02]... son seudónimos de personas reales: déjalos tal cual, no adivines nombres.
- Escribe todo en español."""

PROMPT_DOCUMENTO = """Extrae información estructurada de este documento peruano leído con OCR.
Devuelve un JSON con exactamente estas claves:
- "modalidad": "documento"
- "tema": tema principal en 2 a 6 palabras
- "resumen": 1 o 2 oraciones sobre lo que dice el documento
- "tipo_documental": "literario", "historico", "legal", "placa conmemorativa", "cronica" u "otro"
- "emisor": persona o institución que emite, dedica o firma el documento (null si no aparece)
- "fecha": fecha o año que aparezca escrito en el texto, tal cual (null si no aparece)
- "monto": cantidad de dinero que aparezca en el texto (null si no aparece)
- "lugar": lugar principal mencionado (null si no aparece)
""" + _REGLAS.format(origen="un OCR") + "\n\nTEXTO:\n{texto}"

PROMPT_AUDIO = """Extrae información estructurada de esta transcripción automática de un audio en español peruano.
Devuelve un JSON con exactamente estas claves:
- "modalidad": "audio"
- "tema": tema principal en 2 a 6 palabras
- "resumen": 1 o 2 oraciones sobre lo que se dice
- "tipo_audio": "entrevista", "lectura" o "conversacion"
- "numero_hablantes": número de marcas distintas [HABLANTE_n] que aparecen en el texto (null si no hay marcas)
- "citas_clave": lista de 1 a 3 frases copiadas textualmente de la transcripción (lista vacía si no hay frases claras)
- "lugar": lugar mencionado en el audio (null si no se menciona)
""" + _REGLAS.format(origen="un reconocedor de voz") + "\n\nTRANSCRIPCIÓN:\n{texto}"

CLAVES = {"documento": ["modalidad", "tema", "resumen", "tipo_documental", "emisor", "fecha", "monto", "lugar"],
          "audio": ["modalidad", "tema", "resumen", "tipo_audio", "numero_hablantes", "citas_clave", "lugar"]}


def extraer_llm(texto: str, modalidad: str, max_chars: int = 5000) -> dict:
    """Pide a Ollama un JSON con los campos de la modalidad; deja solo las claves esperadas."""
    import requests
    prompt = (PROMPT_DOCUMENTO if modalidad == "documento" else PROMPT_AUDIO).format(texto=(texto or "")[:max_chars])
    t0 = time.perf_counter()
    r = requests.post("http://localhost:11434/api/generate", timeout=600, json={
        "model": MODELO_LLM, "prompt": prompt, "format": "json", "stream": False,
        "options": {"temperature": 0, "seed": 2026, "num_ctx": 8192}})
    r.raise_for_status()
    crudo = r.json()["response"]
    try:
        datos = json.loads(crudo)
    except json.JSONDecodeError:
        datos = {}
    campos = {k: datos.get(k) for k in CLAVES[modalidad]}
    campos["modalidad"] = modalidad
    for k, v in campos.items():  # el modelo a veces escribe "null" o "" en vez de null
        if isinstance(v, str) and v.strip().lower() in {"", "null", "none", "n/a", "no aparece", "desconocido"}:
            campos[k] = None
    return {"campos": campos, "segundos": round(time.perf_counter() - t0, 2), "json_valido": bool(datos)}
