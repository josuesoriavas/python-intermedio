"""Descarga el corpus de la Tarea 2 (documentos + audio). Todo tiene licencia libre y se cita.

    .venv\\Scripts\\python descargar_datos.py

Qué baja a datos/raw/ (no se versiona en Git):

- documentos/: 25 imágenes de documentos peruanos.
  * 8 impresos nítidos: páginas escaneadas de Wikisource (Tradiciones peruanas de Ricardo Palma, 1893;
    Historia General del Perú del Inca Garcilaso; Ley de Reforma Agraria de 1969). Dominio público.
  * 8 fotos con inclinación, brillo o sombras: placas y un documento enmarcado fotografiados en Lima
    (Wikimedia Commons, CC BY / CC BY-SA).
  * 9 manuscritos: Nueva corónica y buen gobierno de Guaman Poma (1615), Acta de la Independencia
    (1821) y Capitulación de Ayacucho (1824). Dominio público (salvo el facsímil, CC BY-SA 3.0).
- audio/: 23 clips de español peruano (~35 min).
  * 8 entrevistas reales de Wikimedia Commons (CC BY-SA 4.0), grabadas en Lima en 2022.
  * 14 clips de lectura de OpenSLR 73 (Google, CC BY-SA 4.0): 10-12 frases seguidas de un mismo
    hablante. Solo se bajan esas frases (HTTP Range), no los 900 MB de cada zip.
  * 1 entrevista simulada de 2 hablantes armada con frases de OpenSLR 73 (verdad conocida para diarizar).
- referencias_humanas.json: transcripciones hechas por personas que ya existen en las fuentes
  (páginas corregidas/validadas de Wikisource, transcripciones de las descripciones de Commons
  y transcripciones oficiales de OpenSLR 73). Se usan como texto_referencia en la evaluación.

Respeta las APIs de Wikimedia: User-Agent descriptivo y pausas de 1,5-3 s entre solicitudes.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
from PIL import Image
from scipy.signal import resample_poly

BASE = Path(__file__).resolve().parent
RAW = BASE / "datos" / "raw"
SR = 16_000
UA = {"User-Agent": "tarea2-curso-python-up/2026 (github.com/josuesoriavas/python-intermedio; uso academico)"}
FECHA = time.strftime("%Y-%m-%d")

# id, tipo, origen, título del archivo, página (pdf/djvu), descripción corta
DOCUMENTOS = [
    ("doc_001", "impreso", "wikisource", "Tradiciones peruanas - Tomo I (1893).pdf", 35, "Ricardo Palma, «D. Dimas de la Tijereta» (inicio)"),
    ("doc_002", "impreso", "wikisource", "Tradiciones peruanas - Tomo I (1893).pdf", 37, "Ricardo Palma, «D. Dimas de la Tijereta» (p. 31)"),
    ("doc_003", "impreso", "wikisource", "Tradiciones peruanas - Tomo I (1893).pdf", 187, "Ricardo Palma, «Los malditos» (inicio)"),
    ("doc_004", "impreso", "wikisource", "Tradiciones peruanas - Tomo I (1893).pdf", 377, "Ricardo Palma, Tradiciones peruanas (p. 371)"),
    ("doc_005", "impreso", "wikisource", "Historia General del Perú.djvu", 41, "Inca Garcilaso, Historia General del Perú, cap. I"),
    ("doc_006", "impreso", "wikisource", "Historia General del Perú.djvu", 134, "Inca Garcilaso, cap. XV «Origen de los Incas»"),
    ("doc_007", "impreso", "wikisource", "Historia General del Perú.djvu", 229, "Inca Garcilaso, Historia General del Perú"),
    ("doc_008", "impreso", "wikisource", "Ley de Reforma Agraria Peruana.pdf", 2, "Decreto Ley 17716 de Reforma Agraria (1969), arts. 2-3"),
    ("doc_009", "foto", "commons", "Casa de José Santos Chocano en Lima - Placa (izq.).jpg", None, "Placa a José Santos Chocano (1927), Lima"),
    ("doc_010", "foto", "commons", "Placa del Edificio Fénix.jpg", None, "Placa metálica del Edificio Fénix, Lima (brillo fuerte)"),
    ("doc_011", "foto", "commons", "Placa del ex-Círculo Militar del Perú en Lima.jpg", None, "Placa del ex-Círculo Militar del Perú (1937), Lima"),
    ("doc_012", "foto", "commons", "Placa del Palacio de Justicia de Lima.jpg", None, "Placa del Palacio de Justicia de Lima (lejana e inclinada)"),
    ("doc_013", "foto", "commons", "Placa por el centenario de la inmolación de los mártires de Chicago en el Rímac 01.jpg", None, "Placa del Concejo Distrital del Rímac (1986)"),
    ("doc_014", "foto", "commons", "Monumento a Miguel Grau - Miraflores - Placa.jpg", None, "Placa del monumento a Miguel Grau, Miraflores"),
    ("doc_015", "foto", "commons", "Piedra basal andina (placa).JPG", None, "Placa de la Piedra basal andina, Lima (1985)"),
    ("doc_016", "foto", "commons", "Estado General de Miguel Grau.jpg", None, "Estado General de Miguel Grau, documento enmarcado con reflejos"),
    ("doc_017", "manuscrito", "commons", "\"El primer nueva crónica y buen gobierno\" by Felipe Guamán Poma de Ayala, pg 862.png", None, "Guaman Poma (1615), «La borrachera»"),
    ("doc_018", "manuscrito", "commons", "A chaski, 1615.jpg", None, "Guaman Poma (1615), el chasqui"),
    ("doc_019", "manuscrito", "commons", "Arequipa Ascheregen Huaynaputina 1600.jpg", None, "Guaman Poma (1615), Arequipa y el Huaynaputina"),
    ("doc_020", "manuscrito", "commons", "Callao POMA1041v.jpg", None, "Guaman Poma (1615), la villa del Callao"),
    ("doc_021", "manuscrito", "commons", "Cañete - POMA1045v.jpg", None, "Guaman Poma (1615), la villa de Cañete"),
    ("doc_022", "manuscrito", "commons", "Bogotá POMA1005v.jpg", None, "Guaman Poma (1615), capítulo de las ciudades"),
    ("doc_023", "manuscrito", "commons", "Acta de Independencia Peru.jpg", None, "Acta de la Independencia del Perú (1821), original"),
    ("doc_024", "manuscrito", "commons", "Acta de la Indepencia del Perù.jpg", None, "Acta de la Independencia, facsímil fotografiado"),
    ("doc_025", "manuscrito", "commons", "Capitulacón de Ayacucho2.jpg", None, "Capitulación de Ayacucho (1824), página manuscrita"),
]

# Archivos de Commons cuya descripción trae la transcripción humana del texto de la imagen
DESCRIPCION_ES_TRANSCRIPCION = {"doc_009", "doc_010", "doc_011", "doc_020", "doc_021", "doc_022"}

# clip, título en Commons, descripción corta, n.º de hablantes declarado por la fuente (None = no se sabe)
COMMONS_AUDIO = [
    ("clip_001", "Entrevista 1 en la Av. Rivagüero - El Agustino.ogg", "Entrevista en la calle a una vendedora de frutas, El Agustino (2022)"),
    ("clip_002", "Entrevista 2 en la Av. Rivagüero - El Agustino.ogg", "Entrevista en la calle a dos vendedoras de dulces, El Agustino (2022)"),
    ("clip_003", "Entrevista-Aurora Coronado-organización de mujeres indígenas-fiestas patrias.ogg", "Dirigente de una organización de mujeres indígenas en conferencia de prensa (2022)"),
    ("clip_004", "Entrevista 1,.wav", "Entrevista de un estudiante de la UNMSM por Fiestas Patrias (2022)"),
    ("clip_005", "Entrevista 2.wav", "Entrevista de un estudiante de la UNMSM por Fiestas Patrias (2022)"),
    ("clip_006", "Entrevista 3.wav", "Entrevista de un estudiante de la UNMSM por Fiestas Patrias (2022)"),
    ("clip_007", "Entrevista 4.wav", "Entrevista de un estudiante de la UNMSM por Fiestas Patrias (2022)"),
    ("clip_008", "Entrevista en el medio tiempo.opus", "Mini entrevista en el medio tiempo del repechaje Perú-Australia (2022)"),
]
OPENSLR73 = "https://www.openslr.org/resources/73/es_pe_{sexo}.zip"


# ───────────────────────────────────────────────────────── red
def _get(url, rango=None, pausa=1.5):
    cab = dict(UA)
    if rango:
        cab["Range"] = f"bytes={rango[0]}-{rango[1]}"
    for intento in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=180) as r:
                datos = r.read()
            if not rango:
                time.sleep(pausa)
            return datos
        except urllib.error.HTTPError as e:
            if e.code != 429 or intento == 4:
                raise
            time.sleep(60 * (intento + 1))


def api(host, **p):
    p.setdefault("format", "json")
    return json.loads(_get(f"https://{host}/w/api.php?" + urllib.parse.urlencode(p), pausa=2))


def sha1(ruta: Path) -> str:
    return hashlib.sha1(ruta.read_bytes()).hexdigest()


# ───────────────────────────────────────────────────────── documentos
def _url_imagen(ii: dict, pagina: int | None) -> str:
    """Wikimedia pide usar miniaturas de tamaño estándar (https://w.wiki/GHai): 1280 px para páginas
    de PDF/DjVu y 1920 px para fotos grandes; las imágenes chicas se bajan tal cual."""
    sin_query = lambda u: u.split("?")[0].replace("thumb.wikimedia.org", "upload.wikimedia.org")
    if pagina:
        return re.sub(r"page(\d+)-\d+px-", r"page\1-1280px-", sin_query(ii["thumburl"]))
    if ii["width"] <= 1920:
        return sin_query(ii["url"])
    return re.sub(r"/\d+px-", "/1920px-", sin_query(ii["thumburl"]))


def _limpiar_wikitexto(t: str) -> str:
    """Wikitexto de una página de Wikisource -> texto plano tal como aparece en el escaneo."""
    cab = re.search(r"\{\{cp\|([^}]*)\}\}", t)  # cabecera de página: número y título corrido
    cabecera = " ".join(x for x in cab.group(1).split("|") if x.strip()) if cab else ""
    t = re.sub(r"<noinclude>.*?</noinclude>", " ", t, flags=re.S)
    t = re.sub(r"\[\[(?:Archivo|File|Imagen):[^\]]*\]\]", " ", t)
    t = re.sub(r"<section[^>]*/>|<references\s*/>|<ref>.*?</ref>", " ", t, flags=re.S)
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"\{\{[Gg]randeInicial\|([^|}]*)[^}]*\}\}", r"\1", t)
    for _ in range(4):  # plantillas de formato: se queda el primer argumento
        t = re.sub(r"\{\{[^{}|]+\|([^{}|]*)(?:\|[^{}]*)?\}\}", r"\1", t)
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
    t = re.sub(r"'{2,}", "", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", f"{cabecera} {t}").strip()


def _limpiar_descripcion(t: str) -> str:
    """Descripción de Commons -> solo lo que está escrito en la imagen."""
    t = re.sub(r"^Dibujo \d+\. [^\n]*?(?=\d{3,4} \[)", "", t)   # título editorial de la edición digital
    t = re.sub(r"\n\s*\d+ “.*$", "", t, flags=re.S)            # nota al pie del editor
    t = re.sub(r"\[\.\.\.\]", " ", t)                           # omisiones del editor
    # la foliación moderna [1045] sí está escrita (a lápiz) en el escaneo: se queda, sin corchetes
    t = re.sub(r"(\w)1\b", r"\1", t)                           # llamada de nota (gouernador1)
    t = t.replace("[", "").replace("]", "").replace("/", " ").replace("*", " ")
    return re.sub(r"\s+", " ", t.strip(" «»\n")).strip()


def bajar_documentos():
    destino = RAW / "documentos"
    destino.mkdir(parents=True, exist_ok=True)
    filas, refs = [], {}
    for id_, tipo, origen, titulo, pagina, desc in DOCUMENTOS:
        ruta = destino / f"{id_}.jpg"
        kw = {"iiurlparam": f"page{pagina}-1280px"} if pagina else {"iiurlwidth": 1920}
        r = api("commons.wikimedia.org", action="query", titles="File:" + titulo, prop="imageinfo|revisions",
                iiprop="url|extmetadata|size", rvprop="content", rvslots="main", **kw)
        p = next(iter(r["query"]["pages"].values()))
        if "imageinfo" not in p:  # algunos escaneos están subidos solo a Wikisource, no a Commons
            r = api("es.wikisource.org", action="query", titles="Archivo:" + titulo, prop="imageinfo|revisions",
                    iiprop="url|extmetadata|size", rvprop="content", rvslots="main", **kw)
            p = next(iter(r["query"]["pages"].values()))
        ii = p["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        limpio = lambda k: re.sub(r"<[^>]+>|\s+", " ", meta.get(k, {}).get("value", "")).strip()
        if not ruta.exists():
            img = Image.open(io.BytesIO(_get(_url_imagen(ii, pagina), pausa=3))).convert("RGB")
            img.thumbnail((2400, 2400))  # suficiente para OCR y más liviano
            img.save(ruta, quality=92)
        if origen == "wikisource":
            ws = api("es.wikisource.org", action="query", titles=f"Página:{titulo}/{pagina}",
                     prop="revisions|proofread", rvprop="content", rvslots="main")
            wp = next(iter(ws["query"]["pages"].values()))
            nivel = wp["proofread"]["quality"]
            refs[id_] = {"texto": _limpiar_wikitexto(wp["revisions"][0]["slots"]["main"]["*"]),
                         "procedencia": f"Wikisource, página {'validada' if nivel == 4 else 'corregida'} por voluntarios (nivel {nivel})",
                         "url": "https://es.wikisource.org/wiki/" + urllib.parse.quote(f"Página:{titulo}/{pagina}".replace(" ", "_"))}
            fuente_url = refs[id_]["url"]
            licencia = "Dominio público (texto y escaneo)"
        else:
            fuente_url = ii["descriptionurl"]
            licencia = limpio("LicenseShortName")
            if id_ in DESCRIPCION_ES_TRANSCRIPCION:
                wt = p["revisions"][0]["slots"]["main"]["*"]
                m = re.search(r"\{\{es\|(?:1=)?(.*?)\}\}", wt, re.S)
                refs[id_] = {"texto": _limpiar_descripcion(m.group(1)),
                             "procedencia": "Transcripción humana en la descripción del archivo en Commons",
                             "url": fuente_url}
        filas.append({"id": id_, "modalidad": "documento", "tipo": tipo, "archivo": f"datos/raw/documentos/{id_}.jpg",
                      "descripcion": desc, "titulo_original": titulo + (f" (página {pagina})" if pagina else ""),
                      "autor": limpio("Artist")[:150] or "Desconocido", "licencia": licencia, "fuente_url": fuente_url,
                      "acceso": "descargar_datos.py: API de Wikimedia (imageinfo) y guardar como JPEG de 2400 px máx.",
                      "fecha_extraccion": FECHA, "sha1": sha1(ruta)})
        print(id_, tipo, ruta.stat().st_size // 1024, "KB")
    return pd.DataFrame(filas), refs


# ───────────────────────────────────────────────────────── audio
class ZipRemoto(io.RawIOBase):
    """Archivo remoto que se lee por partes (HTTP Range): zipfile solo pide los bytes que necesita."""

    BLOQUE = 1 << 20

    def __init__(self, url):
        self.url, self.pos, self.buf_ini, self.buf = url, 0, 0, b""
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA, method="HEAD"), timeout=60) as r:
            self.size = int(r.headers["Content-Length"])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        fin = self.pos + n
        if not (self.buf_ini <= self.pos and fin <= self.buf_ini + len(self.buf)):
            self.buf_ini = self.pos
            self.buf = _get(self.url, (self.pos, min(self.pos + max(n, self.BLOQUE), self.size) - 1))
        datos = self.buf[self.pos - self.buf_ini:fin - self.buf_ini]
        self.pos += len(datos)
        return datos


def _a_16k(contenido: bytes) -> np.ndarray:
    x, sr = sf.read(io.BytesIO(contenido), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype("float32")
    return x


def bajar_audio_commons():
    destino = RAW / "audio"
    destino.mkdir(parents=True, exist_ok=True)
    filas = []
    for id_, titulo, desc in COMMONS_AUDIO:
        r = api("commons.wikimedia.org", action="query", titles="File:" + titulo, prop="imageinfo", iiprop="url|extmetadata")
        ii = next(iter(r["query"]["pages"].values()))["imageinfo"][0]
        meta = ii["extmetadata"]
        ext = Path(titulo).suffix.lower()
        original = destino / "original" / f"{id_}{ext}"
        original.parent.mkdir(exist_ok=True)
        if not original.exists():
            original.write_bytes(_get(ii["url"], pausa=3))
        filas.append({"id": id_, "modalidad": "audio", "fuente": "Wikimedia Commons", "archivo_original": f"datos/raw/audio/original/{id_}{ext}",
                      "descripcion": desc, "titulo_original": titulo,
                      "autor": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip(),
                      "licencia": meta.get("LicenseShortName", {}).get("value", ""), "fuente_url": ii["descriptionurl"],
                      "acceso": "descargar_datos.py: API de Wikimedia (imageinfo) y archivo original",
                      "fecha_extraccion": FECHA})
        print(id_, original.stat().st_size // 1024, "KB")
    return pd.DataFrame(filas)


def bajar_openslr73(n_por_sexo=7, frases=11, semilla=2026):
    """Clips de lectura: `frases` frases seguidas de un mismo hablante, con 0,6 s de pausa entre frases.

    Además arma una entrevista simulada (dos hablantes que se turnan) para medir la diarización.
    """
    from concurrent.futures import ThreadPoolExecutor
    destino = RAW / "audio"
    destino.mkdir(parents=True, exist_ok=True)
    pausa = np.zeros(int(0.6 * SR), dtype=np.float32)
    filas, refs, turnos, tareas = [], {}, {}, []
    n = 9  # clip_009 en adelante
    for sexo in ["female", "male"]:
        url = OPENSLR73.format(sexo=sexo)
        z = zipfile.ZipFile(ZipRemoto(url))
        lineas = z.read("line_index.tsv").decode("utf-8").strip().splitlines()
        tabla = pd.DataFrame([l.split("	") for l in lineas], columns=["id", "texto"]).sort_values("id")
        tabla["hablante"] = tabla["id"].str.rsplit("_", n=1).str[0]
        cuenta = tabla["hablante"].value_counts()
        hablantes = sorted(cuenta[cuenta >= frases + 4].index)
        rng = random.Random(semilla)
        rng.shuffle(hablantes)
        for h in hablantes[:n_por_sexo]:
            sel = tabla[tabla["hablante"] == h].head(frases)
            id_ = f"clip_{n:03d}"
            tareas.append((url, list(sel["id"]), destino / f"{id_}.wav"))
            refs[id_] = {"texto": " ".join(t.strip() for t in sel["texto"]), "procedencia": "Transcripción oficial de OpenSLR 73 (line_index.tsv)",
                         "url": url, "frases": sel["id"].tolist()}
            filas.append({"id": id_, "modalidad": "audio", "fuente": "OpenSLR 73", "archivo_original": f"datos/raw/audio/{id_}.wav",
                          "descripcion": f"Lectura de {frases} frases, hablante {'mujer' if sexo == 'female' else 'hombre'} ({h})",
                          "titulo_original": f"es_pe_{sexo}.zip: " + ", ".join(sel["id"]), "autor": "Google (Guevara-Rukoz et al., 2020)",
                          "licencia": "CC BY-SA 4.0", "fuente_url": "https://www.openslr.org/73/",
                          "acceso": "descargar_datos.py: lectura parcial del zip con HTTP Range", "fecha_extraccion": FECHA})
            n += 1
        # el siguiente hablante sirve para la entrevista simulada
        h = hablantes[n_por_sexo]
        turnos[sexo] = (url, [(f.id, f.texto.strip()) for f in tabla[tabla["hablante"] == h].head(8).itertuples()])

    def leer(url, ids):  # cada hilo abre su propio zip remoto (el lector no es seguro entre hilos)
        z = zipfile.ZipFile(ZipRemoto(url))
        return [_a_16k(z.read(f"{i}.wav")) for i in ids]

    def clip(url, ids, ruta):
        if not ruta.exists():
            sf.write(ruta, np.concatenate([x for a in leer(url, ids) for x in (a, pausa)]), SR)
        print(ruta.stem, f"{sf.info(ruta).duration:.0f} s", flush=True)

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda t: clip(*t), tareas))
        sim = {s: ex.submit(leer, u, [i for i, _ in fr]) for s, (u, fr) in turnos.items()}
        turnos = {s: [(x, t, i) for x, (i, t) in zip(sim[s].result(), turnos[s][1])] for s in turnos}
    # entrevista simulada: turnos alternados mujer/hombre
    audio, verdad, t = [], [], 0.0
    for (xa, ta, ia), (xb, tb, ib) in zip(turnos["female"], turnos["male"]):
        for x, texto, quien in [(xa, ta, "H1"), (xb, tb, "H2")]:
            verdad.append({"inicio": round(t, 2), "fin": round(t + len(x) / SR, 2), "hablante": quien, "texto": texto})
            audio += [x, pausa]
            t += (len(x) + len(pausa)) / SR
    id_ = f"clip_{n:03d}"
    sf.write(destino / f"{id_}.wav", np.concatenate(audio), SR)
    pd.DataFrame(verdad).to_csv(destino / f"{id_}_verdad_hablantes.csv", index=False)
    refs[id_] = {"texto": " ".join(v["texto"] for v in verdad), "procedencia": "Transcripción oficial de OpenSLR 73 (line_index.tsv)",
                 "url": "https://www.openslr.org/73/", "hablantes": 2}
    filas.append({"id": id_, "modalidad": "audio", "fuente": "OpenSLR 73", "archivo_original": f"datos/raw/audio/{id_}.wav",
                  "descripcion": "Entrevista simulada: 2 hablantes (mujer y hombre) se turnan 16 frases",
                  "titulo_original": "es_pe_female.zip + es_pe_male.zip: " + ", ".join(i for p in zip(turnos["female"], turnos["male"]) for _, _, i in p),
                  "autor": "Google (Guevara-Rukoz et al., 2020)", "licencia": "CC BY-SA 4.0", "fuente_url": "https://www.openslr.org/73/",
                  "acceso": "descargar_datos.py: frases de OpenSLR 73 concatenadas con 0,6 s de pausa", "fecha_extraccion": FECHA})
    print(id_, f"entrevista simulada {t:.0f} s")
    return pd.DataFrame(filas), refs


def _por_partes(nombre, funcion):
    """Guarda el resultado de cada parte para poder reanudar si un servidor corta la descarga (HTTP 429)."""
    tabla, refs = RAW / f"_parte_{nombre}.csv", RAW / f"_parte_{nombre}.json"
    if tabla.exists():
        return pd.read_csv(tabla), json.loads(refs.read_text(encoding="utf-8"))
    salida = funcion()
    df, r = salida if isinstance(salida, tuple) else (salida, {})
    df.to_csv(tabla, index=False)
    refs.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
    return df, r


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    aud_o, refs_aud = _por_partes("openslr73", bajar_openslr73)
    aud_c, _ = _por_partes("commons_audio", bajar_audio_commons)
    docs, refs_docs = _por_partes("documentos", bajar_documentos)
    pd.concat([docs, aud_c, aud_o], ignore_index=True).to_csv(RAW / "inventario_fuentes.csv", index=False)
    (RAW / "referencias_humanas.json").write_text(json.dumps({**refs_docs, **refs_aud}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(docs)} documentos, {len(aud_c) + len(aud_o)} clips; referencias humanas: {len(refs_docs)} docs, {len(refs_aud)} clips")
