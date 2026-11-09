"""Exporta la conversación de Claude Code (archivo .jsonl de la sesión) a Markdown legible para evidencias_ia/.

    uv run python scripts/exportar_conversacion.py RUTA/sesion.jsonl --salida evidencias_ia

Incluye, en orden: los mensajes del usuario, el texto de las respuestas del asistente, cada llamada a herramienta
(nombre y argumentos) y un extracto de cada resultado. Omite el razonamiento interno del modelo y los recordatorios
automáticos del sistema. Oculta correos, tokens y claves (patrones comunes) antes de escribir.

Escribe <salida>/conversacion_completa.md y, para facilitar la revisión, la misma conversación partida por fases en
<salida>/{mcp,skills,integracion,evaluacion}/conversacion_*.md (las fases se cortan en el primer archivo de cada parte).
"""
import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

CORREO = re.compile(r"(?<![\\\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b")   # no toma «\n@mcp.tool»
PUBLICOS = ("noreply@",)   # direcciones genéricas que no identifican a nadie (p. ej. la firma Co-Authored-By)
SECRETOS = [
    (CORREO, lambda m: m[0] if m[0].startswith(PUBLICOS) else "[correo oculto]"),
    # carpeta personal del usuario en rutas de Windows, Git Bash y nombres de proyecto de Claude Code
    (re.compile(r"(?i)\b([A-Za-z]:[\\/]+Users[\\/]+)(?!<usuario>)[^\\/\s\"'<>]+"), r"\1<usuario>"),
    (re.compile(r"(?i)(/[a-z]/Users/)(?!<usuario>)[^/\s\"'<>]+"), r"\1<usuario>"),
    (re.compile(r"(?i)\b([A-Za-z]--Users-)(?!<usuario>)[^-\s\"'<>\\/]+"), r"\1<usuario>"),
    (re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|sk-ant-[A-Za-z0-9_-]{16,})"), "[clave oculta]"),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"), "[token oculto]"),
    (re.compile(r"(?i)(api[_-]?key|token|password|contraseña)\s*[:=]\s*\S+"), r"\1=[oculto]"),
]
# Primer archivo escrito en cada fase (cortes de la conversación)
FASES = [("mcp", r"tarea_4[\\/]+mcp[\\/]+server\.py"),
         ("skills", r"limpiando-enaho[\\/]+scripts[\\/]+estimacion\.py"),
         ("integracion", r"informes[\\/]+pregunta_investigacion\.md"),
         ("evaluacion", r"evaluacion[\\/]+respuestas_esperadas\.py")]
MAX_ENTRADA, MAX_RESULTADO = 2500, 1500


def ocultar(texto, reglas=()):
    for patron, reemplazo in [*SECRETOS, *reglas]:
        texto = patron.sub(reemplazo, texto)
    return texto


def reglas_personales(crudo):
    """Reglas extra sacadas del propio registro, sin escribir datos personales en este script:
    - la parte local de cada correo (incluidos los de los avisos del sistema, que no se exportan), también cuando aparece
      sin el dominio dentro de un comando: se oculta toda palabra que empiece con sus primeros 8 caracteres;
    - el nombre de usuario de Windows de las rutas C:\\Users\\<nombre>, como palabra suelta (p. ej. el dueño en `ls -la`)."""
    correos = {m[0] for m in CORREO.finditer(crudo) if not m[0].startswith(PUBLICOS) and len(m[0].split("@")[0]) >= 6}
    locales, dominios = {c.split("@")[0] for c in correos}, {c.split("@")[1] for c in correos}
    reglas = [(re.compile(re.escape(t[:8]) + r"[\w.+-]*", re.IGNORECASE), "[correo oculto]")
              for t in sorted(locales, key=len, reverse=True)]
    # restos abreviados del tipo «abcd…@dominio» (p. ej. en la salida de un conteo de correos)
    reglas += [(re.compile(r"[\w.+\-…]*@" + re.escape(d) + r"\b", re.IGNORECASE), "[correo oculto]") for d in dominios]
    usuarios = {m[1] for m in re.finditer(r"(?i)\b[A-Za-z]:[\\/]+Users[\\/]+([\w.-]+)", crudo)}
    reglas += [(re.compile(rf"\b{re.escape(u)}\b"), "<usuario>") for u in usuarios - {"Public", "Default", "usuario"}]
    return reglas


def sin_recordatorios(texto):
    texto = re.sub(r"<system-reminder>.*?</system-reminder>", "", texto, flags=re.DOTALL)
    return texto.strip()


def recortar(texto, n):
    return texto if len(texto) <= n else texto[:n] + f"\n… [recortado: {len(texto) - n:,} caracteres más]"


def hora(ts):
    try:   # hora de Perú (UTC-5)
        return (datetime.fromisoformat(ts.replace("Z", "+00:00")) - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")
    except (AttributeError, ValueError):
        return ""


def bloques(evento):
    contenido = evento.get("message", {}).get("content", [])
    if isinstance(contenido, str):
        return [{"type": "text", "text": contenido}]
    return contenido


def convertir(ruta):
    """Devuelve una lista de (fase, markdown) en orden."""
    partes, fase = [], "planificacion"
    crudo = Path(ruta).read_text(encoding="utf-8")
    reglas = reglas_personales(crudo)
    for linea in crudo.splitlines():
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            continue
        tipo, cuando = e.get("type"), hora(e.get("timestamp", ""))
        if tipo not in ("user", "assistant") or e.get("isMeta"):
            continue
        for b in bloques(e):
            t = b.get("type")
            if tipo == "user" and t == "text":
                texto = sin_recordatorios(b.get("text", ""))
                if texto:
                    partes.append((fase, f"\n---\n\n### 🧑 Usuario · {cuando}\n\n{recortar(texto, 60_000)}\n"))
            elif tipo == "user" and t == "tool_result":
                c = b.get("content")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "[imagen]") if x.get("type") == "text" else "[imagen]" for x in c)
                c = sin_recordatorios(str(c or ""))
                marca = "⚠️ error" if b.get("is_error") else "resultado"
                partes.append((fase, f"\n<details><summary>{marca}</summary>\n\n```text\n"
                                     f"{recortar(c, MAX_RESULTADO)}\n```\n</details>\n"))
            elif tipo == "assistant" and t == "text" and b.get("text", "").strip():
                partes.append((fase, f"\n### 🤖 Claude · {cuando}\n\n{b['text'].strip()}\n"))
            elif tipo == "assistant" and t == "tool_use":
                entrada = json.dumps(b.get("input", {}), ensure_ascii=False, indent=1)
                for nombre, patron in FASES:
                    if re.search(patron, entrada) and [n for n, _ in FASES].index(nombre) > \
                            ([n for n, _ in FASES].index(fase) if fase in [n for n, _ in FASES] else -1):
                        fase = nombre
                        break
                partes.append((fase, f"\n**🔧 {b.get('name')}**\n\n```json\n{recortar(entrada, MAX_ENTRADA)}\n```\n"))
    return [(f, ocultar(md, reglas)) for f, md in partes]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("jsonl")
    p.add_argument("--salida", default="evidencias_ia")
    a = p.parse_args()
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    partes = convertir(a.jsonl)
    encabezado = ("# Conversación de desarrollo con Claude Code (Tarea 4)\n\n"
                  f"Exportada de `{Path(a.jsonl).name}` con `scripts/exportar_conversacion.py`. Incluye los mensajes "
                  "del usuario, las respuestas del asistente, cada llamada a herramienta con sus argumentos y un "
                  "extracto de su resultado. Se omitió el razonamiento interno y los recordatorios automáticos; se "
                  "ocultaron correos y patrones de claves o tokens. Horas en Perú (UTC-5).\n")
    (salida / "conversacion_completa.md").write_text(encabezado + "".join(md for _, md in partes), encoding="utf-8")
    titulos = {"planificacion": "Planificación y revisión inicial", "mcp": "Desarrollo del servidor MCP y pruebas",
               "skills": "Desarrollo de las Skills de ENAHO", "integracion": "Integración del agente e informe",
               "evaluacion": "Evaluación A/B, correcciones y documentación"}
    for fase, titulo in titulos.items():
        carpeta = salida / ("." if fase == "planificacion" else fase)
        carpeta.mkdir(parents=True, exist_ok=True)
        texto = "".join(md for f, md in partes if f == fase)
        nombre = "conversacion_0_planificacion.md" if fase == "planificacion" else f"conversacion_{fase}.md"
        (carpeta / nombre).write_text(f"# {titulo}\n\nParte de `conversacion_completa.md` (fase «{fase}»).\n"
                                      + texto, encoding="utf-8")
        print(f"{fase:<14} {len(texto):>9,} caracteres -> {carpeta / nombre}")


if __name__ == "__main__":
    main()
