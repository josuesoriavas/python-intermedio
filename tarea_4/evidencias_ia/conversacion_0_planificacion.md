# Planificación y revisión inicial

Parte de `conversacion_completa.md` (fase «planificacion»).

---

### 🧑 Usuario · 2026-11-09 11:36

<pasted_content id="8ed4">
Tarea 4 – Agente de investigación socioeconómica: MCP, Skills y datos oficiales del Perú
Pregunta guía del trabajo
¿Pueden construir un agente de inteligencia artificial capaz de investigar la realidad socioeconómica peruana utilizando datos oficiales del INEI y el BCRP, combinando servidores MCP, Skills de Claude Code y herramientas de análisis reproducible?

En este proyecto desarrollarán un agente de investigación socioeconómica que integre dos fuentes oficiales de información:

INEI – ENAHO 2024: microdatos para estudiar pobreza monetaria, desigualdades territoriales y características socioeconómicas de la población.

BCRP – Series estadísticas: indicadores macroeconómicos para analizar inflación, actividad económica, tipo de cambio u otras variables relevantes.

El agente deberá interpretar preguntas formuladas en lenguaje natural, consultar las fuentes correspondientes, procesar los datos, ejecutar cálculos verificables y producir gráficos, mapas e informes.

El objetivo principal no es construir un chatbot que responda utilizando únicamente su conocimiento previo, sino un sistema que utilice herramientas especializadas para producir respuestas verificables y reproducibles.

📌 Instrucciones generales
El trabajo es individual y corresponde a la Tarea 4 del curso Python Intermedio.

1. Materiales de referencia
El proyecto deberá integrar los contenidos de las siguientes sesiones:

Sesión 04 – MCP: Claude conectado a sus datos

https://github.com/d2cml-ai/Data-Science-Python/tree/main/sessions/04-mcp-claude-code

Sesión 16 – Skills de Claude Code: limpiar, graficar y mapear la ENAHO

https://github.com/d2cml-ai/Data-Science-Python/tree/main/sessions/16-skills-enaho

Los estudiantes deberán utilizar como referencia los ejemplos de FastMCP, las pruebas del servidor BCRP y las reglas de procesamiento de la ENAHO.

No será suficiente copiar y ejecutar los proyectos de las sesiones por separado. La tarea exige integrarlos en un agente funcional, desarrollar componentes propios y evaluar su desempeño.

2. Herramientas y tecnologías
Se utilizarán:

Claude Code: agente principal para coordinar el proyecto.

Python y uv: desarrollo y gestión del entorno.

FastMCP: construcción del servidor MCP.

Pandas y PyArrow: procesamiento de microdatos.

GeoPandas: análisis y representación territorial.

Matplotlib o Plotly: generación de visualizaciones.

Pytest: pruebas automatizadas.

Git y GitHub: versionamiento, documentación y entrega.

Pueden incorporar otras bibliotecas o herramientas cuando su utilización esté justificada.

3. Datos obligatorios
Fuente | Datos | Uso -- | -- | -- INEI | ENAHO 2024, módulo 34 (sumaria) | Pobreza e indicadores de hogares INEI | ENAHO 2024, módulo 02 (miembros) | Características individuales Repositorio del curso | Límites departamentales del Perú | Mapas territoriales BCRP | Series estadísticas oficiales | Análisis macroeconómico
La penalización se aplicará sobre la nota obtenida según la rúbrica de 20 puntos, sin que la calificación final pueda ser inferior a 0.

Se recomienda comprobar con anticipación que:

El repositorio y todos los enlaces sean accesibles.

Los scripts, pruebas y resultados estén correctamente guardados.

Las evidencias del uso de IA estén completas.

No se hayan publicado credenciales ni información sensible.

El comentario de entrega se haya registrado correctamente dentro del plazo.

🎯 Resultado esperado
Al finalizar esta tarea, cada estudiante deberá contar con un agente de investigación socioeconómica funcional, capaz de consultar información oficial del BCRP mediante MCP, procesar y analizar microdatos de ENAHO mediante Skills y elaborar informes con resultados verificables.

El proyecto estará completo cuando el agente pueda responder una pregunta real utilizando ambas herramientas, y cuando otra persona pueda reproducir, evaluar y comprobar los resultados obtenidos.

El propósito es desarrollar competencias para construir sistemas de inteligencia artificial que no se limiten a generar respuestas, sino que sean capaces de utilizar herramientas, ejecutar procedimientos reproducibles y producir evidencia confiable para el análisis de datos y la investigación social.

¡Éxitos con sus proyectos! 🚀

# 🤖 Tarea 4 – Agente de investigación socioeconómica: MCP, Skills y datos oficiales del Perú
Pregunta guía del trabajo
¿Pueden construir un agente de inteligencia artificial capaz de investigar la realidad socioeconómica peruana utilizando datos oficiales del INEI y el BCRP, combinando servidores MCP, Skills de Claude Code y herramientas de análisis reproducible?

En este proyecto desarrollarán un agente de investigación socioeconómica que integre dos fuentes oficiales de información:

INEI – ENAHO 2024: microdatos para estudiar pobreza monetaria, desigualdades territoriales y características socioeconómicas de la población.
BCRP – Series estadísticas: indicadores macroeconómicos para analizar inflación, actividad económica, tipo de cambio u otras variables relevantes.
El agente deberá interpretar preguntas formuladas en lenguaje natural, consultar las fuentes correspondientes, procesar los datos, ejecutar cálculos verificables y producir gráficos, mapas e informes.

El objetivo principal no es construir un chatbot que responda utilizando únicamente su conocimiento previo, sino un sistema que utilice herramientas especializadas para producir respuestas verificables y reproducibles.

📌 Instrucciones generales
El trabajo es individual y corresponde a la Tarea 4 del curso Python Intermedio.

1. Materiales de referencia
El proyecto deberá integrar los contenidos de las siguientes sesiones:

Sesión 04 – MCP: Claude conectado a sus datos

https://github.com/d2cml-ai/Data-Science-Python/tree/main/sessions/04-mcp-claude-code

Sesión 16 – Skills de Claude Code: limpiar, graficar y mapear la ENAHO

https://github.com/d2cml-ai/Data-Science-Python/tree/main/sessions/16-skills-enaho

Los estudiantes deberán utilizar como referencia los ejemplos de FastMCP, las pruebas del servidor BCRP y las reglas de procesamiento de la ENAHO.

No será suficiente copiar y ejecutar los proyectos de las sesiones por separado. La tarea exige integrarlos en un agente funcional, desarrollar componentes propios y evaluar su desempeño.

2. Herramientas y tecnologías
Se utilizarán:

Claude Code: agente principal para coordinar el proyecto.
Python y uv: desarrollo y gestión del entorno.
FastMCP: construcción del servidor MCP.
Pandas y PyArrow: procesamiento de microdatos.
GeoPandas: análisis y representación territorial.
Matplotlib o Plotly: generación de visualizaciones.
Pytest: pruebas automatizadas.
Git y GitHub: versionamiento, documentación y entrega.
Pueden incorporar otras bibliotecas o herramientas cuando su utilización esté justificada.

3. Datos obligatorios
Fuente	Datos	Uso
INEI	ENAHO 2024, módulo 34 (sumaria)	Pobreza e indicadores de hogares
INEI	ENAHO 2024, módulo 02 (miembros)	Características individuales
Repositorio del curso	Límites departamentales del Perú	Mapas territoriales
BCRP	Series estadísticas oficiales	Análisis macroeconómico
Enlaces de referencia:

[ENAHO 2024 – Módulo 34](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip)
[ENAHO 2024 – Módulo 02](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip)
[GeoJSON departamental del Perú](https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson)
[Estadísticas del BCRP](https://estadisticas.bcrp.gob.pe/estadisticas/series/)
Valores de referencia para validar ENAHO 2024:

Indicador	Referencia
Pobreza monetaria nacional	Aproximadamente 27.6 %
Residentes habituales	108,664
Unidades territoriales del mapa	25
Pobreza urbana	Aproximadamente 24.8 %
Pobreza rural	Aproximadamente 39.3 %
Las estimaciones deberán reproducir razonablemente las cifras de referencia, admitiendo diferencias de redondeo y ponderación debidamente explicadas. Para la pobreza nacional se aceptará una diferencia máxima de 0.1 puntos porcentuales respecto del 27.6 % de referencia.

Important

Los cálculos de ENAHO deben aplicar correctamente los factores de expansión y respetar la unidad de análisis. No se aceptarán promedios simples cuando corresponda una estimación ponderada.

Tampoco se deberán presentar asociaciones descriptivas como relaciones causales demostradas.

Las cifras no pueden introducirse manualmente como resultados: deben obtenerse mediante el procesamiento de los datos y validarse posteriormente.

🤖 Uso de inteligencia artificial y evidencias de desarrollo
Se permite y fomenta el uso de herramientas de inteligencia artificial durante todas las etapas del proyecto.

Los estudiantes podrán utilizar Claude Code, ChatGPT, Codex, OpenCode, Gemini u otros asistentes para:

Desarrollar y depurar código en Python.
Configurar servidores MCP.
Crear, modificar y ejecutar Skills.
Procesar datos y elaborar visualizaciones.
Diseñar pruebas automatizadas.
Identificar y corregir errores.
Interpretar resultados y preparar el informe final.
No se evaluará cuánto código escribieron manualmente, sino la funcionalidad, calidad técnica, reproducibilidad y validez de los resultados.

Sin embargo, cada estudiante deberá comprender el funcionamiento de su proyecto, verificar sus resultados y garantizar que los componentes desarrollados cumplan los requisitos establecidos.

Evidencias obligatorias
Como requisito de entrega, deberán presentar el registro completo de las conversaciones utilizadas con asistentes de inteligencia artificial durante el desarrollo del proyecto, mediante una de las siguientes modalidades:

Opción A – Capturas de pantalla

Capturas legibles de las conversaciones completas.
Archivos numerados y organizados cronológicamente.
Deben permitir identificar las instrucciones proporcionadas y las respuestas del asistente.
Opción B – Exportación de conversaciones

Exportación del historial completo de las sesiones utilizadas.
Se aceptarán formatos como Markdown, TXT, JSON o HTML.
Los archivos deben permitir reconstruir el proceso de desarrollo.
En ambos casos, las evidencias deberán abarcar el desarrollo del servidor MCP, las Skills, la integración del agente, las pruebas, las correcciones y el informe final.

Todos los archivos deberán almacenarse en una carpeta evidencias_ia/ dentro del repositorio. Si el tamaño impide subirlos a GitHub, se podrá incluir un enlace público a una carpeta externa que contenga las evidencias completas.

Warning

Antes de publicar las conversaciones, deberán ocultar claves API, contraseñas, tokens, datos personales e información confidencial.

No se aceptarán únicamente capturas aisladas de los resultados finales como sustituto del historial de desarrollo.

La documentación del uso de IA es obligatoria y será considerada en la evaluación de documentación y reproducibilidad.

🗂️ Organización del repositorio
Cada estudiante deberá crear una carpeta tarea_4/ dentro de su repositorio del curso o utilizar un repositorio público independiente.

La estructura esperada es:

tarea_4/
├── README.md
├── pyproject.toml
├── .mcp.json
├── .gitignore
│
├── mcp/
│   ├── server.py
│   └── test_server.py
│
├── .claude/
│   └── skills/
│       ├── limpiando-enaho/
│       │   ├── SKILL.md
│       │   ├── reference.md
│       │   └── scripts/
│       │       └── limpiar.py
│       │
│       ├── graficando-enaho/
│       │   ├── SKILL.md
│       │   └── scripts/
│       │
│       └── mapeando-enaho/
│           ├── SKILL.md
│           └── scripts/
│
├── datos/
│   └── (microdatos originales ignorados por Git)
│
├── salidas/
│   ├── validacion.txt
│   └── indicadores.csv
│
├── figuras/
├── mapas/
│
├── evaluacion/
│   ├── preguntas.csv
│   ├── resultados.csv
│   └── comparacion.md
│
├── informes/
│   └── informe_final.md
│
└── evidencias_ia/
    ├── mcp/
    ├── skills/
    ├── integracion/
    └── evaluacion/
La organización puede adaptarse a las necesidades del proyecto, siempre que los archivos obligatorios sean identificables y el sistema pueda ejecutarse siguiendo las instrucciones del README.

No deben subirse microdatos originales pesados, archivos temporales, credenciales ni información sensible. Los datos originales deberán incluirse en .gitignore, y el README deberá explicar cómo descargarlos y reproducir el procesamiento.

Las evidencias del uso de IA deben mantenerse separadas de los datos originales y de los archivos de resultados.

Flujo de trabajo en GitHub
Se espera que los estudiantes:

Utilicen Git para registrar el desarrollo.
Realicen commits descriptivos a medida que avanzan.
Mantengan los archivos del proyecto organizados.
Documenten los requisitos, dependencias e instrucciones de ejecución.
Publiquen un repositorio accesible para su revisión.
📊 Criterios de calificación (sobre 20 puntos)
Componente	Puntos
Parte 1 – Servidor MCP del BCRP	5 pts
Parte 2 – Skills para procesar y analizar ENAHO	6 pts
Parte 3 – Integración y agente de investigación	5 pts
Parte 4 – Evaluación, documentación y reproducibilidad	4 pts
Total	20 pts
🔌 Parte 1 – Servidor MCP del BCRP [5 pts]
El primer componente consiste en implementar un servidor MCP funcional que permita a Claude Code consultar series estadísticas oficiales del Banco Central de Reserva del Perú.

Archivo principal: mcp/server.py
Pasos requeridos
1. Construcción del servidor

Tomar como referencia el proyecto de la Sesión 04:

https://github.com/d2cml-ai/Data-Science-Python/tree/main/sessions/04-mcp-claude-code/proyecto

Completar y adaptar server.py, implementando como mínimo cuatro herramientas:

Herramienta	Función
buscar_series	Encontrar series oficiales mediante palabras clave
serie	Descargar datos de una serie para un período determinado
resumen	Calcular variaciones, promedios, mínimos y máximos
Herramienta propia	Incorporar una funcionalidad adicional de análisis
La herramienta propia deberá ser útil y no limitarse a duplicar las funciones anteriores.

Por ejemplo:

comparar_series: comparar dos indicadores en períodos compatibles.
correlacion: calcular la correlación entre series, alineando períodos y tratando valores faltantes.
graficar_serie: generar y guardar un gráfico de una serie oficial.
comparar_periodos: comparar el comportamiento de un indicador entre dos intervalos.
Los cálculos numéricos deberán realizarse mediante código Python y no mediante estimaciones improvisadas del modelo de lenguaje.

2. Recursos y prompts MCP

Implementar como mínimo:

Un recurso MCP que permita consultar información descriptiva de una serie.
Un prompt MCP reutilizable para generar informes o interpretar indicadores.
Ambos deberán ser accesibles desde el cliente MCP utilizado.

3. Integración con Claude Code

Configurar el servidor mediante .mcp.json y demostrar su funcionamiento desde Claude Code.

El agente deberá poder:

Identificar una serie estadística.
Solicitar los datos correspondientes.
Ejecutar cálculos mediante las herramientas.
Presentar el resultado con su código de serie, período y fuente.
4. Pruebas automatizadas

El servidor deberá superar:

Las 8 pruebas originales del proyecto de la Sesión 04.
2 pruebas adicionales diseñadas por el estudiante para evaluar su herramienta propia.
Las pruebas originales no deberán modificarse para facilitar su aprobación. Solo podrán realizarse los ajustes de importación necesarios si cambia la ubicación de los archivos.

El resultado esperado será:

10 passed
Rúbrica Parte 1 [5 pts]
Criterio	Pts
Servidor funcional con búsqueda, consulta y resumen de series	2.0
Herramienta propia útil, validada y documentada	1.0
Recurso, prompt e integración efectiva con Claude Code	1.0
10 pruebas automatizadas aprobadas	1.0
Total	5.0
📊 Parte 2 – Skills para procesar y analizar ENAHO [6 pts]
El segundo componente consiste en desarrollar tres Skills reutilizables siguiendo la metodología de la Sesión 16.

No será suficiente escribir las instrucciones en SKILL.md. Cada Skill deberá ejecutar código funcional y generar resultados verificables.

Skill 1 – limpiando-enaho
Desarrollar una Skill capaz de:

Leer los módulos 34 y 02 de ENAHO 2024.
Normalizar los nombres de las variables.
Filtrar residentes habituales.
Unir correctamente personas y hogares utilizando las llaves conglome, vivienda y hogar.
Construir indicadores de pobreza, departamento y área geográfica.
Aplicar los factores de expansión correspondientes.
Ejecutar validaciones y generar salidas/validacion.txt.
Reglas técnicas
La lectura de los archivos Stata deberá respetar los tipos de datos de las llaves, evitando perder ceros iniciales.

El filtro de residentes habituales seguirá la condición utilizada en la sesión:

((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))
La unión entre la base de personas y hogares deberá utilizar:

merge(..., validate="m:1")
La Skill deberá verificar que la unión no genere duplicaciones inesperadas.

Validaciones mínimas
Pobreza monetaria nacional cercana a 27.6 %.
108,664 residentes habituales.
Identificación correcta de los 25 códigos territoriales.
Ninguna duplicación indebida de registros.
Aplicación correcta de los factores de expansión.
El archivo validacion.txt deberá mostrar los resultados y señalar las verificaciones aprobadas y fallidas.

Si una validación esencial falla, la Skill deberá detener el proceso o devolver un mensaje de error explícito. No se aceptará corregir artificialmente los resultados para que coincidan con los valores de referencia.

Skill 2 – graficando-enaho
Desarrollar una Skill que produzca visualizaciones a partir de los datos procesados.

Deberá permitir solicitar gráficos mediante lenguaje natural y generar, como mínimo:

Pobreza monetaria según área urbana y rural.
Pobreza por sexo u otro grupo demográfico pertinente.
Comparación de pobreza entre departamentos.
Requisitos de visualización
Utilizar estimaciones ponderadas.
Presentar títulos claros y analíticos.
Identificar el período y las unidades.
Incluir la fuente de información.
Utilizar escalas y representaciones apropiadas.
Guardar los resultados en figuras/.
Los gráficos deberán permitir interpretar diferencias reales y no limitarse a mostrar datos sin contexto.

Skill 3 – mapeando-enaho
Desarrollar una Skill capaz de construir un mapa coroplético de pobreza monetaria departamental.

Requisitos
Unir los indicadores y las geometrías mediante códigos territoriales.
Utilizar ubigeo[:2] y FIRST_IDDP como llaves de referencia.
Representar las 25 unidades territoriales.
Mantener Lima y Callao separados.
Incorporar una escala de colores interpretable.
Mostrar la unidad de medida en la leyenda.
Comparar los resultados con el archivo de referencia de la Sesión 16.
El mapa deberá guardarse en mapas/.

No se aceptarán uniones realizadas únicamente por nombres de departamentos cuando exista una llave oficial de identificación.

Activación y coordinación de las Skills
Las tres Skills deberán encontrarse dentro de .claude/skills/ y contar con un archivo SKILL.md correctamente estructurado.

Se deberá demostrar que:

Pueden invocarse individualmente.
Pueden activarse mediante solicitudes en lenguaje natural.
Las Skills de gráficos y mapas pueden ejecutar previamente la Skill de limpieza cuando no exista la base procesada.
Por ejemplo, ante el pedido:

Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.

Claude Code deberá identificar que necesita una base procesada y, si esta no existe, ejecutar primero limpiando-enaho y después mapeando-enaho.

Rúbrica Parte 2 [6 pts]
Criterio	Pts
Skill de limpieza funcional, ponderación y validación de ENAHO	2.5
Skill de gráficos con indicadores correctos	1.5
Skill de mapas con unión territorial y 25 unidades	1.5
Activación automática y coordinación entre Skills	0.5
Total	6.0
🧠 Parte 3 – Agente de investigación socioeconómica [5 pts]
Esta es la parte central e integradora del proyecto.

El estudiante deberá construir un flujo de trabajo en el que Claude Code utilice coordinadamente el servidor MCP del BCRP y las Skills de ENAHO para desarrollar una investigación breve sobre la economía y las condiciones sociales del Perú.

1. Formulación de la pregunta de investigación
Cada estudiante deberá formular una pregunta propia que requiera información de ambas fuentes oficiales.

Ejemplo:

¿Cómo evolucionó la inflación peruana entre 2020 y 2024 y qué diferencias territoriales presentaba la pobreza monetaria al finalizar ese período?

Otros temas posibles:

Evolución de la actividad económica y características territoriales de la pobreza.
Inflación y diferencias socioeconómicas entre áreas urbanas y rurales.
Evolución de indicadores macroeconómicos y desigualdades regionales.
Tipo de cambio, precios y características de los hogares peruanos.
Los estudiantes podrán elegir otros temas, siempre que sean compatibles con las fuentes y permitan formular un análisis coherente.

Important

No se exige demostrar una relación causal entre las variables macroeconómicas y la pobreza. Si se utilizan datos de diferentes niveles de agregación o períodos, el informe deberá reconocer esas limitaciones.

No se aceptarán preguntas que utilicen únicamente el BCRP o únicamente ENAHO.

2. Ejecución del agente
El agente deberá realizar las siguientes operaciones:

Interpretar la pregunta y preparar un plan de análisis.
Consultar las series oficiales necesarias mediante el MCP.
Ejecutar las Skills de procesamiento y análisis de ENAHO.
Construir indicadores y visualizaciones.
Contrastar los resultados con las fuentes oficiales.
Elaborar un informe final reproducible.
Condición obligatoria de integración
En una misma ejecución demostrable deberán utilizarse:

Al menos 2 herramientas MCP distintas.
Al menos 2 Skills distintas.
No se aceptará ejecutar ambos proyectos de manera completamente independiente y luego copiar manualmente los resultados a un documento.

La evidencia deberá mostrar que Claude Code coordinó las herramientas necesarias para completar la investigación.

3. Informe final de investigación
El agente deberá generar:

informes/informe_final.md

El documento deberá contener:

Pregunta de investigación: tema, objetivo y delimitación del análisis.
Fuentes y metodología: datos utilizados, procesamiento e indicadores.
Resultados: al menos 3 hallazgos sustentados.
Visualizaciones: un gráfico del BCRP, un gráfico elaborado con ENAHO y un mapa departamental.
Interpretación: explicación de los principales patrones identificados.
Limitaciones: cobertura temporal, calidad de los datos y alcance de las conclusiones.
Reproducibilidad: referencias a los scripts, archivos y series utilizadas.
Todas las cifras deberán poder rastrearse hasta la fuente original o el procesamiento correspondiente.

No se aceptarán afirmaciones numéricas sin sustento o referencias inventadas.

4. Verificación de resultados
El estudiante deberá comprobar manualmente al menos 3 afirmaciones numéricas del informe, incluyendo resultados provenientes de ambas fuentes.

Deberá documentar:

La afirmación del informe.
El valor calculado.
La fuente o procedimiento de verificación.
Si el resultado coincide con la referencia.
Cualquier diferencia observada.
Cuando una herramienta falle, no encuentre datos o devuelva una respuesta incompatible, el agente deberá informar esa limitación en lugar de inventar resultados.

Rúbrica Parte 3 [5 pts]
Criterio	Pts
Pregunta pertinente y planificación coherente	0.5
Orquestación real de MCP y Skills en una ejecución	2.0
Informe con tres hallazgos, gráficos, mapa e interpretación	1.5
Verificación de cifras y manejo de errores	1.0
Total	5.0
🧪 Parte 4 – Evaluación, documentación y reproducibilidad [4 pts]
El último componente consiste en evaluar si el uso de MCP y Skills mejora la calidad de las respuestas producidas por Claude Code.

La evaluación deberá utilizar preguntas con respuestas verificables, comparar condiciones equivalentes y documentar los resultados.

1. Diseño del experimento
Construir un conjunto de 10 preguntas de evaluación:

Tipo de pregunta	Cantidad
Indicadores del BCRP	4
Indicadores de ENAHO	4
Preguntas que combinan ambas fuentes	2
Total	10
Las preguntas deberán tener respuestas esperadas verificadas mediante fuentes oficiales o cálculos independientes.

No se aceptarán preguntas cuyas respuestas correctas hayan sido inventadas o definidas únicamente a partir de lo que respondió el agente.

Guardar el conjunto de preguntas en:

evaluacion/preguntas.csv

2. Comparación de dos configuraciones
Cada estudiante deberá ejecutar las mismas 10 preguntas bajo dos condiciones.

Modo A – Sin MCP ni Skills personalizados
Claude Code deberá responder sin acceso al servidor MCP desarrollado ni a las Skills del proyecto.

Este modo permitirá observar su desempeño sin los componentes especializados.

Modo B – Con MCP y Skills
Claude Code dispondrá del servidor MCP y las Skills desarrolladas.

Deberá poder consultar fuentes, procesar datos y ejecutar cálculos mediante esas herramientas.

Condiciones del experimento
Utilizar las mismas 10 preguntas.
Mantener, en lo posible, el mismo modelo y las mismas instrucciones.
Ejecutar las preguntas en sesiones independientes para evitar que respuestas anteriores contaminen la comparación.
Documentar qué otras herramientas estaban habilitadas en cada modo.
Evitar que el modo sin herramientas personalizadas acceda indirectamente a archivos con las respuestas ya calculadas.
No modificar las respuestas esperadas después de observar los resultados.
3. Métricas de evaluación
Para cada pregunta registrar:

Pregunta formulada.
Respuesta esperada.
Respuesta generada.
Fuente utilizada.
Herramientas efectivamente utilizadas.
Corrección del resultado según una tolerancia definida previamente.
Tiempo de ejecución.
Errores o ausencia de respuesta.
Para las preguntas que combinan ambas fuentes, establecer criterios que consideren tanto la exactitud de los datos como la coherencia de la interpretación.

Los resultados deberán guardarse en:

evaluacion/resultados.csv

El archivo evaluacion/comparacion.md deberá presentar una comparación entre ambos modos, indicando:

Cantidad de respuestas correctas.
Respuestas incorrectas o no contestadas.
Tiempo promedio de ejecución.
Preguntas que mejoraron o empeoraron.
Principales errores encontrados.
Conclusión sobre la utilidad de MCP y Skills.
No es obligatorio que el agente obtenga 10/10 ni que mejore una cantidad determinada de respuestas. Se evaluará la calidad y reproducibilidad del experimento, así como la capacidad de explicar sus resultados.

4. Documentación y reproducibilidad
El archivo README.md deberá contener:

Objetivo del proyecto.
Arquitectura general del agente.
Descripción de las herramientas MCP.
Descripción de las tres Skills.
Fuentes y enlaces para descargar los datos.
Procedimiento de instalación con uv.
Instrucciones para conectar el MCP a Claude Code.
Comandos para reproducir el procesamiento y las pruebas.
Resultados de la evaluación.
Limitaciones y problemas encontrados.
Ejemplo de una ejecución completa.
Referencia a las evidencias del uso de inteligencia artificial.
El repositorio deberá incluir las salidas necesarias para comprobar que el sistema fue ejecutado.

Las conversaciones completas con los asistentes de IA deberán estar disponibles en evidencias_ia/ o mediante un enlace público incluido en el README, con la información sensible previamente ocultada.

Rúbrica Parte 4 [4 pts]
Criterio	Pts
Diseño de 10 preguntas y respuestas esperadas verificables	1.0
Experimento comparativo ejecutado en ambos modos	1.5
Análisis de aciertos, errores, uso de herramientas y tiempo	0.5
README, reproducibilidad y evidencias completas del uso de IA	1.0
Total	4.0
💡 Ideas de innovación (opcionales)
Los estudiantes que hayan completado los requisitos principales podrán incorporar mejoras como:

Crear una Skill adicional para generar automáticamente informes socioeconómicos.
Integrar un segundo MCP con otra fuente oficial de datos.
Diseñar mecanismos para detectar inconsistencias entre resultados de diferentes herramientas.
Construir un dashboard para explorar los resultados generados por el agente.
Implementar pruebas de robustez frente a solicitudes ambiguas o datos inexistentes.
Incorporar análisis de cómo cambia la calidad de las respuestas al desactivar determinadas herramientas.
Automatizar la elaboración de informes con tablas, gráficos y referencias.
Estas mejoras podrán contribuir a obtener la máxima calificación dentro de los criterios establecidos, pero no sustituyen los requisitos obligatorios ni garantizan puntos adicionales fuera de la rúbrica.

✅ Lista de verificación antes de entregar
Servidor MCP

El servidor MCP funciona y cuenta con las cuatro herramientas requeridas.

Incluye un recurso y un prompt funcionales.

Supera las 8 pruebas originales y las 2 pruebas adicionales.

El archivo .mcp.json permite conectarlo a Claude Code.

Las consultas devuelven datos de fuentes oficiales verificables.
Skills de ENAHO

Existen las tres Skills solicitadas con sus archivos SKILL.md.

La limpieza reproduce las validaciones de ENAHO 2024.

Los indicadores utilizan los factores de expansión adecuados.

Los gráficos contienen títulos, unidades y fuentes.

El mapa representa las 25 unidades territoriales.

Las Skills pueden activarse y coordinarse correctamente.
Integración del agente

El agente utiliza efectivamente MCP y Skills en una misma ejecución.

La pregunta de investigación requiere información del BCRP y ENAHO.

Existe un informe con al menos 3 hallazgos sustentados.

El informe contiene un gráfico del BCRP, un gráfico de ENAHO y un mapa.

Se verificaron manualmente al menos 3 afirmaciones numéricas.
Evaluación y documentación

Se construyeron 10 preguntas de evaluación.

Se ejecutó la comparación con y sin MCP/Skills.

Los resultados están documentados en archivos reproducibles.

El README incluye instalación, arquitectura y procedimiento de ejecución.

El repositorio es público y sus enlaces funcionan.
Uso de inteligencia artificial

Se adjuntaron capturas completas o exportaciones de las conversaciones utilizadas.

Las evidencias están organizadas en evidencias_ia/ o mediante un enlace público.

Los registros permiten revisar el proceso de desarrollo del MCP, las Skills, la integración y la evaluación.

Se ocultaron claves API, contraseñas, tokens y datos personales.
📤 Formato y canal de entrega
Cada estudiante deberá publicar un comentario en este Issue utilizando el siguiente formato:

### Tarea 4 – Individual

**Estudiante:** Nombre completo (@usuario_github)

**Pregunta de investigación:** ...

**Repositorio de GitHub:** https://github.com/...

**Informe final:** https://github.com/.../informes/informe_final.md

**Pruebas MCP:** XX/10 aprobadas

**Validación ENAHO:**
- Pobreza nacional 2024: XX.X %
- Residentes habituales: XX,XXX
- Unidades territoriales procesadas: XX/25

**Evaluación del agente:**
- Sin MCP/Skills: X/10 respuestas correctas
- Con MCP/Skills: X/10 respuestas correctas
- Resultados completos: https://github.com/.../evaluacion/resultados.csv

**Evidencia de integración MCP + Skills:** https://github.com/...

**Evidencias de uso de IA:** https://github.com/...
Precisiones sobre la entrega
Repositorio de GitHub: deberá contener el código, las configuraciones, las Skills y los resultados.
Informe final: enlace directo al documento de investigación desarrollado con el agente.
Pruebas MCP: cantidad de pruebas automatizadas aprobadas, respaldada por el código y su ejecución.
Validación ENAHO: resultados calculados mediante el procesamiento de los microdatos.
Evaluación del agente: resultados obtenidos al ejecutar las mismas diez preguntas en las dos condiciones.
Evidencia de integración: registro o demostración de una ejecución en la que Claude Code utilice conjuntamente MCP y Skills.
Evidencias de uso de IA: capturas completas o exportaciones de las conversaciones utilizadas durante el desarrollo.
No será necesario adjuntar nuevamente los microdatos originales de ENAHO, siempre que se proporcionen instrucciones reproducibles para obtenerlos.

Todos los enlaces deberán ser públicos y accesibles sin solicitar permisos adicionales.

⏰ Fecha límite de entrega
Domingo 8 de noviembre de 2026, hasta las 11:59 p. m. (hora de Perú / UTC-5).

La entrega deberá realizarse mediante un comentario en este Issue de GitHub, siguiendo el formato establecido y proporcionando todos los enlaces solicitados.

Política de entregas fuera de plazo
Important

No se aceptarán trabajos presentados después de la fecha límite sin una justificación debidamente sustentada.

Las entregas tardías únicamente podrán ser consideradas de manera excepcional, previa evaluación y autorización del equipo docente.

En caso de autorizarse una entrega fuera de plazo, se aplicará una penalización de 2 puntos sobre la calificación final por cada día de retraso.

La presentación de una justificación no garantiza la aceptación de la entrega tardía. Cada caso será evaluado individualmente por el equipo docente.

Para aplicar la penalización, se contabilizará cada período de 24 horas de retraso iniciado después del vencimiento del plazo. Cualquier fracción de un nuevo período se considerará un día adicional.

Ejemplo: Para un trabajo que obtiene 18/20 según la rúbrica:

Retraso	Penalización	Nota final
1 día	−2	16
2 días	−4	14
3 días	−6	12
4 días	−8	10
La penalización se aplicará sobre la nota obtenida según la rúbrica de 20 puntos, sin que la calificación final pueda ser inferior a 0.

Se recomienda comprobar con anticipación que:

El repositorio y todos los enlaces sean accesibles.
Los scripts, pruebas y resultados estén correctamente guardados.
Las evidencias del uso de IA estén completas.
No se hayan publicado credenciales ni información sensible.
El comentario de entrega se haya registrado correctamente dentro del plazo.
</pasted_content id="8ed4">

 tenemos esta tarea, la podemos hacer?

**🔧 mcp__ccd_turn__update_plan**

```json
{
 "items": [
  {
   "content": "Revisar el repo y las tareas anteriores",
   "status": "in_progress"
  },
  {
   "content": "Comprobar acceso a INEI, BCRP y material del curso",
   "status": "pending"
  },
  {
   "content": "Evaluar viabilidad y proponer plan",
   "status": "pending"
  }
 ],
 "scope": "first_task"
}
```

<details><summary>resultado</summary>

```text
Plan shown (3 steps).
```
</details>

**🔧 Bash**

```json
{
 "command": "ls -la && echo \"---\" && ls tarea_* 2>/dev/null | head -50 && echo \"---\" && git remote -v && echo \"---\" && (uv --version; python --version; claude --version; gh --version | head -1) 2>&1",
 "description": "List repo contents and check installed tools"
}
```

<details><summary>resultado</summary>

```text
total 29
drwxr-xr-x 1 <usuario> 197121  0 Nov  1 22:32 .
drwxr-xr-x 1 <usuario> 197121  0 Oct 28 21:21 ..
drwxr-xr-x 1 <usuario> 197121  0 Nov  1 22:31 .claude
drwxr-xr-x 1 <usuario> 197121  0 Nov  1 22:58 .git
-rw-r--r-- 1 <usuario> 197121 71 Oct 18 19:03 .gitignore
-rw-r--r-- 1 <usuario> 197121  0 Nov  1 22:32 .nojekyll
drwxr-xr-x 1 <usuario> 197121  0 Oct 18 19:00 .venv
drwxr-xr-x 1 <usuario> 197121  0 Oct 18 20:08 tarea_1
drwxr-xr-x 1 <usuario> 197121  0 Oct 25 19:37 tarea_2
drwxr-xr-x 1 <usuario> 197121  0 Nov  1 22:57 tarea_3
---
tarea_1:
01_recoleccion.ipynb
02_clasificacion.ipynb
README.md
app.py
datos
modelo
requirements.txt

tarea_2:
01_extraccion.ipynb
02_evaluacion.ipynb
README.md
app.py
datos
descargar_datos.py
evidencias_ia
herramientas.py
modelos
requirements-notebooks.txt
requirements.txt
voz.py

tarea_3:
README.md
capturas
datos
reel
requirements.txt
scripts
web
---
origin	https://github.com/josuesoriavas/python-intermedio.git (fetch)
origin	https://github.com/josuesoriavas/python-intermedio.git (push)
---
uv 0.12.18 (01cb90c1a 2026-09-22 x86_64-pc-windows-msvc)
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
2.1.314 (Claude Code)
gh version 2.102.0 (2026-09-30)
```
</details>

**🔧 mcp__ccd_turn__update_plan**

```json
{
 "advance": true
}
```

<details><summary>resultado</summary>

```text
Plan updated: step 2 of 3 is in progress.
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio\necho \"== INEI mod34 ==\"; curl -sIL --max-time 30 \"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip\" | grep -iE \"^(HTTP|content-length|content-type)\" \necho \"== INEI mod02 ==\"; curl -sIL --max-time 30 \"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip\" | grep -iE \"^(HTTP|content-length|content-type)\"\necho \"== BCRP API ==\"; curl -s --max-time 30 \"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2024-1/2024-3\" | head -c 400; echo\necho \"== GeoJSON ==\"; curl -sI --max-time 30 \"https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson\" | grep -iE \"^(HTTP|content-length)\"\necho \"== Sesion 04 ==\"; gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/04-mcp-claude-code/proyecto --jq '.[].name' 2>&1 | head -30\necho \"== Sesion 16 ==\"; gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho --jq '.[].name' 2>&1 | head -30",
 "description": "Check access to INEI, BCRP, GeoJSON and course sessions",
 "timeout": 180000
}
```

<details><summary>resultado</summary>

```text
== INEI mod34 ==
HTTP/1.1 200 OK
Content-Length: 15935617
Content-Type: application/x-zip-compressed
== INEI mod02 ==
HTTP/1.1 200 OK
Content-Length: 5793097
Content-Type: application/x-zip-compressed
== BCRP API ==
{
"config":
{
"title":"Índice de precios Lima Metropolitana (var% 12 meses)",
"series":
[
{
"name":"Índice de precios Lima Metropolitana (var% 12 meses) - IPC",
"dec":"2"
}]
},
"periods":
[
{
"name":"Ene.2024",
"values":["3.02392174826855"]
},
{
"name":"Feb.2024",
"values":["3.29406696032184"]
},
{
"name":"Mar.2024",
"values":["3.04504592593905"]
}
]
}
== GeoJSON ==
HTTP/1.1 200 OK
Content-Length: 139681
== Sesion 04 ==
.gitignore
README.md
evaluar.py
preguntas.csv
pyproject.toml
server.py
test_server.py
uv.lock
== Sesion 16 ==
README.md
referencias
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio\necho \"== S16 referencias ==\"; gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/referencias --jq '.[] | \"\\(.name) \\(.size)\"' 2>&1\necho \"== S04 server.py (TODOs) ==\"; gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/04-mcp-claude-code/proyecto/server.py --jq '.content' | base64 -d | grep -nE \"def |TODO|@mcp\" | head -40\necho \"== S04 tests ==\"; gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/04-mcp-claude-code/proyecto/test_server.py --jq '.content' | base64 -d | grep -nE \"^def test|^async def test\" \necho \"== S16 README headings ==\"; gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/README.md --jq '.content' | base64 -d | grep -nE \"^#\" | head -40",
 "description": "Inspect course session 04 and 16 reference files",
 "timeout": 120000
}
```

<details><summary>resultado</summary>

```text
== S16 referencias ==
mapa_pobreza_2024.png 154081
pobreza_departamento_2024.csv 459
== S04 server.py (TODOs) ==
1:"""Servidor MCP del BCRP. Empiecen aquí: buscar_series ya funciona; completen los TODO hasta que pasen las pruebas.
31:def _sin_tildes(s):
36:def catalogo():
51:def _ficha(codigo):
60:@mcp.tool(annotations=SOLO_LECTURA)
61:def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
81:# TODO 1 · serie(codigo, desde, hasta) -> {"codigo", "nombre", "frecuencia", "datos": [{"periodo", "valor"}], "fuente"}
92:# TODO 2 · resumen(codigo, desde, hasta): primero, ultimo, cambio, variacion_pct, promedio, maximo y minimo
95:# TODO 3 · Una herramienta suya, bien descrita. Ideas:
101:# TODO 4 · Un recurso, por ejemplo la plantilla bcrp://serie/{codigo} con la ficha de la serie.
103:# TODO 5 · Un prompt, por ejemplo informe(tema) que pida citar el código y el periodo de cada cifra.
== S04 tests ==
25:def test_buscar_encuentra_el_ipc():
31:def test_cuatro_herramientas_como_minimo():
37:def test_serie_mensual():
45:def test_serie_diaria():
51:def test_resumen_sin_cuentas_a_mano():
59:def test_codigo_inexistente_da_un_error_claro():
64:def test_un_recurso():
70:def test_un_prompt():
== S16 README headings ==
1:# Sesión 16 · Skills de Claude Code: limpiar, graficar y mapear la ENAHO
15:## Contenido
22:## Lo esencial de una skill
38:### Por qué crearla en Claude Code
48:## Los datos
59:## El proyecto
72:### 1. Preparar (0–8 min)
82:### 2. Limpiar 
… [recortado: 203 caracteres más]
```
</details>

**🔧 mcp__ccd_turn__update_plan**

```json
{
 "advance": true
}
```

<details><summary>resultado</summary>

```text
Plan updated: step 3 of 3 is in progress.
```
</details>

**🔧 mcp__ccd_turn__wrap_up**

```json
{
 "recap": "Revisé el repo y las fuentes. Todo es accesible: los ZIP de ENAHO del INEI, la API del BCRP, el GeoJSON y el material de las sesiones 04 y 16. La tarea 4 se puede hacer, pero según la fecha de mi entorno el plazo venció ayer, 8 de noviembre. Todavía no creé ningún archivo.",
 "ask": "¿Empezamos la tarea 4 aunque ya pasó el plazo?",
 "actions": [
  {
   "label": "Sí, empecemos"
  },
  {
   "label": "Primero consulto"
  }
 ],
 "blocked": true
}
```

<details><summary>resultado</summary>

```text
Shown in the next-step box. Your closing message is your answer to the user: write it now, in full, as the last thing you say this turn. The box asks your question, so do not ask it again.
```
</details>

### 🤖 Claude · 2026-11-09 11:37

Sí, se puede hacer. Pero antes de empezar tienes que saber algo importante: **según la fecha de mi entorno, hoy es lunes 9 de noviembre de 2026, y el plazo venció ayer domingo 8 a las 11:59 p. m. (hora de Perú).** Si entregas hoy, cuenta como un día de retraso (−2 puntos), y solo la aceptan si el equipo docente aprueba una justificación. Si mi fecha estuviera mal o tienes una prórroga, esto no aplica. Si no, conviene escribirle al docente cuanto antes.

**Qué comprobé:**
- **Datos INEI:** las descargas de ENAHO 2024 funcionan. El módulo 34 pesa unos 16 MB y el módulo 02 unos 6 MB.
- **API del BCRP:** responde bien. Probé la inflación de Lima en 2024 y devolvió datos reales.
- **GeoJSON departamental:** está accesible.
- **Sesión 04:** tiene el `server.py` con 5 TODO por completar y las 8 pruebas originales. Solo `buscar_series` viene hecho.
- **Sesión 16:** trae el README con las reglas de limpieza y el CSV y el mapa de referencia, que sirven para la comparación que pide el mapa.
- **Herramientas instaladas:** `uv` 0.12, Claude Code y `gh`. No hay Python del sistema, pero `uv` lo instala solo.

**Cómo lo haría** (todo en `tarea_4/`, con commits por etapa):
- **Parte 1:** completar el servidor MCP con `serie`, `resumen`, una herramienta propia (`comparar_periodos` o `correlacion`), un recurso y un prompt. Luego el `.mcp.json` y la meta de 10 pruebas aprobadas.
- **Parte 2:** las tres Skills con scripts que se ejecuten de verdad. La limpieza tiene que dar 27.6 % de pobreza nacional, 108,664 residentes y 25 departamentos, y detenerse con error si alguna validación falla.
- **Parte 3:** una pregunta de investigación que cruce las dos fuentes. Una ejecución de Claude Code en modo no interactivo (`claude -p`), que guarda un registro, usaría el MCP y las Skills juntos. Eso produce el informe final y la verificación de 3 cifras.
- **Parte 4:** 10 preguntas con respuestas calculadas de forma independiente. Cada una se corre en sesiones separadas, sin y con MCP/Skills, midiendo el tiempo. Así salen `resultados.csv` y `comparacion.md`.
- **Evidencias y README:** exportaría esta conversación y las ejecuciones a `evidencias_ia/`, ocultando los datos sensibles.

**Lo que te va a tocar a ti:**
- Darme tu nombre completo para el comentario de entrega.
- Publicar ese comentario en el Issue. Te lo dejo redactado.
- Aceptar que la evaluación lanza unas 20 o más sesiones de Claude Code en modo no interactivo, y eso consume tu cuota de uso.

Es un trabajo de varias horas de ejecución. Lo que más cuesta es la evaluación A/B, más que el código.

---

### 🧑 Usuario · 2026-11-09 11:37

olvidate de la fecha de entrega.

**🔧 mcp__ccd_turn__update_plan**

```json
{
 "items": [
  {
   "content": "Bajar material de sesiones 04/16 y microdatos",
   "status": "in_progress"
  },
  {
   "content": "Servidor MCP del BCRP con 10 pruebas",
   "status": "pending"
  },
  {
   "content": "Skill limpiando-enaho con validaciones",
   "status": "pending"
  },
  {
   "content": "Skills graficando-enaho y mapeando-enaho",
   "status": "pending"
  },
  {
   "content": "Ejecución integrada e informe final",
   "status": "pending"
  },
  {
   "content": "Evaluación A/B de 10 preguntas",
   "status": "pending"
  },
  {
   "content": "README, evidencias IA y commits",
   "status": "pending"
  }
 ],
 "scope": "continuation"
}
```

<details><summary>resultado</summary>

```text
Plan shown (7 steps).
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio\nSP=\"/c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad\"\nmkdir -p \"$SP/ref04\" \"$SP/ref16\"\nR=repos/d2cml-ai/Data-Science-Python/contents/sessions\nfor f in .gitignore README.md evaluar.py preguntas.csv pyproject.toml server.py test_server.py; do gh api \"$R/04-mcp-claude-code/proyecto/$f\" --jq '.content' | base64 -d > \"$SP/ref04/$f\"; done\ngh api \"$R/04-mcp-claude-code\" --jq '.[] | \"\\(.type) \\(.name)\"'\ngh api \"$R/04-mcp-claude-code/README.md\" --jq '.content' | base64 -d > \"$SP/ref04/README_sesion.md\"\ngh api \"$R/16-skills-enaho/README.md\" --jq '.content' | base64 -d > \"$SP/ref16/README.md\"\ngh api \"$R/16-skills-enaho/referencias/pobreza_departamento_2024.csv\" --jq '.content' | base64 -d > \"$SP/ref16/pobreza_departamento_2024.csv\"\nwc -l \"$SP\"/ref04/* \"$SP\"/ref16/*\necho \"== root .claude ==\"; ls -la .claude; cat .gitignore\necho \"== tarea_2 evidencias ==\"; ls -la tarea_2/evidencias_ia | head",
 "description": "Download course session reference files to scratchpad",
 "timeout": 120000
}
```

<details><summary>resultado</summary>

```text
file .gitignore
file README.md
file mcps_mas_usados.md
dir proyecto
  146 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/README.md
   37 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/README_sesion.md
   75 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/evaluar.py
    9 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/preguntas.csv
    9 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/pyproject.toml
  107 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/server.py
   71 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/test_server.py
  217 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref16/README.md
   26 /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref16/pobreza_departamento_2024.csv
  697 total
== root .claude ==
total 5
drwxr-xr-x 1 <usuario> 197121   0 Nov  1 22:31 .
drwxr-xr-x 1 <usuario> 197121   0 Nov  1 22:32 ..
-rw-r--r-- 1 <usuario> 197121 248 Nov  1 22:31 launch.json
# Entornos y caches
.venv/
__pycache__/
.ipynb_checkp
… [recortado: 246 caracteres más]
```
</details>

**🔧 Bash**

```json
{
 "command": "SP=\"/c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad\"\nfor f in server.py test_server.py pyproject.toml preguntas.csv evaluar.py README.md; do echo \"=================== $f\"; cat \"$SP/ref04/$f\"; done",
 "description": "Show session 04 project reference files"
}
```

<details><summary>resultado</summary>

```text
=================== server.py
"""Servidor MCP del BCRP. Empiecen aquí: buscar_series ya funciona; completen los TODO hasta que pasen las pruebas.

    uv run pytest                                           # el contrato: las 8 pruebas deben pasar
    uv run server.py                                        # el servidor, por stdio
    claude mcp add --scope project bcrp -- uv run server.py # conectarlo a Claude Code

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""
import re
import unicodedata
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
CATALOGO = AQUI / "datos" / "catalogo_bcrp.csv"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, y serie para los datos. No calcules a mano: "
    "cita siempre el código de la serie y el periodo."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 
… [recortado: 19,258 caracteres más]
```
</details>

**🔧 Bash**

```json
{
 "command": "SP=\"/c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad\"\ncat \"$SP/ref16/README.md\"; echo \"==========\"; cat \"$SP/ref16/pobreza_departamento_2024.csv\"; echo \"======\"; cat \"$SP/ref04/.gitignore\"",
 "description": "Show session 16 README and reference CSV"
}
```

<details><summary>resultado</summary>

```text
# Sesión 16 · Skills de Claude Code: limpiar, graficar y mapear la ENAHO

Qué es una skill de Claude Code, por qué conviene crearla dentro del repositorio y cómo se arma una que limpie la ENAHO
siempre de la misma forma. El proyecto son tres skills que trabajan juntas: una limpia los módulos del INEI, otra
hace gráficos y otra hace un mapa por departamento.

**Slides de la clase:** https://claude.ai/artifact/X7H6PUvaWKde1epsYCJNze

| Bloque | Duración | Qué se hace |
|---|---|---|
| Clase | 30 min | Qué es una skill, cómo se carga y se activa, por qué en Claude Code, el pipeline de la ENAHO y sus trampas |
| Proyecto | 45 min | Tres skills: `limpiando-enaho`, `graficando-enaho` y `mapeando-enaho`, validadas y probadas con y sin ellas |
| Presentaciones | 15 min | Cuatro repositorios al azar, tres minutos cada uno |

## Contenido

| Archivo | Qué hay |
|---|---|
| [`referencias/pobreza_departamento_2024.csv`](referencias/pobreza_departamento_2024.csv) | La pobreza 2024 de los 25 departamentos, para validar el mapa |
| [`referencias/mapa_pobreza_2024.png`](referencias/mapa_pobreza_2024.png) | Cómo debe verse el mapa |

## Lo esencial de una skill

- **Es una carpeta** con un `SKILL.md` obligatorio y, si hace falta, archivos de referencia y scripts. En un proyecto
  va en `.claude/skills/<nombre>/`. Así viaja con git y todo el equipo usa la misma.
- **`SKILL.md`** empieza con un bloque YAML con `name` (minúsculas, números y guiones; hasta 64 caracteres) y
  `description`. Debajo
… [recortado: 10,517 caracteres más]
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio\nmkdir -p tarea_4/{mcp,datos/inei,datos/geo,salidas,figuras,mapas,evaluacion,informes,evidencias_ia/{mcp,skills,integracion,evaluacion}} tarea_4/.claude/skills/{limpiando-enaho/scripts,graficando-enaho/scripts,mapeando-enaho/scripts}\ncd tarea_4/datos/inei\ncurl -sL --max-time 300 -o 966-Modulo34.zip \"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip\" &\ncurl -sL --max-time 300 -o 966-Modulo02.zip \"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip\" &\ncurl -sL --max-time 120 -o ../geo/peru_departamental_simple.geojson \"https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson\" &\nwait\nls -la . ../geo\nunzip -l 966-Modulo34.zip; unzip -l 966-Modulo02.zip",
 "description": "Create tarea_4 folders and download ENAHO zips and GeoJSON",
 "timeout": 360000
}
```

<details><summary>resultado</summary>

```text
.:
total 21224
drwxr-xr-x 1 <usuario> 197121        0 Nov  9 11:39 .
drwxr-xr-x 1 <usuario> 197121        0 Nov  9 11:39 ..
-rw-r--r-- 1 <usuario> 197121  5793097 Nov  9 11:39 966-Modulo02.zip
-rw-r--r-- 1 <usuario> 197121 15935617 Nov  9 11:39 966-Modulo34.zip

../geo:
total 140
drwxr-xr-x 1 <usuario> 197121      0 Nov  9 11:39 .
drwxr-xr-x 1 <usuario> 197121      0 Nov  9 11:39 ..
-rw-r--r-- 1 <usuario> 197121 139681 Nov  9 11:39 peru_departamental_simple.geojson
Archive:  966-Modulo34.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2026-05-14 09:56   966-Modulo34/
    24486  2025-05-07 19:18   966-Modulo34/ConstVarGasto-Metodologia actualizada.zip
   254671  2025-05-05 19:34   966-Modulo34/DefinicionValoresMonetariosBasedeDatos.pdf
  3940690  2025-05-16 14:36   966-Modulo34/Diccionario2024.pdf
   207192  2025-05-05 16:51   966-Modulo34/Estratificacion del Marco.pdf
   487444  2024-02-06 18:57   966-Modulo34/FichaTecnica.pdf
 29991565  2026-05-12 14:22   966-Modulo34/sumaria-2024-12g.dta
  2727028  2025-05-05 16:48   966-Modulo34/Sumaria-2024-12g.pdf
 21219121  2025-05-08 09:27   966-Modulo34/sumaria-2024.dta
  2142849  2025-05-05 16:48   966-Modulo34/Sumaria-2024.pdf
---------                     -------
 60995046                     10 files
Archive:  966-Modulo02.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2025-05-07 14:43   966-Modulo02/
   201079  2024-06-18 10:39   966-Modulo02/CED-01-200-2024.pdf
   395343  2021-05-07
… [recortado: 471 caracteres más]
```
</details>

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\pyproject.toml",
 "content": "[project]\nname = \"agente-socioeconomico-peru\"\nversion = \"0.1.0\"\ndescription = \"Agente de investigación socioeconómica: MCP del BCRP + Skills de la ENAHO 2024 (Tarea 4, Python Intermedio)\"\nrequires-python = \">=3.11\"\ndependencies = [\n    \"fastmcp>=4,<5\",\n    \"httpx\",\n    \"pandas\",\n    \"pyarrow\",\n    \"geopandas\",\n    \"matplotlib\",\n]\n\n[dependency-groups]\ndev = [\"pytest\"]\n\n[tool.pytest.ini_options]\ntestpaths = [\"mcp\"]\n"
}
```

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.gitignore",
 "content": "# Entorno\n.venv/\n__pycache__/\n.pytest_cache/\n\n# Microdatos originales y bases intermedias (se descargan y regeneran con los scripts)\ndatos/\nsalidas/*.parquet\n\n# Config local de Claude Code (permisos de la máquina)\n.claude/settings.local.json\n\n# Corridas temporales de la evaluación\nevaluacion/_tmp/\n"
}
```

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && echo \"3.12\" > .python-version && uv sync 2>&1 | tail -15 && uv run python -c \"import fastmcp, geopandas, pandas, pyarrow, matplotlib; print(fastmcp.__version__, geopandas.__version__, pandas.__version__)\"",
 "description": "Create uv environment and install dependencies",
 "timeout": 600000
}
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\pyproject.toml (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.gitignore (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
+ referencing==0.37.0
 + rich==15.0.0
 + rich-rst==2.2.0
 + rpds-py==2026.9.1
 + shapely==2.2.0
 + sse-starlette==3.7.0
 + starlette==1.10.0
 + truststore==0.10.5
 + typing-extensions==4.16.0
 + typing-inspection==0.4.5
 + tzdata==2026.6
 + uncalled-for==0.6.0
 + uvicorn==0.54.0
 + watchfiles==1.3.0
 + websockets==17.4
4.1.6 1.2.0 3.1.1
```
</details>

### 🤖 Claude · 2026-11-09 11:40

Avance: ya tengo los datos de ENAHO (dos ZIP), el GeoJSON y el entorno `uv` instalado. Ahora estoy armando el servidor MCP del BCRP.

**🔧 mcp__ccd_turn__update_plan**

```json
{
 "advance": true
}
```

<details><summary>resultado</summary>

```text
Plan updated: step 2 of 7 is in progress. App actions available now: commit, create_pr, verify.
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4\ncp \"/c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/test_server.py\" mcp/test_server.py\nF=$(uv run python -c \"import fastmcp,os;print(os.path.dirname(fastmcp.__file__))\")\ngrep -n \"def resource\\|def prompt\\|def tool\" \"$F/server/server.py\" | head; ls \"$F\"",
 "description": "Copy original tests and inspect FastMCP 4 decorators"
}
```

<details><summary>resultado</summary>

```text
1839:    def tool(
1860:    def tool(
1880:    def tool(
2001:    def resource(
2132:    def prompt(
2147:    def prompt(
2161:    def prompt(
__init__.py
_compat.py
_install_hints.py
_warnings.py
apps
cli
client
contrib
decorators.py
dependencies.py
exceptions.py
experimental
mcp_config.py
prompts
py.typed
resources
server
settings.py
skills
telemetry.py
tools
types.py
utilities
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4\nF=$(uv run python -c \"import fastmcp,os;print(os.path.dirname(fastmcp.__file__))\")\nsed -n 2001,2060p \"$F/server/server.py\"; sed -n 2132,2200p \"$F/server/server.py\"",
 "description": "Read FastMCP resource and prompt decorator signatures"
}
```

<details><summary>resultado</summary>

```text
def resource(
        self,
        uri: str,
        *,
        name: str | None = None,
        version: str | int | None = None,
        title: str | None = None,
        description: str | None = None,
        icons: list[mcp_types.Icon] | None = None,
        mime_type: str | None = None,
        tags: set[str] | None = None,
        annotations: Annotations | dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
        app: AppConfig | dict[str, Any] | bool | None = None,
        auth: AuthCheck | list[AuthCheck] | None = None,
        security: ResourceSecurity | None | InheritSecurity = INHERIT_SECURITY,
    ) -> Callable[[F], F]:
        """Decorator to register a function as a resource.

        The function will be called when the resource is read to generate its content.
        The function can return:
        - str for text content
        - bytes for binary content
        - other types will be converted to JSON

        Resources can optionally request a Context object by adding a parameter with the
        Context type annotation. The context provides access to MCP capabilities like
        logging, progress reporting, and session information.

        If the URI contains parameters (e.g. "resource://{param}") or the function
        has parameters, it will be registered as a template resource.

        Args:
            uri: URI for the resource (e.g. "resource://my-resource" or "resource://{param}")
            name: Optional name for t
… [recortado: 3,677 caracteres más]
```
</details>
