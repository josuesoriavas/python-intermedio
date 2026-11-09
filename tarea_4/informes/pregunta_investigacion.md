Eres un agente de investigación socioeconómica sobre el Perú. Responde la pregunta de abajo solo con datos oficiales obtenidos con las herramientas de este proyecto, y deja un informe reproducible.

PREGUNTA DE INVESTIGACIÓN
Después de la recesión de 2020 y del pico inflacionario de 2022, ¿cómo evolucionaron entre 2019 y 2024 la actividad económica y la inflación (en especial la de alimentos), y qué brechas territoriales y socioeconómicas de pobreza monetaria, y de peso de los alimentos en el gasto de los hogares, mostraba el Perú en 2024?

CÓMO TRABAJAR
1. Plan. Antes de consultar nada, escribe un plan breve: qué series del BCRP necesitas, qué indicadores de la ENAHO 2024, qué gráficos y qué mapa.
2. BCRP, con el servidor MCP `bcrp`. Identifica los códigos con buscar_series o con el recurso bcrp://series-clave. Obtén las cifras con resumen, serie o comparar_periodos. Genera el gráfico macroeconómico con graficar_serie, que lo guarda en figuras/. No hagas cuentas a mano.
3. ENAHO 2024, con las skills del proyecto. Activa cada una con la herramienta Skill y sigue sus instrucciones; no leas los SKILL.md con cat ni escribas código de análisis propio:
   - limpiando-enaho: asegura una base válida y obtén las cifras ponderadas (pobreza por área, región o grupo; participación de los alimentos en el gasto según condición de pobreza).
   - graficando-enaho: al menos un gráfico de la ENAHO.
   - mapeando-enaho: el mapa departamental de pobreza monetaria.
4. Contraste. Compara tus cifras de la ENAHO con las oficiales que reporta salidas/validacion.txt y con la comparación del mapa contra la referencia del curso (mapas/comparacion_referencia.txt). Di si coinciden y por qué difieren.
5. Informe. Escribe informes/informe_final.md en español con estas secciones:
   1. Pregunta de investigación: tema, objetivo y delimitación (períodos, cobertura geográfica y unidades).
   2. Plan de análisis.
   3. Fuentes y metodología: datos, procesamiento, indicadores, ponderación.
   4. Resultados: al menos 3 hallazgos numerados. Cada cifra va con su fuente: código de serie y período para el BCRP; archivo o script de la skill para la ENAHO.
   5. Visualizaciones: el gráfico del BCRP, al menos un gráfico de la ENAHO y el mapa, insertados en Markdown con rutas relativas desde informes/ (../figuras/..., ../mapas/...) y con una línea de lectura cada uno.
   6. Interpretación: los patrones principales.
   7. Limitaciones: cobertura temporal, niveles de agregación distintos (por ejemplo, IPC de Lima Metropolitana frente a pobreza nacional; series de tiempo frente a un corte transversal de 2024), calidad de los datos y alcance de las conclusiones.
   8. Reproducibilidad: comandos, scripts, archivos y códigos de series usados.
   9. Registro de herramientas: qué herramientas MCP y qué skills usaste, y para qué.

REGLAS
- Cada cifra debe venir de una herramienta (MCP o scripts de las skills), no de tu memoria. No inventes referencias.
- Describe asociaciones, no causas: no afirmes que la inflación o el PBI causaron la pobreza observada.
- Si una herramienta falla, no encuentra datos o devuelve algo incompatible, dilo en el informe en vez de estimar. En Limitaciones, enumera con honestidad los errores de herramientas que hayas tenido durante la ejecución, aunque los hayas resuelto.
- Al final, responde con un resumen de 5 líneas y la lista de archivos que generaste.
