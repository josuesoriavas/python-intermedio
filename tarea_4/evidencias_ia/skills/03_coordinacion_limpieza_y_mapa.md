# Traza: 03_coordinacion_limpieza_y_mapa (modo skills)

- Modelo: `claude-sonnet-5-5`
- Servidores MCP: 
- Herramientas MCP distintas usadas: 0 → 
- Skills usadas: 2 → `mapeando-enaho`, `limpiando-enaho`
- Duración: 38.3 s · turnos: 9 · costo: 0.1076116 USD

## Llamadas a herramientas, en orden

| # | Herramienta | Entrada |
|---|---|---|
| 1 | `Skill` | `{"skill": "mapeando-enaho"}` |
| 2 | `Glob` | `{"pattern": "salidas/*"}` |
| 3 | `Bash` | `{"command": "cat salidas/validacion.txt \| head -30"}` |
| 4 | `Skill` | `{"skill": "limpiando-enaho"}` |
| 5 | `Bash` | `{"command": "cd C:/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 2>&1 \| tail -30; tail -5 salidas/validacion.txt; ls salidas", "tim` |
| 6 | `Bash` | `{"command": "cd C:/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && uv run python .claude/skills/mapeando-enaho/scripts/mapear.py 2>&1 \| tail -40; cat mapas/pobreza_departamento_2024.csv \| head -30; cat mapas/` |

## Respuesta final

Hice el mapa de pobreza monetaria por departamento con la ENAHO 2024: `mapas/pobreza_departamento_2024.png`. La tabla que se graficó está en `mapas/pobreza_departamento_2024.csv` (valor, IC 95 % y n por departamento).

Antes de mapear tuve que correr la limpieza, porque faltaba `salidas/personas_2024.parquet`. La validación dio 14 de 14 aprobadas ("BASE VÁLIDA"), con pobreza nacional de 27.5 %.

- **Cobertura:** hay 25 de 25 departamentos con dato. Lima y Callao van separados, y la unión se hizo por código ubigeo, no por nombre.
- **Mayor pobreza:** Cajamarca (45.0 %, IC 95 % 40.5–49.5), Loreto (42.6 %), Puno (40.4 %), Huánuco (39.5 %) y Pasco (39.3 %). Los cinco están por encima del 39 % de personas en pobreza monetaria.
- **Menor pobreza:** Ica (5.9 %), Moquegua (10.9 %), Madre de Dios (11.1 %) y Lambayeque (14.1 %).
- **Comparación con la referencia del curso:**
  - Con el método del INEI (`inei_hogares`), coincide en los 25 departamentos.
  - Con residentes habituales ponderados con `facpob07`, que es lo que usé en el mapa, coinciden 6 de 25 y la diferencia máxima es 0.5 puntos. Se debe a que cuentan poblaciones distintas. El orden de los departamentos casi no cambia (correlación de rangos 0.999).
- **Intervalos:** las diferencias entre departamentos cercanos pueden no ser concluyentes, porque los IC 95 % se superponen. Por ejemplo, Puno, Huánuco y Pasco no se pueden ordenar con seguridad entre sí.

Las cifras son descriptivas de un corte transversal y no indican causas.

Fuente: INEI, ENAHO 2024, módulos 34 y 02.

Si quieres las cifras oficiales exactas del INEI en el mapa, lo regenero con `--metodo inei_hogares`.

## Pedido

```text
Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.
```

Modo `skills`: `--strict-mcp-config --allowedTools Skill,Bash(uv run:*),Read,Glob,Grep` · modelo `sonnet` · 39.2 s de reloj · código de salida 0
