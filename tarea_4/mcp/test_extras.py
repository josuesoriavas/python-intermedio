"""Pruebas extra (fuera del contrato de 10): graficar_serie y los recursos. uv run pytest mcp/test_extras.py"""
import asyncio
import json
from pathlib import Path

from fastmcp import Client

from server import PROYECTO, mcp


async def _con_cliente(f):
    async with Client(mcp) as c:
        return await f(c)


def test_graficar_serie_guarda_png_con_fuente():
    r = asyncio.run(_con_cliente(lambda c: c.call_tool("graficar_serie", {
        "codigos": ["PN01273PM", "PN09822PM"], "desde": "2024-01", "hasta": "2024-12",
        "unidad": "var. % 12 meses", "archivo": "_prueba_grafico"}))).data
    ruta = PROYECTO / r["archivo"]
    try:
        assert ruta.exists() and ruta.stat().st_size > 10_000
        assert r["codigos"] == ["PN01273PM", "PN09822PM"]
        assert (r["desde"], r["hasta"]) == ("2024-01", "2024-12")
        assert all(u.startswith("https://estadisticas.bcrp.gob.pe") for u in r["fuente"])
    finally:
        ruta.unlink(missing_ok=True)


def test_recurso_ficha_de_serie():
    async def leer(c):
        return await c.read_resource("bcrp://serie/PN01273PM")
    contenido = asyncio.run(_con_cliente(leer))
    ficha = json.loads(contenido[0].text)
    assert ficha["codigo"] == "PN01273PM" and ficha["frecuencia"] == "Mensual"
