---
name: graficando-enaho
description: Hace gráficos de barras de la pobreza monetaria del Perú con la ENAHO 2024 del INEI, siempre ponderados con factores de expansión y con intervalos de confianza, título analítico, unidades y fuente. Úsala cuando pidan graficar, visualizar o comparar en un gráfico la pobreza (o pobreza extrema) por área urbana y rural, sexo, edad, jefatura del hogar, región natural, dominio o departamento.
argument-hint: "[por: area|sexo|grupo_edad|sexo_jefe|region_natural|nombre_dominio|departamento]"
allowed-tools: Bash(uv run:*), Read, Glob
---

# Graficando la ENAHO 2024

## Antes de graficar

Si no existe `salidas/personas_2024.parquet`, usa primero la skill **limpiando-enaho** (o deja que el script la
ejecute: si no encuentra la base corre `limpiar.py` y se detiene si la validación falla). Nunca grafiques con una base
que no pasó `salidas/validacion.txt`.

## Traducir el pedido a argumentos

| Pedido en lenguaje natural | Comando |
|---|---|
| «pobreza urbana y rural», «por área» | `--por area` |
| «por sexo», «hombres y mujeres» | `--por sexo` |
| «por departamento», «regiones», «comparar departamentos» | `--por departamento` |
| «por edad», «niños y adultos mayores» | `--por grupo_edad` |
| «según el sexo del jefe de hogar» | `--por sexo_jefe` |
| «costa, sierra y selva» | `--por region_natural` |
| «por edad y área», «sexo dentro de cada área» | `--por grupo_edad --dividir area` |
| «solo en zonas rurales» | `--filtro "area == 'Rural'"` |
| «pobreza extrema» | `--indicador pobre_extremo` |
| «los gráficos básicos» | `--todos` (área, sexo, departamento, edad × área) |

Corre desde la raíz del proyecto:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por area
```

Si el usuario da un título, pásalo con `--titulo "..."`; si no, el script escribe uno con el hallazgo principal
calculado con los mismos números (y dice «sin diferencia concluyente» cuando los IC 95 % se superponen).

## Qué produce

- `figuras/<nombre>.png` a 200 dpi y `figuras/<nombre>.csv` con la tabla exacta graficada (valor, IC 95 %, n).
- Barras horizontales desde cero, un solo color (dos si hay `--dividir`), valor escrito en cada barra, IC 95 % en gris,
  línea punteada con el promedio nacional, subtítulo con indicador, período y unidad (% de personas), y nota de fuente:
  «INEI, ENAHO 2024 (módulos 34 y 02)».

## Al responder

Muestra la ruta del PNG, resume en 2–3 frases lo que se ve con las cifras de la tabla impresa (un decimal, % de
personas) y aclara si las diferencias son concluyentes según los IC. Describe asociaciones, no causas.
