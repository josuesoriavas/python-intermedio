# Traza: 01_invocacion_directa_limpiando (modo skills)

- Modelo: `claude-sonnet-5-5`
- Servidores MCP: 
- Herramientas MCP distintas usadas: 0 → 
- Skills usadas: 1 → `limpiando-enaho`
- Duración: 19.5 s · turnos: 3 · costo: 0.077215 USD
- Invocación directa: `/limpiando-enaho` (la skill se carga como comando, sin la herramienta Skill; sus instrucciones guían las llamadas de abajo)

## Llamadas a herramientas, en orden

| # | Herramienta | Entrada |
|---|---|---|
| 1 | `Bash` | `{"command": "ls salidas/ && grep -n \"Resultado\" salidas/validacion.txt", "description": "Check existing base and validation result"}` |
| 2 | `Bash` | `{"command": "uv run python C:/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4/.claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 2>&1 \| tail -40; ls salidas; grep -n \"Resultado\" salidas/validacion.tx` |

## Respuesta final

La limpieza de la ENAHO 2024 terminó y la base quedó **válida**: pasaron las 15 validaciones (cero fallidas).

**Bases generadas** (en `salidas/`)
- `personas_2024.parquet`: 108,664 residentes habituales.
- `hogares_2024.parquet`: 33,691 hogares.
- `indicadores.csv`: 178 filas con los indicadores ya calculados.
- `validacion.txt`: el detalle de las validaciones.

**Pobreza monetaria nacional 2024**
- **Personas (`facpob07`):** 27.5 % de las personas, con IC 95 % de 26.5 a 28.6.
- **Método INEI (sumaria, `factor07 × mieperho`):** 27.6 %, igual a la cifra publicada.
- **Pobreza extrema:** 5.5 %.
- **Urbana y rural:** 24.7 % urbana y 39.4 % rural con residentes habituales. Con el método INEI salen 24.8 % y 39.3 %.
- **Lima Metropolitana:** 28.0 % con residentes habituales y 28.2 % con el método INEI.
- **Efecto de ponderar:** el promedio sin ponderar daría 25.6 %, así que subestima la pobreza en 1.9 puntos porcentuales.

Los dos métodos difieren unas décimas porque cuentan poblaciones distintas. Los residentes habituales excluyen a 1,787 miembros ausentes 30 días o más e incluyen a 609 no miembros presentes 30 días o más.

Fuente: INEI, ENAHO 2024, módulos 34 y 02.

Si quiere un corte concreto (por departamento, sexo o área, por ejemplo), lo calculo con `consultar.py`.

## Pedido

```text
/limpiando-enaho 2024
```

Modo `skills`: `--strict-mcp-config --allowedTools Skill,Bash(uv run:*),Read,Glob,Grep` · modelo `sonnet` · 20.5 s de reloj · código de salida 0
