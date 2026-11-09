# Traza: 03_manejo_errores (modo mcp_skills)

- Modelo: `claude-sonnet-5-5`
- Servidores MCP: `bcrp` (connected)
- Herramientas MCP distintas usadas: 2 → `mcp__bcrp__buscar_series`, `mcp__bcrp__serie`
- Skills usadas: 1 → `limpiando-enaho`
- Duración: 19.2 s · turnos: 7 · costo: 0.1003122 USD

## Llamadas a herramientas, en orden

| # | Herramienta | Entrada |
|---|---|---|
| 1 | `ToolSearch` | `{"query": "select:mcp__bcrp__buscar_series,mcp__bcrp__serie,mcp__bcrp__resumen", "max_results": 5}` |
| 2 | `Skill` | `{"skill": "limpiando-enaho"}` |
| 3 | `mcp__bcrp__buscar_series` | `{"texto": "ipc lima metropolitana 12 meses", "frecuencia": "Mensual"}` |
| 4 | `Read` | `{"file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\salidas\\validacion.txt", "limit": 30}` |
| 5 | `mcp__bcrp__serie` | `{"codigo": "PN01273PM", "desde": "2026-09", "hasta": "2026-12"}` |

## Respuesta final

Ninguna de las dos cifras se pudo obtener, así que no tengo valores para el informe. No escribí ni modifiqué archivos.

**1. Inflación interanual de Lima Metropolitana, diciembre de 2026: no disponible**
- Usé la serie `PN01273PM` del BCRP (IPC de Lima Metropolitana, variación porcentual en 12 meses), consultada de septiembre a diciembre de 2026.
- La consulta no devolvió error, pero solo trae datos hasta octubre de 2026. La serie figura como actualizada el 2026-10-08.
- Hoy es 2026-11-09 y diciembre de 2026 todavía no ocurrió, así que ese dato no existe. No lo estimo.
- Los últimos datos que sí existen, por si le sirven (no sustituyen diciembre):
  - Septiembre de 2026: 4.55 %.
  - Octubre de 2026: 5.25 %.
- Fuente: https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2026-9/2026-12

**2. Pobreza monetaria nacional 2025 con la ENAHO 2025: no calculada**
- La skill `limpiando-enaho` está construida solo para la ENAHO 2024. Usa los archivos del INEI con código 966 (módulos 34 y 02). No tengo el código del INEI para 2025, y la skill no lo trae.
- El script `limpiar.py` descarga archivos a `datos/inei/` y escribe en `salidas/`, así que correrlo contradice su instrucción de no modificar archivos.
- No hay datos de 2025 en el proyecto. La única validación que existe, `salidas/validacion.txt`, es de 2024.
- Para cualquier otro año, la validación de la skill compara contra cifras de referencia de 2024, así que no serviría para validar 2025.
- No reemplazo 2025 por 2024. Como referencia aparte, la pobreza monetaria nacional de 2024 ya validada en el proyecto es 27.5 % con el método de personas y 27.6 % con el método INEI (sumaria). Esa cifra no es la de 2025.

**Cómo puedo avanzar**
- Para la cifra de 2025, necesito el código de la ENAHO 2025 en el portal del INEI. Con ese código, y si me autoriza a escribir en `datos/` y `salidas/`, adapto la corrida y valido el resultado antes de reportarlo.
- Para la inflación de diciembre de 2026, hay que esperar a que el BCRP publique el dato, normalmente a inicios de enero de 2027.

## Pedido

```text
Para un informe necesito dos cifras oficiales: (1) la inflación interanual (IPC, variación en 12 meses) de Lima Metropolitana en diciembre de 2026 según el BCRP y (2) la tasa de pobreza monetaria nacional de 2025 calculada con la ENAHO 2025 del INEI. Usa el servidor MCP bcrp y las skills del proyecto (actívalas con la herramienta Skill). No escribas ni modifiques archivos. Si una herramienta falla o un dato no está disponible, dilo con el mensaje de error y explica por qué; no lo estimes ni lo reemplaces por otro período sin decirlo.
```

Modo `mcp_skills`: `--strict-mcp-config --mcp-config .mcp.json --allowedTools mcp__bcrp,Skill,Bash(uv run:*),Read,Glob,Grep,Write,Edit` · modelo `sonnet` · 24.7 s de reloj · código de salida 0
