"""Ejecuta Claude Code en modo no interactivo (claude -p) con una configuración controlada y guarda la traza completa.

    uv run python scripts/ejecutar_agente.py --modo mcp_skills --prompt-file informes/pregunta.md \
        --salida evidencias_ia/integracion/ejecucion_integrada

Escribe <salida>.jsonl (stream-json: cada mensaje, llamada a herramienta y resultado) y <salida>.md (resumen legible
con las herramientas MCP y las skills que usó). Es la evidencia de que Claude Code coordinó las herramientas.

Modos (todos con --strict-mcp-config: ningún otro servidor MCP del usuario entra en juego):
    base        sin MCP ni skills del proyecto y sin herramientas: solo el conocimiento del modelo
    skills      skills del proyecto + Bash limitado a `uv run` + lectura de archivos
    mcp         servidor MCP bcrp, sin herramientas de archivos ni terminal
    mcp_skills  servidor MCP bcrp + skills + Bash(uv run) + lectura y escritura de archivos
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from resumir_traza import a_markdown, leer, resumir  # noqa: E402

PROYECTO = Path(__file__).resolve().parents[1]
LECTURA = "Read,Glob,Grep"
MODOS = {
    "base": ["--tools", "", "--strict-mcp-config"],
    "skills": ["--strict-mcp-config", "--allowedTools", f"Skill,Bash(uv run:*),{LECTURA}"],
    "mcp": ["--tools", "", "--strict-mcp-config", "--mcp-config", ".mcp.json", "--allowedTools", "mcp__bcrp"],
    "mcp_skills": ["--strict-mcp-config", "--mcp-config", ".mcp.json",
                   "--allowedTools", f"mcp__bcrp,Skill,Bash(uv run:*),{LECTURA},Write,Edit"],
}


def ejecutar(prompt, modo, salida, modelo="sonnet", cwd=PROYECTO, sistema=None, timeout=1800, esquema=None,
             flags=None, env=None):
    """Corre claude -p y devuelve el resumen de la traza (dict). salida: ruta sin extensión.
    flags reemplaza a MODOS[modo] (para configuraciones propias, como las de la evaluación)."""
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    flags = MODOS[modo] if flags is None else flags
    cmd = ["claude", "-p", prompt, "--model", modelo, "--output-format", "stream-json", "--verbose",
           "--no-session-persistence", *flags]
    if sistema:
        cmd += ["--append-system-prompt", sistema]
    if esquema:
        cmd += ["--json-schema", json.dumps(esquema)]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                              timeout=timeout, env={**os.environ, **(env or {})})
        stdout, stderr, codigo = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr, codigo = f"TIMEOUT tras {timeout} s", -1
    segundos = round(time.time() - t0, 1)
    jsonl = salida.with_suffix(".jsonl")
    jsonl.write_text(stdout, encoding="utf-8")
    r = resumir(leer(jsonl))
    r.update({"modo": modo, "segundos_reloj": segundos, "codigo_salida": codigo, "stderr": stderr[-500:],
              "structured_output": next((json.loads(l).get("structured_output") for l in stdout.splitlines()
                                         if l.startswith('{"type":"result"')), None)})
    escribir_md(r, salida, prompt, modo, flags, modelo)
    return r


def escribir_md(r, salida, prompt, modo, flags, modelo):
    """Resumen legible de la traza. Un pedido «/skill …» es una invocación directa: Claude Code expande la skill como
    comando y no pasa por la herramienta Skill, así que se registra aparte (aparece en `slash_commands` del init)."""
    nombre = prompt.split()[0][1:] if prompt.startswith("/") else None
    if nombre and nombre in (r.get("skills_disponibles") or []):
        r["skills_usadas"] = [nombre] + r["skills_usadas"]
    md = a_markdown(r, f"Traza: {Path(salida).name} (modo {modo})")
    if nombre and nombre in (r.get("skills_disponibles") or []):
        md = md.replace("\n\n## Llamadas", f"\n- Invocación directa: `/{nombre}` (la skill se carga como comando, sin "
                                           "la herramienta Skill; sus instrucciones guían las llamadas de abajo)"
                                           "\n\n## Llamadas", 1)
    md = md + (f"\n## Pedido\n\n```text\n{prompt}\n```\n"
               f"\nModo `{modo}`: `{' '.join(repr(f) if f == '' else f for f in flags)}` · modelo `{modelo}` · "
               f"{r.get('segundos_reloj')} s de reloj · código de salida {r.get('codigo_salida')}\n")
    Path(salida).with_suffix(".md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    p.add_argument("--modo", choices=list(MODOS), default="mcp_skills")
    p.add_argument("--salida", required=True, help="ruta sin extensión para .jsonl y .md")
    p.add_argument("--modelo", default="sonnet")
    p.add_argument("--sistema", help="texto que se agrega al prompt de sistema")
    p.add_argument("--timeout", type=int, default=1800)
    a = p.parse_args()
    prompt = a.prompt or Path(a.prompt_file).read_text(encoding="utf-8")
    r = ejecutar(prompt, a.modo, a.salida, a.modelo, sistema=a.sistema, timeout=a.timeout)
    print(f"{r['segundos_reloj']} s · MCP {r['herramientas_mcp_distintas']} · skills {r['skills_usadas']} · "
          f"errores {len(r['errores'])} · salida {r['codigo_salida']}")
    print((r["respuesta"] or r["stderr"] or "")[:2500])
