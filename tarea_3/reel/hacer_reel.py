"""Reel vertical 1080x1920: guion.json -> narración -> subtítulos -> video con gráficos y música.

Reutiliza el pipeline de la Sesión 15 (clase/reel.py: narración por escena, control de calidad y
subtítulos con Whisper) y le agrega lo que pide la Tarea 3:
  - un gráfico o captura del dashboard por escena, con un zoom lento (efecto Ken Burns),
  - música de fondo (recursos/musica_fondo.wav, sintetizada en graficos_reel.py) por debajo de la voz,
  - aviso de voz sintética, fuente de los datos y créditos en pantalla.

La narración usa una voz masculina genérica de Windows (Microsoft Pablo, es-ES) mediante
voz_windows.ps1: no clona a ninguna persona ni necesita descargar modelos. Con --voz se puede
volver al flujo de clase (Qwen3-TTS clonando una grabación propia).

Uso (desde tarea_3/reel, con el entorno de la sesión 15):
    .venv/Scripts/python hacer_reel.py                      # voz genérica de Windows
    .venv/Scripts/python hacer_reel.py --voz mi_voz.m4a     # voz propia clonada con Qwen3-TTS
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")   # Whisper ya está en caché; no consultar Hugging Face
import soundfile as sf
from PIL import Image, ImageDraw

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI / "clase"))
import reel as R  # noqa: E402  (pipeline de la sesión 15)

R.FUENTES = AQUI / "recursos" / "fuentes"
ANCHO, ALTO, FPS, MARGEN = R.ANCHO, R.ALTO, R.FPS, R.MARGEN
FUENTE_DATOS = "NOAA CPC (ERSSTv5, OISST) y FAOSTAT (FAO)"
CREDITOS = ("Voz: Microsoft Pablo (texto a voz de Windows) · Música: pista sintetizada con código para este reel "
            "(sin derechos de terceros) · Gráficos y dashboard: elaboración propia")
AVISO = "VOZ SINTÉTICA GENERADA POR COMPUTADORA"
Y_IMG, ALTO_IMG, Y_SUB = 720, 600, 1400


class VozWindows:
    """Voz genérica masculina de Windows (OneCore). Misma interfaz que reel.Voz: decir(frases) -> lista de audios."""

    def __init__(self, nombre="Pablo", velocidad="+0%"):
        self.nombre, self.velocidad, self.sr = nombre, velocidad, 16000
        self.texto_ref = f"(voz del sistema: Microsoft {nombre})"
        self.carpeta = Path(tempfile.mkdtemp())

    def decir(self, frases, estilos=None):
        wavs = []
        for k, f in enumerate(frases):
            salida = self.carpeta / f"escena_{k}_{time.time_ns()}.wav"
            subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            str(AQUI / "voz_windows.ps1"), "-Texto", f, "-Salida", str(salida),
                            "-Voz", self.nombre, "-Velocidad", self.velocidad], check=True, capture_output=True)
            audio, self.sr = sf.read(salida, dtype="float32")
            wavs.append(audio if audio.ndim == 1 else audio.mean(axis=1))
        return wavs


def base(titulo, autor):
    img = Image.new("RGB", (ANCHO, ALTO), R.FONDO)
    d = ImageDraw.Draw(img)
    d.text((MARGEN, 250), titulo.upper(), font=R._fuente("PublicSans", 40, 800), fill=R.ACENTO)
    aviso = AVISO
    f = R._fuente("PublicSans", 28, 700)
    x1 = MARGEN + d.textlength(aviso, font=f) + 36
    d.rounded_rectangle((MARGEN, 315, x1, 365), radius=25, outline=R.SUAVE, width=2)
    d.text((MARGEN + 18, 340), aviso, font=f, fill=R.SUAVE, anchor="lm")
    pie, chico = R._fuente("PublicSans", 32, 600), R._fuente("PublicSans", 26, 500)
    y = 1580
    for linea in R._envolver(d, f"Fuente: {FUENTE_DATOS}", pie, ANCHO - 2 * MARGEN):
        d.text((MARGEN, y), linea, font=pie, fill=R.TEXTO)
        y += 44
    for linea in R._envolver(d, f"{autor} · {CREDITOS}", chico, ANCHO - 2 * MARGEN):
        d.text((MARGEN, y + 10), linea, font=chico, fill=R.SUAVE)
        y += 36
    return img


def capa_texto(e):
    """Cifra grande (si hay) y etiqueta, entre el aviso de IA y el gráfico."""
    capa = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    ancho = ANCHO - 2 * MARGEN
    y = 430
    if e.get("cifra"):
        f = R._ajustar(d, e["cifra"], "Oswald", 700, ancho, 170, 90)
        y += -d.textbbox((0, 0), e["cifra"], font=f, anchor="ls")[1]
        d.text((MARGEN, y), e["cifra"], font=f, fill=R.ACENTO, anchor="ls")
        y += 30
        fe, color = R._fuente("PublicSans", 50, 600), R.TEXTO
    else:
        fe, color = R._fuente("Oswald", 84, 600), R.TEXTO
        y += 40
    for linea in R._envolver(d, e["etiqueta"], fe, ancho)[:2]:
        y += fe.size
        d.text((MARGEN, y), linea, font=fe, fill=color, anchor="ls")
        y += int(fe.size * 0.35)
    return capa


def cargar_imagen(ruta):
    """Ajusta el gráfico (o la captura) a 900 x 600 con esquinas redondeadas."""
    im = Image.open(AQUI / ruta).convert("RGB")
    w, h = ANCHO - 2 * MARGEN, ALTO_IMG
    escala = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * escala), int(im.height * escala)), Image.LANCZOS)
    im = im.crop((0, 0, w, h)) if im.height > h else im.crop(((im.width - w) // 2, 0, (im.width - w) // 2 + w, h))
    mascara = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, w, h), radius=24, fill=255)
    im.putalpha(mascara)
    return im


def cuadro(fondo, textos, imagenes, narr, t, bloques, fsub):
    img = fondo.copy()
    i = max([k for k, (ini, _) in enumerate(narr.escenas) if ini - R.PAUSA <= t] or [0])
    ini, fin = narr.escenas[i]
    a = min(1.0, max(0.0, (t - ini + R.PAUSA) / 0.35))   # entrada suave de la escena
    # gráfico con zoom lento (1.00 -> 1.05) durante la escena
    im = imagenes[i]
    z = 1 + 0.05 * min(1, max(0, (t - ini) / max(fin - ini, 0.1)))
    if z > 1.001:
        w, h = im.size
        g = im.resize((int(w * z), int(h * z)), Image.BILINEAR)
        dx, dy = (g.width - w) // 2, (g.height - h) // 2
        im = g.crop((dx, dy, dx + w, dy + h))
        im.putalpha(imagenes[i].getchannel("A"))
    if a < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    img.paste(im, (MARGEN, Y_IMG + int(30 * (1 - a))), im)
    capa = textos[i]
    if a < 1:
        capa = capa.copy()
        capa.putalpha(capa.getchannel("A").point(lambda v: int(v * a)))
    img.paste(capa, (0, int(30 * (1 - a))), capa)

    d = ImageDraw.Draw(img)
    d.rounded_rectangle((MARGEN, 180, ANCHO - MARGEN, 188), radius=4, fill=R.CAJA)
    d.rounded_rectangle((MARGEN, 180, MARGEN + (ANCHO - 2 * MARGEN) * t / narr.duracion, 188), radius=4, fill=R.ACENTO)
    b = next((b for b in bloques if b[0][0] - 0.1 <= t <= b[-1][1] + 0.25), None)
    if b:
        texto = " ".join(p[2] for p in b)
        w = d.textlength(texto, font=fsub)
        x = (ANCHO - w) / 2
        d.rounded_rectangle((x - 36, Y_SUB - 26, x + w + 36, Y_SUB + fsub.size + 34), radius=28, fill=R.CAJA)
        for p_ini, p_fin, palabra in b:
            d.text((x, Y_SUB), palabra, font=fsub, fill=R.ACENTO if p_ini <= t <= p_fin + 0.05 else R.TEXTO)
            x += d.textlength(palabra + " ", font=fsub)
    return img


def video(guion, narr, ruta, autor, musica, vol_musica=0.10):
    ruta = Path(ruta)
    wav = ruta.with_suffix(".wav")
    sf.write(wav, narr.audio, narr.sr)
    fondo = base(guion["titulo"], autor)
    textos = [capa_texto(e) for e in guion["escenas"]]
    imagenes = [cargar_imagen(e["imagen"]) for e in guion["escenas"]]
    bloques = R._bloques(narr.palabras)
    fsub = R._fuente("PublicSans", 60, 800)
    filtro = (f"[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[voz];"
              f"[2:a]volume={vol_musica},afade=t=out:st={max(narr.duracion - 2, 0):.2f}:d=2,aresample=48000[mus];"
              f"[voz][mus]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [R.FFMPEG, "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ANCHO}x{ALTO}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-i", str(musica),
           "-filter_complex", filtro, "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(ruta)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(int(narr.duracion * FPS)):
        proc.stdin.write(cuadro(fondo, textos, imagenes, narr, k / FPS, bloques, fsub).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    cuadro(fondo, textos, imagenes, narr, narr.escenas[0][0] + 1.5, bloques, fsub).convert("RGB").save(AQUI / "portada.png")
    return ruta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voz", help="grabación propia de 15 a 25 s para clonar con Qwen3-TTS (si se omite: voz de Windows)")
    ap.add_argument("--voz-sistema", default="Pablo", help="voz de Windows OneCore (por defecto Microsoft Pablo, es-ES)")
    ap.add_argument("--ritmo", default="+0%", help="velocidad SSML de la voz de Windows, p. ej. +8%%")
    ap.add_argument("--autor", default="josuesoriavas")
    ap.add_argument("--tts", default="Qwen/Qwen3-TTS-12Hz-0.6B-Base")
    ap.add_argument("--asr", default="small", help="modelo de faster-whisper (small ya está en caché; large-v3-turbo es mejor)")
    ap.add_argument("--velocidad", type=float, default=1.0)
    args = ap.parse_args()
    R.ASR = args.asr
    t0 = time.time()

    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    if args.voz:
        global AVISO, CREDITOS
        AVISO = "VOZ GENERADA CON IA A PARTIR DE MI VOZ"
        CREDITOS = CREDITOS.replace("Microsoft Pablo (texto a voz de Windows)", "Qwen3-TTS (clon de mi voz)")
        voz = R.Voz(args.voz, modelo=args.tts)
        args.tts_usado = args.tts
    else:
        voz = VozWindows(args.voz_sistema, args.ritmo)
        args.tts_usado = f"Windows OneCore: Microsoft {args.voz_sistema}"
    R._reloj(f"voz lista {voz.texto_ref}", t0)
    narr = R.narrar(voz, guion, velocidad=args.velocidad)
    R._reloj(f"narración lista: {narr.duracion:.1f} s; WER por escena: {[round(e['wer'], 2) for e in guion['escenas']]}", t0)
    R.subtitulos(narr, guion)
    R.a_srt(narr, AQUI / "subtitulos.srt")
    R._reloj("subtítulos listos", t0)
    video(guion, narr, AQUI / "reel.mp4", args.autor, AQUI / "recursos" / "musica_fondo.wav")
    R._reloj("reel.mp4 listo", t0)
    control = {"duracion_s": round(narr.duracion, 1), "texto_referencia": voz.texto_ref,
               "wer_por_escena": [round(e["wer"], 3) for e in guion["escenas"]], "tts": args.tts_usado, "asr": args.asr}
    (AQUI / "control_calidad.json").write_text(json.dumps(control, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
