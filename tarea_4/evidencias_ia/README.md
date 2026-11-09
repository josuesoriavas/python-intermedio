# Evidencias del uso de IA

Hay dos tipos de evidencia: la conversación de desarrollo con Claude Code y las trazas de las ejecuciones del agente. Todas las sesiones se hicieron con Claude Code el 9/11/2026.

## 1. Conversación de desarrollo (Claude Code, escritorio)

Es la sesión interactiva en la que se construyó el proyecto. Incluye:

- los mensajes del usuario;
- las respuestas del asistente;
- cada llamada a herramienta, con sus argumentos;
- un extracto de cada resultado.

La exportó [`scripts/exportar_conversacion.py`](../scripts/exportar_conversacion.py) desde el registro `.jsonl` de la sesión.

| Archivo | Fase |
|---|---|
| [`conversacion_completa.md`](conversacion_completa.md) | Conversación entera, de principio a fin |
| [`conversacion_0_planificacion.md`](conversacion_0_planificacion.md) | Lectura del enunciado, revisión del material del curso y plan |
| [`mcp/conversacion_mcp.md`](mcp/conversacion_mcp.md) | Servidor MCP del BCRP y sus pruebas |
| [`skills/conversacion_skills.md`](skills/conversacion_skills.md) | Skills `limpiando-enaho`, `graficando-enaho` y `mapeando-enaho`, y validación |
| [`integracion/conversacion_integracion.md`](integracion/conversacion_integracion.md) | Pregunta de investigación y ejecución integrada |
| [`evaluacion/conversacion_evaluacion.md`](evaluacion/conversacion_evaluacion.md) | Evaluación A/B, verificación, correcciones y documentación |

Notas:

- La sesión se compactó una vez por longitud. El resumen automático aparece como un mensaje del usuario que empieza con «This session is being continued…»; lo genera Claude Code, no lo escribió el usuario.
- No se incluye el razonamiento interno del modelo ni los recordatorios automáticos del sistema.
- Las entradas de herramientas se recortan a 2,500 caracteres y los resultados a 1,500. El contenido completo está en los archivos del repositorio.

## 2. Trazas de ejecuciones del agente (`claude -p`)

Son ejecuciones no interactivas de Claude Code lanzadas con [`scripts/ejecutar_agente.py`](../scripts/ejecutar_agente.py) o [`evaluacion/evaluar.py`](../evaluacion/evaluar.py). Cada una tiene dos archivos:

- `.jsonl`: la salida `stream-json` completa. Contiene el evento `init` (servidores MCP conectados y skills disponibles), cada mensaje, cada llamada a herramienta con su resultado y el evento final con duración y costo.
- `.md`: un resumen legible, con las herramientas MCP y las skills usadas, la tabla de llamadas en orden, los errores y la respuesta final.

| Carpeta / archivo | Qué demuestra |
|---|---|
| [`skills/01_invocacion_directa_limpiando`](skills/01_invocacion_directa_limpiando.md) | Invocación directa con `/limpiando-enaho 2024`: sin base procesada, la skill corre `limpiar.py` y valida 15 de 15 |
| [`skills/02_lenguaje_natural_graficando`](skills/02_lenguaje_natural_graficando.md) | Activación por lenguaje natural, sin nombrar la skill: «Grafica la pobreza monetaria por sexo del jefe de hogar en el Perú con la ENAHO 2024…» |
| [`skills/03_coordinacion_limpieza_y_mapa`](skills/03_coordinacion_limpieza_y_mapa.md) | Coordinación: sin base procesada, `mapeando-enaho` invoca primero `limpiando-enaho` y después mapea |
| [`integracion/02_ejecucion_integrada`](integracion/02_ejecucion_integrada.md) | **Ejecución integrada final**: 5 herramientas MCP distintas, un recurso MCP y las 3 skills; produjo `informes/informe_final.md` |
| [`integracion/01_ejecucion_integrada_v1`](integracion/01_ejecucion_integrada_v1.md) | Primer intento: leyó dos `SKILL.md` con `cat` en vez de activarlos. Por eso se ajustó la instrucción |
| [`integracion/03_manejo_errores`](integracion/03_manejo_errores.md) | Datos inexistentes (IPC de dic-2026 y ENAHO 2025): el agente lo informa y no inventa cifras |
| [`evaluacion/trazas/`](evaluacion/trazas/) | Las 20 sesiones de la evaluación A/B (`A_<id>` sin herramientas, `B_<id>` con MCP y skills) |
| `*_consola.txt` | Lo que imprimió cada ejecución en la terminal |

## Privacidad

[`scripts/ocultar_evidencias.py`](../scripts/ocultar_evidencias.py) y el exportador aplican los mismos patrones a todos los archivos de texto de esta carpeta. Ocultan:

- correos;
- claves con forma `sk-…`;
- tokens de GitHub;
- pares `clave=valor` de contraseñas o tokens;
- el nombre de usuario dentro de las rutas de la computadora (aparece como `C:\Users\<usuario>`).

En las sesiones no se usó ninguna clave de API: todos los eventos `init` registran `"apiKeySource":"none"`. Las consultas al BCRP y al INEI usan endpoints públicos sin credenciales.
