---
name: limpiando-enaho
description: Limpia, une y valida los microdatos de la ENAHO 2024 del INEI (módulo 34 sumaria y módulo 02 miembros) y calcula pobreza monetaria ponderada con factores de expansión. Úsala cuando pidan limpiar, preparar o validar la ENAHO, o cuando una pregunta necesite cifras de pobreza, pobreza extrema o gasto de los hogares peruanos (nacional, urbana o rural, por departamento, región, sexo, edad o jefatura del hogar). También es el paso previo de graficando-enaho y mapeando-enaho si no existe salidas/personas_2024.parquet.
argument-hint: "[anio=2024]"
allowed-tools: Bash(uv run:*), Read, Glob
---

# Limpiando la ENAHO 2024

Convierte los zip del INEI en una base de personas validada y responde cifras ponderadas. Lo que no se discute
(llaves, filtro, unión, pesos, validación) está en `scripts/limpiar.py`; no lo reescribas ni lo reemplaces con código
propio.

## Pasos

1. **¿Ya hay base válida?** Si existen `salidas/personas_2024.parquet` y `salidas/validacion.txt` dice
   `Resultado: BASE VÁLIDA`, salta al paso 4 (salvo que pidan rehacer la limpieza).
2. **Limpiar.** Desde la raíz del proyecto corre exactamente:

   ```bash
   uv run python ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio 2024
   ```

   Descarga `966-Modulo34.zip` y `966-Modulo02.zip` a `datos/inei/` si faltan (966 = ENAHO 2024 en el portal del INEI).
3. **Leer la validación.** Abre `salidas/validacion.txt`. Si el script termina con error o dice `BASE RECHAZADA`,
   **detente**: informa qué validación falló y no reportes cifras. Nunca ajustes datos ni pesos para que coincidan con
   las referencias.
4. **Responder con cifras ponderadas.** Para cualquier corte usa el script de consulta (nunca un promedio simple):

   ```bash
   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --por area
   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --por departamento --orden desc
   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --por sexo --filtro "area == 'Rural'"
   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --indicador pobre_extremo
   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --media gasto_pc_mensual --por region_natural
   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --media participacion_alimentos --por condicion_pobreza
   ```

   Las tablas ya calculadas están en `salidas/indicadores.csv` (columna `metodo`).
5. **Citar.** Cada cifra va con un decimal, su unidad (% de personas), el IC 95 % si importa la comparación, el método
   y la fuente: «INEI, ENAHO 2024, módulos 34 y 02; residentes habituales ponderados con facpob07».

## Qué método usar

| Pregunta | Método | Cómo |
|---|---|---|
| Características de las personas (sexo, edad) o cualquier análisis propio | `personas` (por defecto) | residentes habituales, `facpob07` |
| Comparar con la cifra oficial publicada por el INEI (nacional, área, dominio, departamento) | `inei_hogares` | sumaria, `factor07 × mieperho`; `--metodo inei_hogares` |

Las dos dan 27.6 % nacional (27.53 % y 27.58 %). En departamentos difieren hasta 0.5 puntos porque cuentan poblaciones
distintas; está explicado en `salidas/validacion.txt` y en [reference.md](reference.md).

## Reglas

- Diferencias entre grupos: compara los IC 95 %. Si se superponen, di que la diferencia no es concluyente.
- Son asociaciones descriptivas de un corte transversal: no afirmes causas.
- Antes de usar una variable que no está en la base, o para entender códigos y filtros, lee [reference.md](reference.md).
