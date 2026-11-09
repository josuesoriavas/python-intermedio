"""Resume una traza de `claude -p --output-format stream-json --verbose`: servidores MCP, skills, herramientas usadas y respuesta.

    uv run python scripts/resumir_traza.py evidencias_ia/integracion/traza.jsonl            # texto
    uv run python scripts/resumir_traza.py traza.jsonl --md resumen.md                        # además, en Markdown

Sirve como evidencia: muestra qué herramientas MCP y qué skills llamó Claude Code, en qué orden y con qué argumentos.
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def leer(ruta):
    eventos = []
    for linea in Path(ruta).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            eventos.append(json.loads(linea))
        except json.JSONDecodeError:
            continue
    return eventos


def resumir(eventos):
    init = next((e for e in eventos if e.get("type") == "system" and e.get("subtype") == "init"), {})
    final = next((e for e in reversed(eventos) if e.get("type") == "result"), {})
    llamadas, errores = [], []
    for e in eventos:
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use":
                    llamadas.append({"id": b["id"], "herramienta": b["name"], "entrada": b.get("input", {})})
        if e.get("type") == "user":
            contenido = e.get("message", {}).get("content", [])
            for b in contenido if isinstance(contenido, list) else []:
                if b.get("type") == "tool_result" and b.get("is_error"):
                    texto = b.get("content")
                    texto = texto if isinstance(texto, str) else json.dumps(texto, ensure_ascii=False)
                    errores.append({"id": b.get("tool_use_id"), "error": texto[:300]})
    skills = [c["entrada"].get("skill") or c["entrada"].get("command") for c in llamadas if c["herramienta"] == "Skill"]
    mcp = [c["herramienta"] for c in llamadas if c["herramienta"].startswith("mcp__")]
    return {
        "modelo": init.get("model"),
        "servidores_mcp": init.get("mcp_servers"),
        "skills_disponibles": init.get("skills"),
        "llamadas": llamadas,
        "herramientas_mcp_distintas": sorted(set(mcp)),
        "skills_usadas": skills,
        "conteo": dict(Counter(c["herramienta"] for c in llamadas)),
        "errores": errores,
        "respuesta": final.get("result"),
        "segundos": round(final.get("duration_ms", 0) / 1000, 1),
        "turnos": final.get("num_turns"),
        "costo_usd": final.get("total_cost_usd"),
    }


def a_markdown(r, titulo="Resumen de la traza"):
    lineas = [f"# {titulo}", "",
              f"- Modelo: `{r['modelo']}`",
              f"- Servidores MCP: {', '.join(f'`{s.get('name')}` ({s.get('status')})' for s in r['servidores_mcp'] or [])}",
              f"- Herramientas MCP distintas usadas: {len(r['herramientas_mcp_distintas'])} → "
              + ", ".join(f"`{h}`" for h in r["herramientas_mcp_distintas"]),
              f"- Skills usadas: {len(set(r['skills_usadas']))} → " + ", ".join(f"`{s}`" for s in dict.fromkeys(r["skills_usadas"])),
              f"- Duración: {r['segundos']} s · turnos: {r['turnos']} · costo: {r['costo_usd']} USD",
              "", "## Llamadas a herramientas, en orden", "", "| # | Herramienta | Entrada |", "|---|---|---|"]
    for i, c in enumerate(r["llamadas"], 1):
        entrada = json.dumps(c["entrada"], ensure_ascii=False).replace("|", "\\|").replace("\n", " ")
        lineas.append(f"| {i} | `{c['herramienta']}` | `{entrada[:220]}` |")
    if r["errores"]:
        lineas += ["", "## Errores devueltos por herramientas", ""]
        lineas += [f"- `{e['id']}`: {e['error']}" for e in r["errores"]]
    lineas += ["", "## Respuesta final", "", r["respuesta"] or "(sin respuesta)"]
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("traza")
    p.add_argument("--md", help="escribe además un resumen en Markdown")
    p.add_argument("--titulo", default="Resumen de la traza")
    a = p.parse_args()
    r = resumir(leer(a.traza))
    print(f"modelo={r['modelo']}  mcp={[(s.get('name'), s.get('status')) for s in r['servidores_mcp'] or []]}")
    print(f"skills disponibles={r['skills_disponibles']}")
    for i, c in enumerate(r["llamadas"], 1):
        print(f"{i:>2}. {c['herramienta']}  {json.dumps(c['entrada'], ensure_ascii=False)[:160]}")
    print(f"MCP distintas={r['herramientas_mcp_distintas']}  skills={r['skills_usadas']}  errores={len(r['errores'])}")
    print(f"segundos={r['segundos']} turnos={r['turnos']}\n--- respuesta ---\n{(r['respuesta'] or '')[:1500]}")
    if a.md:
        Path(a.md).write_text(a_markdown(r, a.titulo), encoding="utf-8")
