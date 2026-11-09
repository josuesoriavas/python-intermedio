# Traza: 02_lenguaje_natural_graficando (modo skills)

- Modelo: `claude-sonnet-5-5`
- Servidores MCP: 
- Herramientas MCP distintas usadas: 0 → 
- Skills usadas: 1 → `graficando-enaho`
- Duración: 16.0 s · turnos: 4 · costo: 0.066161 USD

## Llamadas a herramientas, en orden

| # | Herramienta | Entrada |
|---|---|---|
| 1 | `Skill` | `{"skill": "graficando-enaho"}` |
| 2 | `Bash` | `{"command": "cd C:/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por sexo_jefe 2>&1 \| tail -40; ls figuras \| grep -i jefe; cat figuras/*se` |

## Respuesta final

Gráfico guardado en `tarea_4/figuras/pobreza_sexo_jefe.png`. La tabla exacta está en `figuras/pobreza_sexo_jefe.csv`.

**Pobreza monetaria por sexo del jefe de hogar, ENAHO 2024 (% de personas, con IC 95 %)**

| Jefatura | Pobreza | IC 95 % | n |
|---|---|---|---|
| Jefe hombre | 28.3 % | 27.1–29.5 | 73 855 |
| Jefa mujer | 26.0 % | 24.5–27.6 | 34 809 |

**¿La diferencia es importante?** Es pequeña y no es concluyente.
- **Tamaño:** los hogares con jefa mujer tienen 2.3 puntos porcentuales menos de pobreza que los de jefe hombre. Eso es una diferencia chica frente a las brechas por área o departamento.
- **Intervalos:** los IC 95 % se superponen (27.1–27.6), así que el gráfico dice «sin diferencia concluyente».
- **Matiz:** superponerse es un criterio conservador. Una prueba aproximada de la diferencia da un error estándar de unos 1.0 punto y un z de unos 2.3. Eso sugiere una diferencia al límite de ser significativa al 5 %. No la calculé con el diseño muestral completo, así que no la daría por establecida.
- **Interpretación:** es una asociación descriptiva. No dice que la jefatura femenina «reduzca» la pobreza. Los hogares con jefa mujer difieren en composición, por ejemplo en tamaño del hogar, en ser unipersonales o en el área de residencia. Esos factores no están controlados aquí.

## Pedido

```text
Grafica la pobreza monetaria por sexo del jefe de hogar en el Perú con la ENAHO 2024 y dime si la diferencia es importante.
```

Modo `skills`: `--strict-mcp-config --allowedTools Skill,Bash(uv run:*),Read,Glob,Grep` · modelo `sonnet` · 17.1 s de reloj · código de salida 0
