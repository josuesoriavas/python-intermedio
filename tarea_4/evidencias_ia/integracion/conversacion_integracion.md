# Integración del agente e informe

Parte de `conversacion_completa.md` (fase «integracion»).

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\informes\\pregunta_investigacion.md",
 "content": "Eres un agente de investigación socioeconómica sobre el Perú. Responde la pregunta de abajo solo con datos oficiales obtenidos con las herramientas de este proyecto, y deja un informe reproducible.\n\nPREGUNTA DE INVESTIGACIÓN\nDespués de la recesión de 2020 y del pico inflacionario de 2022, ¿cómo evolucionaron entre 2019 y 2024 la actividad económica y la inflación (en especial la de alimentos), y qué brechas territoriales y socioeconómicas de pobreza monetaria, y de peso de los alimentos en el gasto de los hogares, mostraba el Perú en 2024?\n\nCÓMO TRABAJAR\n1. Plan. Antes de consultar nada, escribe un plan breve: qué series del BCRP necesitas, qué indicadores de la ENAHO 2024, qué gráficos y qué mapa.\n2. BCRP, con el servidor MCP `bcrp`. Identifica los códigos con buscar_series o con el recurso bcrp://series-clave. Obtén las cifras con resumen, serie o comparar_periodos. Genera el gráfico macroeconómico con graficar_serie, que lo guarda en figuras/. No hagas cuentas a mano.\n3. ENAHO 2024, con las skills del proyecto:\n   - limpiando-enaho: asegura una base válida y obtén las cifras ponderadas (pobreza por área, región o grupo; participación de los alimentos en el gasto según condición de pobreza).\n   - graficando-enaho: al menos un gráfico de la ENAHO.\n   - mapeando-enaho: el mapa departamental de pobreza monetaria.\n4. Contraste. Compara tus cifras de la ENAHO con las oficiales que reporta salidas/validacion.txt y con la comparación del mapa contra la referencia del curso (mapas/comparacion_referencia.txt). Di si coinciden y por qué difieren.\n5. Informe. Escribe informes/informe_final.md en español con estas secciones:\n   1. Pregunta de investigación: tema, objetivo y delimitación (períodos, cobertura geográfica y unidades).\n   2. Plan de análisis.\n   3. Fuentes y metodología: datos, procesamiento, indicadores, ponderación.\n   4. Resultados: al menos 3 hallazgos numerados. Cada cifra va con su fuente: código de serie y período para el BCRP; archivo o script de la skill para la ENAHO.\n   5. Visualizaciones: el gráfico del BCRP, al menos un gráfico de la ENAHO y el mapa, insertados en Markdown con rutas relativas desde informes/ (../figuras/..., ../mapas/...) y con una línea de lectura cada uno.\n   6. Interpretación: los patrones principales.\n   7. Limitaciones: cobertura temporal, niveles de agregación distinto
… [recortado: 786 caracteres más]
```

**🔧 Bash**

```json
{
 "command": "rm -f figuras/* mapas/* salidas/personas_2024.parquet salidas/hogares_2024.parquet informes/informe_final.md && ls figuras mapas salidas && echo \"limpio\"",
 "description": "Clear generated outputs so the integrated run rebuilds them"
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\SKILL.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\informes\pregunta_investigacion.md (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
figuras:

mapas:

salidas:
indicadores.csv
validacion.txt
limpio
```
</details>

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python scripts/ejecutar_agente.py --modo mcp_skills --modelo sonnet --prompt-file informes/pregunta_investigacion.md --salida evidencias_ia/integracion/01_ejecucion_integrada --timeout 2400 > evidencias_ia/integracion/_consola.txt 2>&1; echo \"exit=$?\" >> evidencias_ia/integracion/_consola.txt",
 "description": "Run the integrated MCP + Skills research agent",
 "run_in_background": true
}
```

<details><summary>resultado</summary>

```text
Command running in background with ID: bfwd8ztjw. Output is being written to: C:\Users\<usuario>\AppData\Local\Temp\claude\4fa6fe550e34c9f1\5744c2ba-c365-40c4-a4c4-547ea7d6a5ba\tasks\bfwd8ztjw.output. You will be notified when it completes — do not poll that file or sleep while waiting. Read the file only if the user asks for progress, or if you need a line it prints before you can go on, such as a server's ready line or port.
```
</details>
