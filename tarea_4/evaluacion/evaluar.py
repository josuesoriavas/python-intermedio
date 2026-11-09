"""Experimento A/B: las mismas 10 preguntas sin y con el MCP y las Skills, cada una en una sesión independiente.

    uv run python evaluacion/evaluar.py                       # modos A y B, modelo sonnet, 3 sesiones en paralelo
    uv run python evaluacion/evaluar.py --modos A --ids B1 E1 # un subconjunto
    uv run python evaluacion/evaluar.py --solo-calificar      # recalifica desde las trazas guardadas, sin llamar a Claude

Modo A (sin MCP ni Skills): `claude -p` en una carpeta temporal VACÍA fuera del repositorio, con `--tools ""` (ninguna
    herramienta: ni archivos, ni terminal, ni web, ni skills) y `--strict-mcp-config` sin servidores. No puede ver
    preguntas.csv ni ninguna salida del proyecto: responde solo con lo que sabe el modelo.
Modo B (con MCP y Skills): copia limpia del proyecto en una carpeta temporal fuera del repositorio, SIN evaluacion/,
    informes/, salidas/, figuras/, mapas/ ni evidencias_ia/ (no hay respuestas calculadas que leer: cada sesión debe
    limpiar la ENAHO o consultar el BCRP). Servidor `bcrp` por `--mcp-config`; herramientas `--tools
    "Skill,Bash,Read,Glob,Grep"` con permiso solo para mcp__bcrp, Skill, Bash(uv run:*), Read, Glob y Grep. Sin web.
Ambos: mismo modelo, misma instrucción de sistema, misma salida estructurada (--json-schema), --no-session-persistence.

Escribe evaluacion/resultados.csv y las trazas completas en evidencias_ia/evaluacion/trazas/.
"""
import argparse
import json
import math
import re
import shutil
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parent
sys.path.insert(0, str(PROYECTO / "scripts"))
from ejecutar_agente import ejecutar  # noqa: E402
from resumir_traza import leer, resumir  # noqa: E402

TRAZAS = PROYECTO / "evidencias_ia" / "evaluacion" / "trazas"
COPIAR_B = [".mcp.json", "pyproject.toml", "uv.lock", ".python-version", "mcp", ".claude/skills", "datos"]
ESQUEMA = {"type": "object", "required": ["valor", "respuesta", "fuente"],
           "properties": {"valor": {"type": ["number", "null"]}, "valor_2": {"type": ["number", "null"]},
                          "respuesta": {"type": "string"}, "fuente": {"type": "string"}}}
INSTRUCCION = (
    "Responde en español. En «valor» pon la cifra principal que pide la pregunta, en la unidad pedida (solo el "
    "número). Si la pregunta pide dos cifras, la segunda va en «valor_2». En «respuesta» da la respuesta completa en "
    "1 a 3 frases, con los nombres, meses o la interpretación que pida la pregunta. En «fuente» di de dónde sale cada "
    "cifra (código de serie, archivo o herramienta). Si no puedes saberlo con certeza, pon null: no estimes ni inventes.")
MODOS = {
    "A": ["--tools", "", "--strict-mcp-config"],
    "B": ["--tools", "Skill,Bash,Read,Glob,Grep", "--strict-mcp-config", "--mcp-config", ".mcp.json",
          "--allowedTools", "mcp__bcrp,Skill,Bash(uv run:*),Read,Glob,Grep"],
}
CAUSAL = re.compile(r"\b(caus[óoa]\w*|provoc\w*|gener[óo] (la|más) pobreza|explica(n|ría)? (la|el nivel de) pobreza|"
                    r"debido a la inflaci\w*|por culpa de)\b", re.IGNORECASE)


def preparar_carpeta(modo, base):
    destino = Path(tempfile.mkdtemp(prefix=f"eval_{modo}_", dir=base))
    if modo == "B":
        for rel in COPIAR_B:
            origen = PROYECTO / rel
            if origen.is_dir():
                shutil.copytree(origen, destino / rel, ignore=shutil.ignore_patterns("__pycache__", "*.parquet"))
            else:
                (destino / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origen, destino / rel)
    return destino


def correr(q, modo, modelo, base):
    carpeta = preparar_carpeta(modo, base)
    env = {"UV_PROJECT_ENVIRONMENT": str(PROYECTO / ".venv")} if modo == "B" else None
    r = ejecutar(q.pregunta, modo, TRAZAS / f"{modo}_{q.id}", modelo=modelo, cwd=carpeta, sistema=INSTRUCCION,
                 esquema=ESQUEMA, flags=MODOS[modo], env=env, timeout=1200)
    shutil.rmtree(carpeta, ignore_errors=True)
    return r


def herramientas(r):
    usadas = []
    for c in r["llamadas"]:
        h = c["herramienta"]
        if h == "Skill":
            h = f"Skill:{c['entrada'].get('skill')}"
        elif h == "Bash":
            m = re.search(r"skills/([\w-]+)/scripts/(\w+\.py)", c["entrada"].get("command", ""))
            h = f"Bash:{m[1]}/{m[2]}" if m else "Bash"
        elif h == "StructuredOutput":
            continue
        usadas.append(h.replace("mcp__bcrp__", "mcp:"))
    return usadas


def calificar(q, so, texto):
    """Devuelve (resultado, detalle). Tolerancias definidas en preguntas.csv antes del experimento."""
    if not so:
        return "error", "sin salida estructurada (falla o tiempo agotado)"
    v, v2 = so.get("valor"), so.get("valor_2")
    dos = not (isinstance(q.valor_esperado_2, float) and math.isnan(q.valor_esperado_2))
    if v is None and (not dos or v2 is None):
        return "no contesta", "valor null: el agente reconoce que no puede saberlo"
    fallas = []
    if v is None or abs(v - q.valor_esperado) > q.tolerancia:
        fallas.append(f"valor {v} vs {q.valor_esperado} ± {q.tolerancia}")
    if dos and (v2 is None or abs(v2 - q.valor_esperado_2) > q.tolerancia_2):
        fallas.append(f"valor_2 {v2} vs {q.valor_esperado_2} ± {q.tolerancia_2}")
    t = (texto or "").lower()
    if q.id == "E3" and "cajamarca" not in t:
        fallas.append("no nombra a Cajamarca")
    if q.id == "C2" and not ("feb" in t and "2023" in t):
        fallas.append("no da el mes del pico (febrero de 2023)")
    if q.tipo == "combinada" and CAUSAL.search(t) and not re.search(r"no (implica|demuestra|prueba|establece|"
                                                                     r"permite (afirmar|concluir))", t):
        fallas.append("interpretación causal")
    return ("correcta", "dentro de tolerancia") if not fallas else ("incorrecta", "; ".join(fallas))


def salida_estructurada(r):
    """structured_output del evento final o, si no viene, el JSON que el modelo dejó como texto de resultado."""
    if r.get("structured_output"):
        return r["structured_output"]
    texto = (r.get("respuesta") or "").strip()
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    try:
        return json.loads(m[0]) if m else {}
    except json.JSONDecodeError:
        return {}


def fila(q, modo, r):
    so = salida_estructurada(r)
    texto = so.get("respuesta") or r.get("respuesta") or ""
    resultado, detalle = calificar(q, so, texto)
    usadas = herramientas(r)
    return {"id": q.id, "tipo": q.tipo, "modo": modo, "pregunta": q.pregunta,
            "respuesta_esperada": f"{q.valor_esperado:g}" + ("" if math.isnan(q.valor_esperado_2) else
                                                            f" | {q.valor_esperado_2:g}") + f" ({q.unidad})",
            "valor": so.get("valor"), "valor_2": so.get("valor_2"), "respuesta_generada": texto,
            "fuente_declarada": so.get("fuente", ""), "herramientas_usadas": " ".join(dict.fromkeys(usadas)),
            "n_llamadas": len(usadas), "skills": " ".join(sorted({u[6:] for u in usadas if u.startswith("Skill:")})),
            "mcp": " ".join(sorted({u for u in usadas if u.startswith("mcp:")})),
            "segundos": r.get("segundos_reloj"), "turnos": r.get("turnos"), "costo_usd": r.get("costo_usd"),
            "resultado": resultado, "detalle": detalle,
            "errores_herramientas": len(r.get("errores", [])), "modelo": r.get("modelo")}


def revisar(df):
    """Aplica evaluacion/revision_manual.csv (revisión humana de las respuestas combinadas). Conserva la calificación
    automática en `resultado_automatico`; `resultado` queda con la revisada y `revision_manual` con el motivo."""
    df = df.copy()
    df["resultado_automatico"] = df["resultado"]
    df["revision_manual"] = ""
    archivo = AQUI / "revision_manual.csv"
    if archivo.exists():
        rev = pd.read_csv(archivo).set_index(["id", "modo"])
        for i, r in df.iterrows():
            if (r.id, r.modo) in rev.index:
                df.at[i, "resultado"] = rev.loc[(r.id, r.modo), "resultado_revisado"]
                df.at[i, "revision_manual"] = rev.loc[(r.id, r.modo), "motivo"]
    return df


def resumen_desde_traza(modo, qid):
    jsonl = TRAZAS / f"{modo}_{qid}.jsonl"
    r = resumir(leer(jsonl))
    for linea in jsonl.read_text(encoding="utf-8").splitlines():
        if linea.startswith('{"type":"result"'):
            e = json.loads(linea)
            r["structured_output"] = e.get("structured_output")
            r["segundos_reloj"] = round(e.get("duration_ms", 0) / 1000, 1)
    md = jsonl.with_suffix(".md").read_text(encoding="utf-8") if jsonl.with_suffix(".md").exists() else ""
    m = re.search(r"([\d.]+) s de reloj", md)
    if m:
        r["segundos_reloj"] = float(m[1])
    return r


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--modos", nargs="+", default=["A", "B"], choices=list(MODOS))
    p.add_argument("--ids", nargs="+")
    p.add_argument("--modelo", default="sonnet")
    p.add_argument("--paralelo", type=int, default=3)
    p.add_argument("--solo-calificar", action="store_true")
    a = p.parse_args()

    preguntas = pd.read_csv(AQUI / "preguntas.csv")
    if a.ids:
        preguntas = preguntas[preguntas.id.isin(a.ids)]
    casos = [(q, m) for m in a.modos for q in preguntas.itertuples()]
    TRAZAS.mkdir(parents=True, exist_ok=True)
    if a.solo_calificar:
        respuestas = [resumen_desde_traza(m, q.id) for q, m in casos]
    else:
        base = Path(tempfile.mkdtemp(prefix="tarea4_eval_"))
        print(f"{len(casos)} sesiones de claude -p con {a.modelo} (carpetas temporales en {base})...")
        t0 = time.time()
        with ThreadPoolExecutor(a.paralelo) as ex:
            respuestas = list(ex.map(lambda c: correr(c[0], c[1], a.modelo, base), casos))
        print(f"Listo en {time.time() - t0:.0f} s")
        shutil.rmtree(base, ignore_errors=True)

    nuevas = pd.DataFrame([fila(q, m, r) for (q, m), r in zip(casos, respuestas)])
    archivo = AQUI / "resultados.csv"
    if archivo.exists() and (a.ids or len(a.modos) < 2):   # actualiza solo las filas recalculadas
        viejas = pd.read_csv(archivo)
        clave = set(zip(nuevas.id, nuevas.modo))
        viejas = viejas[[(i, m) not in clave for i, m in zip(viejas.id, viejas.modo)]]
        nuevas = pd.concat([viejas, nuevas], ignore_index=True)
    nuevas = revisar(nuevas.drop(columns=["resultado_automatico", "revision_manual"], errors="ignore"))
    nuevas = nuevas.sort_values(["modo", "id"]).reset_index(drop=True)
    nuevas.to_csv(archivo, index=False, encoding="utf-8")

    print(nuevas.pivot(index="id", columns="modo", values="resultado").to_string())
    t = nuevas.groupby("modo").resultado.value_counts().unstack(fill_value=0)
    t["segundos_prom"] = nuevas.groupby("modo").segundos.mean().round(1)
    t["costo_usd"] = nuevas.groupby("modo").costo_usd.sum().round(3)
    print("\n" + t.to_string())


if __name__ == "__main__":
    main()
