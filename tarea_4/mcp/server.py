"""Servidor MCP del BCRP para el agente de investigación socioeconómica (Tarea 4).

Parte del esqueleto de la Sesión 04 (d2cml-ai/Data-Science-Python, sessions/04-mcp-claude-code/proyecto) y lo completa:

    uv run pytest mcp/test_server.py      # el contrato: 8 pruebas originales + 2 de la herramienta propia
    uv run python mcp/server.py           # el servidor, por stdio (así lo lanza .mcp.json)

Herramientas
    buscar_series      palabras clave -> códigos oficiales del catálogo del BCRP
    serie              datos de una serie entre dos fechas, con la URL de la API como fuente
    resumen            primero, último, cambio, variación %, promedio, máximo y mínimo
    comparar_periodos  (propia) compara una serie entre dos intervalos: promedios, extremos y diferencia
    graficar_serie     (propia) guarda un PNG de una o más series en figuras/, con título, unidades y fuente
Recursos
    bcrp://serie/{codigo}   ficha descriptiva de una serie (nombre, frecuencia, inicio, última actualización)
    bcrp://series-clave     las series que usa el proyecto, con su código
Prompts
    informe(tema)                    informe breve que cita código y período de cada cifra
    interpretar_indicador(codigo, desde, hasta)

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""
import re
import time
import unicodedata
from datetime import date
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
PROYECTO = AQUI.parent
CATALOGO = PROYECTO / "datos" / "bcrp" / "catalogo_bcrp.csv"
FIGURAS = PROYECTO / "figuras"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
         "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12}

SERIES_CLAVE = {   # códigos comprobados con buscar_series contra el catálogo oficial
    "PN01273PM": "Inflación de Lima Metropolitana: variación % del IPC en 12 meses (mensual)",
    "PN01271PM": "IPC de Lima Metropolitana: variación % mensual",
    "PN09822PM": "IPC Alimentos y Bebidas de Lima Metropolitana: variación % en 12 meses (mensual)",
    "PN01277PM": "IPC sin Alimentos y Energía de Lima Metropolitana: variación % en 12 meses (mensual)",
    "PM04923AA": "PBI real: variación % anual (anual)",
    "PN01206PM": "Tipo de cambio interbancario venta, promedio del período, S/ por US$ (mensual)",
    "PD04722MM": "Tasa de referencia de la política monetaria del BCRP, % (mensual)",
    "PN38063GM": "Tasa de desempleo de Lima Metropolitana, %, promedio móvil de tres meses (mensual)",
}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series "
    "(o lee el recurso bcrp://series-clave); luego usa resumen para variaciones, promedios y extremos, serie para "
    "los datos, comparar_periodos para contrastar dos intervalos y graficar_serie para guardar un gráfico. "
    "No calcules a mano: cita siempre el código de la serie, el período y la fuente. Si una herramienta falla o no "
    "hay datos, dilo en vez de estimar."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: unas 17 mil series en unos 7 MB. Se baja una vez y queda en datos/bcrp/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    codigo = str(codigo).strip().upper()
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    # primero las series vigentes y, entre ellas, las de nombre más corto (las más generales)
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


# --------------------------------------------------------------------------------------------- fechas y períodos

def _tipo(frecuencia):
    f = _sin_tildes(frecuencia)
    for clave in ("diaria", "mensual", "trimestral", "anual"):
        if clave in f:
            return clave
    raise ToolError(f"Frecuencia {frecuencia!r} no soportada (solo diaria, mensual, trimestral o anual).")


def _fecha_api(texto, tipo, fin):
    """Convierte '2025-01', '2025-1', '2025', '2026-10-15' o '2025-T1' al formato que pide la API."""
    t = str(texto).strip().upper().replace("/", "-")
    m = re.fullmatch(r"(\d{4})(?:-(T?)(\d{1,2}))?(?:-(\d{1,2}))?", t)
    if not m:
        raise ToolError(f"Fecha {texto!r} no reconocida. Usen 2025-01 (mensual), 2026-10-15 (diaria), "
                        f"2025-T1 (trimestral) o 2025 (anual).")
    anio, es_t, mes, dia = int(m[1]), m[2], m[3], m[4]
    if tipo == "anual":
        return f"{anio}"
    if tipo == "trimestral":
        if mes is None:
            return f"{anio}-{4 if fin else 1}"
        trimestre = int(mes) if es_t else (int(mes) - 1) // 3 + 1
        return f"{anio}-{trimestre}"
    if tipo == "mensual":
        return f"{anio}-{int(mes) if mes else (12 if fin else 1)}"
    # diaria
    if mes is None:
        return f"{anio}-12-31" if fin else f"{anio}-01-01"
    if dia is None:
        ultimo = (pd.Timestamp(anio, int(mes), 1) + pd.offsets.MonthEnd(0)).day
        dia = ultimo if fin else 1
    return f"{anio}-{int(mes):02d}-{int(dia):02d}"


def _periodo(nombre, tipo):
    """'Ene.2025' -> '2025-01', '01.Oct.26' -> '2026-10-01', 'T1.25' -> '2025-T1', '2025' -> '2025'."""
    n = nombre.strip()
    if tipo == "anual":
        return n
    if tipo == "trimestral":
        t, a = n.split(".")
        anio = int(a) + 2000 if len(a) == 2 else int(a)
        return f"{anio}-{t.upper()}"
    if tipo == "mensual":
        mes, anio = n.split(".")
        return f"{int(anio)}-{MESES[_sin_tildes(mes)[:3]]:02d}"
    dia, mes, anio = n.split(".")
    anio = int(anio) + 2000 if len(anio) == 2 else int(anio)
    return f"{anio}-{MESES[_sin_tildes(mes)[:3]]:02d}-{int(dia):02d}"


@cache
def _descargar(codigo, desde_api, hasta_api):
    """Llama a la API (con reintentos: si recibe muchos pedidos seguidos responde HTML en vez de JSON)."""
    url = f"{API}/{codigo}/json/{desde_api}/{hasta_api}"
    ultimo_error = ""
    for intento in range(5):
        try:
            r = httpx.get(url, timeout=60, follow_redirects=True)
            r.raise_for_status()
            return url, r.json()
        except (httpx.HTTPError, ValueError) as e:
            ultimo_error = f"{type(e).__name__}: {e}"[:200]
            time.sleep(2 * (intento + 1))
    raise ToolError(f"El BCRP no respondió con datos para {codigo} ({url}) tras 5 intentos: {ultimo_error}")


def _datos(codigo, desde, hasta):
    ficha = _ficha(codigo)
    tipo = _tipo(ficha["frecuencia"])
    d, h = _fecha_api(desde, tipo, fin=False), _fecha_api(hasta, tipo, fin=True)
    url, js = _descargar(ficha["codigo"], d, h)
    datos = []
    for p in js.get("periods", []):
        v = (p.get("values") or [None])[0]
        try:
            valor = float(v)
        except (TypeError, ValueError):   # "n.d." y vacíos
            continue
        datos.append({"periodo": _periodo(p["name"], tipo), "valor": valor})
    if not datos:
        raise ToolError(f"La serie {ficha['codigo']} no tiene datos entre {desde} y {hasta} ({url}).")
    return ficha, url, datos


def _estadisticas(datos):
    s = pd.Series([x["valor"] for x in datos], index=[x["periodo"] for x in datos])
    primero, ultimo = datos[0], datos[-1]
    return {
        "n": len(datos),
        "primero": primero, "ultimo": ultimo,
        "cambio": round(ultimo["valor"] - primero["valor"], 6),
        "variacion_pct": round((ultimo["valor"] / primero["valor"] - 1) * 100, 4) if primero["valor"] else None,
        "promedio": round(float(s.mean()), 6),
        "maximo": {"periodo": s.idxmax(), "valor": float(s.max())},
        "minimo": {"periodo": s.idxmin(), "valor": float(s.min())},
    }


# --------------------------------------------------------------------------------------------- herramientas

@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Descarga los datos oficiales de una serie del BCRP entre dos fechas (ambas incluidas).

    Fechas según la frecuencia de la serie: "2025-01" (mensual), "2026-10-15" (diaria), "2025-T1" (trimestral),
    "2025" (anual). Un año solo ("2024") vale para todo el año en cualquier frecuencia.
    Devuelve {"codigo", "nombre", "frecuencia", "datos": [{"periodo", "valor"}], "fuente"}; "fuente" es la URL de la
    API del BCRP que se consultó. Los valores "n.d." se omiten. Ejemplo: serie("PN01273PM", "2024-01", "2024-12").
    """
    ficha, url, datos = _datos(codigo, desde, hasta)
    return {"codigo": ficha["codigo"], "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"],
            "datos": datos, "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Resume una serie del BCRP entre dos fechas sin cuentas a mano.

    Devuelve primero y último valor (con su período), cambio (último − primero), variacion_pct del último respecto
    del primero, promedio del período, máximo y mínimo (con el período en que ocurrieron), n de observaciones y la
    fuente. Úsenla para "¿cuánto subió?", "¿cuál fue el promedio de 2024?", "¿cuándo fue el máximo?".
    """
    ficha, url, datos = _datos(codigo, desde, hasta)
    return {"codigo": ficha["codigo"], "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"],
            "desde": datos[0]["periodo"], "hasta": datos[-1]["periodo"], **_estadisticas(datos), "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def comparar_periodos(codigo: str, desde_a: str, hasta_a: str, desde_b: str, hasta_b: str) -> dict:
    """Compara el comportamiento de UNA serie del BCRP en dos intervalos (A y B), por ejemplo antes y después de un choque.

    Para cada intervalo calcula n, promedio, primero, último, máximo y mínimo (con su período). Luego devuelve
    diferencia_promedios (B − A, en las unidades de la serie), variacion_pct_promedios ((B/A − 1)·100) y cuál
    intervalo tuvo el promedio mayor. Los intervalos deben estar ordenados (desde ≤ hasta) y no superponerse.
    Ejemplo: comparar_periodos("PN01273PM", "2022-01", "2022-12", "2024-01", "2024-12") compara la inflación
    a 12 meses de 2022 con la de 2024.
    """
    tipo = _tipo(_ficha(codigo)["frecuencia"])
    clave = lambda f: tuple(int(x) for x in f.split("-"))  # noqa: E731  '2024-12' -> (2024, 12)
    for nombre, d, h in (("A", desde_a, hasta_a), ("B", desde_b, hasta_b)):
        if clave(_fecha_api(d, tipo, fin=False)) > clave(_fecha_api(h, tipo, fin=True)):
            raise ToolError(f"Intervalo {nombre} inválido ({d} > {h}): desde debe ser anterior o igual a hasta.")
    _, url_a, datos_a = _datos(codigo, desde_a, hasta_a)
    ficha, url_b, datos_b = _datos(codigo, desde_b, hasta_b)
    a, b = _estadisticas(datos_a), _estadisticas(datos_b)
    if set(x["periodo"] for x in datos_a) & set(x["periodo"] for x in datos_b):
        raise ToolError("Los intervalos A y B se superponen: elijan períodos disjuntos para compararlos.")
    dif = b["promedio"] - a["promedio"]
    return {
        "codigo": ficha["codigo"], "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"],
        "a": {"desde": datos_a[0]["periodo"], "hasta": datos_a[-1]["periodo"], **a},
        "b": {"desde": datos_b[0]["periodo"], "hasta": datos_b[-1]["periodo"], **b},
        "diferencia_promedios": round(dif, 6),
        "variacion_pct_promedios": round((b["promedio"] / a["promedio"] - 1) * 100, 4) if a["promedio"] else None,
        "mayor_promedio": "A" if a["promedio"] > b["promedio"] else ("B" if b["promedio"] > a["promedio"] else "igual"),
        "fuente": [url_a, url_b],
    }


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": True})
def graficar_serie(codigos: list[str], desde: str, hasta: str, titulo: str | None = None,
                   unidad: str | None = None, archivo: str | None = None) -> dict:
    """Grafica una o hasta cuatro series oficiales del BCRP (misma unidad) y guarda un PNG en figuras/.

    El gráfico lleva título analítico (si no se da, usa el nombre de la serie), la unidad en el eje, el período y la
    nota de fuente con los códigos consultados. Devuelve la ruta del PNG, los códigos, el período graficado, el último
    valor de cada serie y las URLs de la API. Ejemplo: graficar_serie(["PN01273PM", "PN01383PM"], "2020-01",
    "2024-12", titulo="La inflación tocó su máximo en 2022 y volvió al rango meta en 2024", unidad="var. % 12 meses").
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not 1 <= len(codigos) <= 4:
        raise ToolError("graficar_serie acepta entre 1 y 4 códigos.")
    series, fuentes, ultimos = [], [], {}
    for c in codigos:
        ficha, url, datos = _datos(c, desde, hasta)
        series.append((ficha, datos))
        fuentes.append(url)
        ultimos[ficha["codigo"]] = datos[-1]
    tipo = _tipo(series[0][0]["frecuencia"])

    def _x(p):
        if tipo == "mensual":
            return pd.Timestamp(p + "-01")
        if tipo == "diaria":
            return pd.Timestamp(p)
        if tipo == "trimestral":
            anio, t = p.split("-T")
            return pd.Timestamp(int(anio), 3 * int(t) - 1, 15)
        return int(p)

    import textwrap

    # Nombre corto para la leyenda: lo que sigue al último " - " del nombre oficial (p. ej. "IPC Alimentos y Bebidas")
    cortos = [f["nombre"].rsplit(" - ", 1)[-1] for f, _ in series]
    comun = series[0][0]["nombre"].rsplit(" - ", 1)[0] if all(
        f["nombre"].rsplit(" - ", 1)[0] == series[0][0]["nombre"].rsplit(" - ", 1)[0] for f, _ in series) else ""
    fig, ax = plt.subplots(figsize=(9, 5.4), facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    colores = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]   # paleta categórica validada (orden fijo)
    for (ficha, datos), color, corto in zip(series, colores, cortos):
        ax.plot([_x(x["periodo"]) for x in datos], [x["valor"] for x in datos], color=color, lw=2,
                marker="o" if len(datos) <= 15 else None, label=f'{corto} ({ficha["codigo"]})')
    ax.axhline(0, color="#999", lw=0.8)
    p0, p1 = series[0][1][0]["periodo"], series[0][1][-1]["periodo"]
    lineas = textwrap.wrap(titulo or series[0][0]["nombre"], 80)
    fig.text(0.012, 0.985, "\n".join(lineas), ha="left", va="top", fontsize=12, fontweight="bold", color="#0b0b0b")
    sub = f"{comun}, {p0} a {p1}" if comun else f"Período: {p0} a {p1}"
    fig.text(0.012, 0.985 - 0.05 * len(lineas) - 0.01, sub, ha="left", va="top", fontsize=9, color="#52514e")
    ax.set_ylabel(unidad or "valor de la serie", color="#52514e")
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8.5, frameon=False, loc="best")
    fig.text(0.012, 0.012, f"Fuente: BCRP, estadisticas.bcrp.gob.pe, series "
             f"{', '.join(f['codigo'] for f, _ in series)} (consulta {date.today():%d/%m/%Y}). "
             f"Elaboración: servidor MCP bcrp (graficar_serie).", fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.04, 1, 0.985 - 0.05 * len(lineas) - 0.05))
    FIGURAS.mkdir(exist_ok=True)
    nombre = archivo or f"bcrp_{'_'.join(f['codigo'] for f, _ in series)}_{p0}_{p1}"
    ruta = FIGURAS / (re.sub(r"[^\w.-]", "_", Path(nombre).stem) + ".png")
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    return {"archivo": str(ruta.relative_to(PROYECTO)).replace("\\", "/"), "codigos": [f["codigo"] for f, _ in series],
            "desde": p0, "hasta": p1, "ultimos": ultimos, "fuente": fuentes}


# --------------------------------------------------------------------------------------------- recursos y prompts

@mcp.resource("bcrp://serie/{codigo}", mime_type="application/json")
def ficha_serie(codigo: str) -> dict:
    """Ficha descriptiva de una serie del BCRP: nombre, categoría, frecuencia, inicio y última actualización."""
    f = _ficha(codigo)
    f["pagina"] = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/{_tipo(f['frecuencia'])}es/resultados/{f['codigo']}/html"
    f["api"] = f"{API}/{f['codigo']}/json"
    return f


@mcp.resource("bcrp://series-clave", mime_type="application/json")
def series_clave() -> dict:
    """Series del BCRP que usa el agente de investigación socioeconómica, con su código y descripción."""
    return SERIES_CLAVE


@mcp.prompt
def informe(tema: str) -> str:
    """Informe breve sobre un tema macroeconómico peruano con cifras oficiales del BCRP, citadas una a una."""
    return (
        f"Prepara un informe breve sobre «{tema}» con series oficiales del BCRP.\n"
        "1. Busca las series con buscar_series (o el recurso bcrp://series-clave) y elige las más generales y vigentes.\n"
        "2. Obtén cada cifra con resumen, serie o comparar_periodos. No calcules nada a mano.\n"
        "3. Cada cifra va con el código de la serie, el período y la fuente (URL de la API), por ejemplo: "
        "«4.55 % (PN01273PM, 2026-09)».\n"
        "4. Si te sirve un gráfico, genéralo con graficar_serie y cita la ruta del PNG.\n"
        "5. Describe asociaciones, no causas. Si una herramienta falla o no hay datos, dilo explícitamente."
    )


@mcp.prompt
def interpretar_indicador(codigo: str, desde: str, hasta: str) -> str:
    """Interpreta la evolución de una serie del BCRP en un período: niveles, extremos y cambios, con cifras verificables."""
    return (
        f"Interpreta la serie {codigo} del BCRP entre {desde} y {hasta}.\n"
        f"Lee primero el recurso bcrp://serie/{codigo} para saber qué mide y en qué unidad. Luego llama a resumen "
        "y, si hace falta, a comparar_periodos para contrastar subperíodos. Explica en 5 líneas: el nivel inicial y "
        "final, el máximo y el mínimo con sus fechas, y qué significa para hogares y empresas. Cita el código y el "
        "período de cada cifra y no atribuyas causas que los datos no demuestran."
    )


if __name__ == "__main__":
    mcp.run()
