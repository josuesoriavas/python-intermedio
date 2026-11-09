---
name: mapeando-enaho
description: Construye el mapa coroplético de la pobreza monetaria por departamento del Perú con la ENAHO 2024 del INEI (25 departamentos, Lima y Callao separados), uniendo por código ubigeo y no por nombre, y lo compara con la referencia del curso. Úsala cuando pidan un mapa, mapear o ver la distribución territorial o geográfica de la pobreza por departamento o región.
argument-hint: "[--metodo personas|inei_hogares] [--indicador pobre|pobre_extremo]"
allowed-tools: Bash(uv run:*), Read, Glob
---

# Mapeando la ENAHO 2024

## Antes de mapear (obligatorio)

1. Comprueba con Glob si existe `salidas/personas_2024.parquet`.
2. **Si no existe, invoca primero la skill `limpiando-enaho`** (herramienta Skill) y sigue sus pasos hasta que
   `salidas/validacion.txt` diga `BASE VÁLIDA`. Si la limpieza falla, detente e informa: no hay mapa sin base válida.
3. Recién entonces corre el mapa. (Como red de seguridad, `mapear.py` también se niega a dibujar sin base válida.)

## Correr

Desde la raíz del proyecto:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/mapear.py                          # residentes habituales (facpob07)
uv run python ${CLAUDE_SKILL_DIR}/scripts/mapear.py --metodo inei_hogares    # cifras oficiales del INEI
uv run python ${CLAUDE_SKILL_DIR}/scripts/mapear.py --indicador pobre_extremo
```

Baja el GeoJSON del curso a `datos/geo/` si falta.

## Reglas que el script garantiza (no las rehagas a mano)

- Une `ubigeo[:2]` con `FIRST_IDDP` como texto de dos dígitos, `validate="1:1"`. Nunca por nombre: «APURIMAC» no es
  «Apurímac».
- Exige 25 unidades con dato y Lima (15) y Callao (07) separados; si no, termina con error y no dibuja nada.
- Escala secuencial de un solo tono (azul claro a oscuro) en clases de 10 puntos desde 0; leyenda con la unidad
  («% de personas en pobreza monetaria») y el número de departamentos por clase. Nunca arcoíris.
- Compara con `referencias/pobreza_departamento_2024.csv` (Sesión 16) y escribe `mapas/comparacion_referencia.csv`
  y `.txt`.

## Qué produce

`mapas/pobreza_departamento_2024.png`, la tabla graficada `mapas/pobreza_departamento_2024.csv` (valor, IC 95 %, n) y
la comparación con la referencia.

## Al responder

Cita la ruta del mapa, los departamentos con mayor y menor pobreza (un decimal, % de personas) y el resultado de la
comparación con la referencia: con `inei_hogares` coincide 25/25; con residentes habituales difiere hasta 0.5 pp
por la definición de población (ver `salidas/validacion.txt`). Describe patrones territoriales, no causas.
