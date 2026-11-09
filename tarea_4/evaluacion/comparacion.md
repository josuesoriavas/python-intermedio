# Evaluación A/B: Claude Code sin herramientas frente a Claude Code con el MCP del BCRP y las Skills de la ENAHO

## Diseño

- **Preguntas.** 10 en total, en [`preguntas.csv`](preguntas.csv): 4 del BCRP (B1–B4), 4 de la ENAHO 2024 (E1–E4) y 2 combinadas (C1–C2). Las respuestas esperadas las calculó [`respuestas_esperadas.py`](respuestas_esperadas.py) sin usar el MCP ni las skills: llama directo a la API del BCRP y lee los `.dta` del INEI con pandas. Las tolerancias y los criterios se fijaron y se registraron en git (commit `9855aff`) **antes** de correr el experimento.
- **Ejecución.** [`evaluar.py`](evaluar.py) corre cada pregunta en una sesión independiente de `claude -p` (20 en total) con `--no-session-persistence`. Las dos condiciones comparten modelo (`claude-sonnet-5-5`), instrucción de sistema y formato de salida (`--json-schema` con `valor`, `valor_2`, `respuesta` y `fuente`). Las corridas se hicieron el 9/11/2026 y las trazas completas están en [`../evidencias_ia/evaluacion/trazas/`](../evidencias_ia/evaluacion/trazas/).

| | Modo A, sin MCP ni Skills | Modo B, con MCP y Skills |
|---|---|---|
| Carpeta de trabajo | temporal y vacía, fuera del repositorio | copia temporal del proyecto, sin `salidas/`, `evaluacion/`, `informes/`, `figuras/`, `mapas/` ni `evidencias_ia/` (no hay respuestas que leer) |
| Herramientas habilitadas | ninguna (`--tools ""`) | `Skill`, `Bash`, `Read`, `Glob`, `Grep`; permisos solo para `mcp__bcrp`, `Skill`, `Bash(uv run:*)`, `Read`, `Glob` y `Grep` |
| Servidores MCP | ninguno (`--strict-mcp-config`) | solo `bcrp` (`--mcp-config .mcp.json`) |
| Skills | ninguna | `limpiando-enaho`, `graficando-enaho` y `mapeando-enaho` |
| Web | no | no |

- **Calificación.** Una respuesta es **correcta** si `valor` (y `valor_2`, cuando la pregunta pide dos cifras) cae dentro de la tolerancia y cumple el criterio adicional: E3 debe nombrar a Cajamarca; C2 debe dar el mes del pico; las combinadas no deben interpretar de forma causal. Es **no contesta** si el agente devuelve `null` y reconoce que no puede saberlo, e **incorrecta** en cualquier otro caso. La calificación automática revisa la interpretación causal con un patrón de texto. Además, revisé a mano las cuatro respuestas combinadas ([`revision_manual.csv`](revision_manual.csv)).

## Resultados

| Modo | Correctas | Incorrectas | No contesta | Tiempo promedio | Turnos promedio | Llamadas a herramientas | Errores de herramientas | Costo total |
|---|---|---|---|---|---|---|---|---|
| **A** (sin herramientas) | **2/10** | 1 | 7 | 7.2 s | 2.1 | 0 (1 intento rechazado) | 1 | 0.18 USD |
| **B** (MCP + Skills) | **10/10** | 0 | 0 | 25.9 s | 7.1 | 46 | 3 | 0.76 USD |

Por tipo de pregunta:

| Tipo | A correctas | B correctas | A tiempo prom. | B tiempo prom. |
|---|---|---|---|---|
| BCRP (4) | 1 | 4 | 6.4 s | 15.1 s |
| ENAHO (4) | 1 | 4 | 6.1 s | 33.4 s |
| Combinadas (2) | 0 | 2 | 10.8 s | 32.8 s |

> **Calificación automática y revisión manual.** El patrón automático calificó C1-B y C2-B como «incorrecta» por «interpretación causal». Los dos casos son falsos positivos: el patrón detectó la palabra *causalidad* en «sin causalidad» y *causales* en «no causales», es decir, en frases que niegan la causalidad. En la revisión manual ambas cifras de cada respuesta están dentro de tolerancia y la interpretación cumple el criterio. Con la calificación automática sola, el modo B tiene **8/10**; tras la revisión manual, **10/10**. `resultados.csv` guarda las dos columnas (`resultado_automatico` y `resultado`) y el motivo de cada revisión.

### Pregunta por pregunta

| ID | Esperado | Modo A | Modo B | Cambio | Herramientas en B |
|---|---|---|---|---|---|
| B1 Inflación dic-2024 | 1.9663 % | ✅ 1.97 «de memoria, no verificado» | ✅ 1.97 | igual | `buscar_series`, `serie` |
| B2 PBI 2024 | 3.5153 % | ❌ 3.3 (de memoria) | ✅ 3.5 | **mejora** | `buscar_series`, `serie` |
| B3 TC promedio 2024 | 3.7559 | ➖ null («ronda 3,75», sin verificar) | ✅ 3.7559 | **mejora** | `buscar_series`, `resumen` |
| B4 Alimentos oct-2026 | 5.2841 % | ➖ null (posterior a lo que sabe el modelo) | ✅ 5.28 | **mejora** | `buscar_series`, `serie` |
| E1 Pobreza nacional | 27.6 % | ✅ 27.6 «de memoria» | ✅ 27.6 | igual | Skill `limpiando-enaho` (`limpiar.py`) |
| E2 Pobreza rural | 39.3 % | ➖ null | ✅ 39.3 | **mejora** | Skill `limpiando-enaho` (`limpiar.py`, `consultar.py`) |
| E3 Departamento más pobre | Cajamarca 45.01 % | ➖ null | ✅ Cajamarca 45.0 | **mejora** | Skill `limpiando-enaho` |
| E4 Pobreza 0–14 años | 37.52 % | ➖ null | ✅ 37.5 | **mejora** | Skill `limpiando-enaho` |
| C1 Brecha rural-urbana e IPC de alimentos dic-2024 | 14.5 pp; 1.2481 % | ➖ null | ✅ 14.7 pp (14.5 con el método INEI); 1.2 % | **mejora** | `buscar_series`, `serie`, Skill `limpiando-enaho` |
| C2 Alimentos en el gasto de los pobres extremos y pico del IPC de alimentos | 51.69 %; 13.1637 % (feb-2023) | ➖ null | ✅ 51.7 %; 13.2 % en feb-2023 | **mejora** | `buscar_series`, `resumen`, scripts de `limpiando-enaho` por Bash |

✅ correcta · ❌ incorrecta · ➖ no contesta

- **Mejoraron:** 8 preguntas. B2 pasó de incorrecta a correcta. B3, B4, E2, E3, E4, C1 y C2 pasaron de «no contesta» a correctas.
- **Empeoraron:** ninguna.
- **Iguales:** B1 y E1, correctas en ambos modos. En el modo A el modelo las respondió de memoria y lo advirtió.

## Principales errores observados

**Modo A**
- **Alucinación (B2).** Dio un crecimiento del PBI 2024 de 3.3 % «de memoria» cuando el dato del BCRP es 3.52 %. Advirtió que podía estar desactualizado, pero puso la cifra en `valor`, y es la única respuesta incorrecta del experimento.
- **Abstenciones.** En 7 de 10 preguntas puso `null`, como pedía la instrucción, en lugar de estimar. B4 (octubre de 2026) es posterior a lo que sabe el modelo, así que no es posible responderla sin herramientas.
- **Aciertos sin fuente.** Las dos respuestas correctas (B1 y E1) son cifras muy difundidas que el modelo recuerda, pero no puede citarlas con período ni código ni verificarlas.
- **Intento de usar una herramienta (C2).** Intentó usar Bash y la sesión lo rechazó («No such tool available: Bash»). Esto confirma que el modo A no tuvo acceso a archivos ni a datos.

**Modo B**
- **Errores de herramientas resueltos sobre la marcha.** Hubo 3, y ninguno afectó a la respuesta. En E3 y E4, Claude Code rechazó dos comandos de Bash con variables de shell («A variable in this command can't be checked before it runs») y el agente los repitió sin variables. En C2, un `ls salidas` falló (código 2) porque la carpeta todavía no existía.
- **La skill no siempre se invocó con la herramienta Skill.** En C2 el agente leyó `SKILL.md` con `cat` y ejecutó `limpiar.py` y `consultar.py` por Bash. El resultado es el mismo porque usa los mismos scripts validados, pero no pasa por el mecanismo de activación de skills. En E1–E4 y C1 sí usó `Skill:limpiando-enaho`.
- **Código de serie no canónico (B2).** `buscar_series` devolvió primero `PM04908AA`, la fila PBI del cuadro de ingreso nacional disponible, en vez de `PM04923AA`, el PBI por tipo de gasto. El valor es el mismo (3.515 %) y el agente lo verificó con los niveles `PM04935AA`, pero mejorar el orden de `buscar_series` daría citas más limpias.
- **Más lento y más caro.** Tardó 3.6 veces más (25.9 s frente a 7.2 s) y costó 4.3 veces más. Las preguntas de la ENAHO toman unos 33 s porque cada sesión reconstruye y valida la base desde los microdatos: el parquet no se copió a la carpeta de prueba.
- **Precisión de la interpretación.** En C2 la frase «les golpea más que a cualquier otro grupo» va un poco más allá de lo medido (la ENAHO no mide el efecto de la inflación), aunque el agente aclara que son asociaciones descriptivas y que el IPC es de Lima.

## Conclusión

Con las mismas preguntas y el mismo modelo, el MCP del BCRP y las Skills de la ENAHO subieron las respuestas correctas de **2/10 a 10/10**. También eliminaron la única alucinación y convirtieron 7 abstenciones en respuestas con fuente (código de serie y período, o script y base validada). La mejora es mayor justo donde el modelo no puede saber la respuesta: datos posteriores a lo que conoce (B4), cifras poco difundidas (B3, E3, E4) y preguntas que exigen cruzar dos fuentes (C1, C2). El costo es más tiempo y dinero por pregunta, y algunos errores de herramientas que el agente resolvió solo. Sin herramientas, el modelo fue prudente y en general se abstuvo antes que inventar, pero no pudo citar ni verificar ninguna cifra.

**Límites de esta evaluación.**
- Hay una sola corrida por pregunta y modo, con 10 preguntas, sin repeticiones que midan la variabilidad.
- Se usó un solo modelo.
- Las preguntas las diseñamos nosotros a partir de lo que cubren las herramientas.
- La calificación automática de la interpretación tuvo dos falsos positivos y requirió revisión manual.
- Los aciertos del modo A se contaron como correctos aunque no estuvieran verificados.

Para reproducir:

```bash
uv run python evaluacion/respuestas_esperadas.py   # recalcula preguntas.csv (cambia solo si el BCRP revisa una serie)
uv run python evaluacion/evaluar.py                # 20 sesiones; ~2 min con 3 en paralelo
uv run python evaluacion/evaluar.py --solo-calificar   # recalifica desde las trazas guardadas
```
