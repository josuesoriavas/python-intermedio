# Actividad, inflación y brechas de pobreza en el Perú, 2019–2024

## 1. Pregunta de investigación

**Tema.** Evolución de la actividad económica y de la inflación (general y de alimentos) tras la recesión de 2020 y el pico inflacionario de 2022, y brechas territoriales y socioeconómicas de pobreza monetaria y del peso de los alimentos en el gasto de los hogares en 2024.

**Objetivo.** Describir (no explicar causalmente) la trayectoria macroeconómica 2019–2024 y la estructura de pobreza y gasto en alimentos observada en 2024.

**Delimitación.**

| Eje | Definición |
|---|---|
| Período macro | 2019–2024 (PBI anual; IPC mensual, ene-2019 a dic-2024) |
| Período micro | Un solo corte transversal: ENAHO 2024 |
| Cobertura geográfica | PBI: Perú. IPC: **Lima Metropolitana**. ENAHO: nacional, urbano/rural, regiones naturales y 25 departamentos (Lima y Callao separados) |
| Unidades | PBI: variación % real anual. IPC: variación % a 12 meses. Pobreza: % de personas. Alimentos: % del gasto del hogar (promedio ponderado por personas) |

## 2. Plan de análisis

1. **BCRP** (servidor MCP `bcrp`): PBI real (`PM04923AA`), inflación general (`PN01273PM`) e inflación de alimentos y bebidas (`PN09822PM`), obtenidos con `resumen`, `serie` y `comparar_periodos`; un gráfico con `graficar_serie`.
2. **ENAHO 2024** (skills): validar la base (`limpiando-enaho`); pobreza por área y departamento; participación de los alimentos en el gasto según condición de pobreza y área.
3. **Gráficos**: pobreza por área y participación de alimentos por condición de pobreza × área (`graficando-enaho`).
4. **Mapa**: pobreza monetaria por departamento (`mapeando-enaho`).
5. **Contraste** con `salidas/validacion.txt` y `mapas/comparacion_referencia.txt`.

## 3. Fuentes y metodología

- **BCRP**, API de estadísticas (`estadisticas.bcrp.gob.pe`), consultada con el servidor MCP del proyecto. No se calculó nada a mano; las variaciones y promedios los devuelven `resumen` y `comparar_periodos`.
- **INEI, ENAHO 2024** (código 966): módulo 34 (sumaria) y módulo 02 (miembros del hogar).
- **Procesamiento** (`.claude/skills/limpiando-enaho/scripts/limpiar.py`): llaves como texto, residentes habituales (108,664 personas), unión m:1 personas–hogares, 25 códigos departamentales. La validación aprobó 15 de 15 controles: **BASE VÁLIDA** (`salidas/validacion.txt`).
- **Ponderación**: todas las cifras de la ENAHO usan factores de expansión. Método `personas`: residentes habituales con `facpob07`. Método `inei_hogares`: sumaria con `factor07 × mieperho`, usado para contrastar con cifras oficiales y para el mapa. Los IC 95 % son del script de estimación (`estimacion.py`).
- **Indicadores**: pobreza monetaria (% de personas); participación de alimentos = gasto en alimentos / gasto total del hogar (`participacion_alimentos`), promediada con `facpob07` según condición de pobreza (no pobre, pobre no extremo, pobre extremo).

## 4. Resultados

### Hallazgos

1. **La actividad cayó en 2020 y rebotó en 2021; 2023 fue un año débil.** PBI real, `PM04923AA`: 2019 = 2.2 %; 2020 = −10.9 %; 2021 = +13.4 %; 2022 = +2.8 %; 2023 = −0.4 %; 2024 = +3.5 % (herramienta `serie`, 2019–2024). El máximo del período es 2021 y el mínimo 2020 (`resumen`).
2. **La inflación de alimentos fue mayor y más persistente que la general.** IPC Lima Metropolitana, var. % a 12 meses:
   - General (`PN01273PM`): promedio 2019 = 2.1 %; promedio 2022 = 7.9 %; máximo 8.8 % en 2022-06; promedio 2024 = 2.4 %; dic-2024 = 2.0 % (`comparar_periodos`, `resumen`).
   - Alimentos y bebidas (`PN09822PM`): promedio 2019 = 1.7 %; promedio 2022 = 10.8 %; **máximo 13.2 % en 2023-02**; promedio 2024 = 2.0 %; mínimo 0.7 % en 2024-09; dic-2024 = 1.2 %.
   - Entre 2022 y 2024 el promedio de la inflación de alimentos bajó 81.3 % (de 10.8 % a 2.0 %) y el de la general 70.1 % (de 7.9 % a 2.4 %).
3. **La pobreza 2024 es más alta en el área rural.** ENAHO 2024, `salidas/indicadores.csv` / `consultar.py --por area` / `figuras/pobreza_area.csv`: nacional 27.5 % (IC 95 %: 26.5–28.5); rural 39.4 % (37.8–41.1); urbana 24.7 % (23.5–25.9). Los IC no se superponen: la brecha de 14.7 pp es concluyente. Pobreza extrema: nacional 5.5 %; rural 15.6 %; urbana 3.1 % (`indicadores.csv`).
4. **Fuerte brecha departamental.** `consultar.py --por departamento --orden desc` y `mapas/pobreza_departamento_2024_inei.csv` (método INEI):
   - Mayor pobreza: Cajamarca 45.0 % (IC 40.5–49.5), Loreto 43.0 % (38.4–47.5), Puno 39.9 %, Pasco 39.0 %, Huánuco 39.0 %.
   - Menor: Ica 6.0 % (4.2–7.8), Moquegua 11.0 %, Madre de Dios 11.1 %, Lambayeque 14.0 %.
   - Cajamarca y Loreto no se distinguen estadísticamente entre sí (IC superpuestos); sí se separan de Ica. Lima 27.1 % y Callao 33.9 %.
5. **Edad y jefatura.** `indicadores.csv` (método `personas`): pobreza 0–14 años = 37.5 % (36.1–38.9) frente a 21.2 % en 45–64 años (20.1–22.2). Hombres 27.4 % y mujeres 27.7 %: diferencia no concluyente (IC superpuestos).
6. **Los alimentos pesan más en el gasto de los hogares pobres y rurales.** `consultar.py --media participacion_alimentos`:
   - Por condición: no pobre 33.6 % (33.3–33.9); pobre no extremo 44.8 % (44.2–45.4); pobre extremo 51.7 % (50.4–53.0).
   - Por área: rural 49.5 % (48.9–50.0); urbana 34.2 % (33.8–34.5).
   - Área × condición (`figuras/participacion_alimentos_condicion_pobreza_area.csv`): urbana no pobre 31.3 %, urbana pobre extrema 46.7 %; rural no pobre 45.8 %, rural pobre extrema 56.0 %.

### Contraste con las cifras oficiales

- **`salidas/validacion.txt`**: pobreza nacional 27.53 % (residentes habituales) y 27.58 % (método INEI) frente a la referencia de 27.6 % (tolerancia ±0.1): **coincide**. Urbana: 24.81 % INEI / 24.74 % personas (ref. 24.8 %). Rural: 39.30 % / 39.44 % (ref. 39.3 %). Pobreza extrema 5.50 % (ref. 5.5 %). Lima Metropolitana: 28.21 % / 28.03 % (ref. 28.2 %).
- **`mapas/comparacion_referencia.txt`** (referencia de la Sesión 16 del curso): con el método INEI coinciden **25/25** departamentos (diferencia máxima 0.0 pp). Con residentes habituales coinciden 6/25, diferencia máxima 0.5 pp (Amazonas, Huánuco, Loreto, Pasco, Puno y Tumbes con ≥ 0.3 pp) y correlación de rangos 0.999.
- **Por qué difieren**: la referencia usa miembros del hogar (`factor07 × mieperho`); mi método principal usa residentes habituales (`facpob07`), que excluye a 1,787 miembros ausentes ≥ 30 días e incluye a 609 no miembros presentes ≥ 30 días (`validacion.txt`). Es una diferencia de definición de población, no un error. No se ajustó ningún dato para forzar coincidencias. Por eso las cifras departamentales de los hallazgos 4 (mapa, método INEI) y de la tabla `consultar.py` (método personas) varían unas décimas (p. ej. Puno 39.9 % frente a 40.4 %).

## 5. Visualizaciones

![Inflación general y de alimentos, Lima Metropolitana, 2019–2024](../figuras/inflacion_general_alimentos_2019_2024.png)

*Lectura:* ambas inflaciones (series `PN01273PM` y `PN09822PM`) suben desde 2021, la de alimentos llega más alto (máx. 13.2 % en 2023-02) y las dos vuelven hacia 1–3 % durante 2024.

![Pobreza monetaria por área, ENAHO 2024](../figuras/pobreza_area.png)

*Lectura:* la pobreza rural (39.4 %) supera a la urbana (24.7 %) y los intervalos de confianza no se superponen.

![Participación de los alimentos en el gasto según condición de pobreza y área](../figuras/participacion_alimentos_condicion_pobreza_area.png)

*Lectura:* en ambas áreas el peso de los alimentos crece con la pobreza; el rural no pobre (45.8 %) gasta una proporción mayor que el urbano pobre no extremo (42.3 %).

![Mapa de pobreza monetaria por departamento, ENAHO 2024 (método INEI)](../mapas/pobreza_departamento_2024_inei.png)

*Lectura:* la pobreza se concentra en la sierra norte y centro-sur (Cajamarca, Puno, Huánuco, Pasco) y en Loreto; es mínima en Ica, Moquegua y Madre de Dios.

## 6. Interpretación

- La secuencia macro fue choque (2020), rebote (2021), pico inflacionario (2022) y estancamiento en 2023, con recuperación y desinflación hacia 2024. Los alimentos tuvieron el pico más alto y tardío (feb-2023).
- En 2024 la pobreza muestra brechas marcadas por área (rural/urbana), territorio (sierra norte y Loreto frente a la costa sur y Ica) y edad (niños).
- Los hogares pobres y rurales destinan una mayor parte de su gasto a alimentos. Es una **asociación** descriptiva: sugiere que una inflación de alimentos alta podría pesar más en esos hogares, pero este análisis no lo mide.
- No se afirma que el PBI o la inflación expliquen los niveles de pobreza de 2024: no hay serie de pobreza 2019–2023 en este trabajo ni modelo causal.

## 7. Limitaciones

- **Cobertura temporal**: la macro cubre 2019–2024, pero la ENAHO es solo 2024; no hay evolución de la pobreza ni del gasto, por lo que no se puede ver cómo cambió el peso de los alimentos tras 2022.
- **Niveles de agregación distintos**: el IPC es de Lima Metropolitana, el PBI es nacional y la pobreza es nacional/departamental; series de tiempo y un corte transversal no son comparables directamente. Los precios de alimentos de Lima no representan los de Cajamarca o Loreto.
- **Calidad de datos**: la ENAHO es una encuesta muestral; los departamentos tienen IC amplios (aprox. ±4–5 pp en los más pobres), así que muchos rankings intermedios no son concluyentes. La pobreza se mide con gasto del hogar, con posibles errores de medición. La participación de alimentos usa `gashog2d`.
- **Dos métodos de población** (residentes habituales frente a miembros del hogar) dan diferencias de hasta 0.5 pp en departamentos.
- **Alcance**: son asociaciones descriptivas, sin inferencia causal. La serie de PBI es la devuelta por la herramienta como «variaciones porcentuales reales» (`PM04923AA`); no se verificaron revisiones posteriores del BCRP.
- Todas las herramientas respondieron sin fallos.

## 8. Reproducibilidad

Desde la raíz de `tarea_4/` (los zip del INEI se descargan a `datos/inei/` si faltan):

```bash
uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por area
uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por departamento --orden desc
uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --media participacion_alimentos --por condicion_pobreza
uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --media participacion_alimentos --por area
uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por area
uv run python .claude/skills/graficando-enaho/scripts/graficar.py --indicador participacion_alimentos --por condicion_pobreza --dividir area
uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --metodo inei_hogares
```

- **Series BCRP**: `PM04923AA` (PBI real, var. % anual, 2019–2024); `PN01273PM` (IPC Lima Metropolitana, var. % 12 meses, 2019-01 a 2024-12); `PN09822PM` (IPC Alimentos y Bebidas, var. % 12 meses, 2019-01 a 2024-12).
- **Llamadas MCP**: `graficar_serie(["PN01273PM","PN09822PM"], "2019-01", "2024-12", unidad="var. % 12 meses")`; `comparar_periodos` para 2019 vs 2022 y 2022 vs 2024 (ambas series de IPC).
- **Archivos**: `salidas/validacion.txt`, `salidas/indicadores.csv`, `salidas/personas_2024.parquet`, `salidas/hogares_2024.parquet`, `figuras/*.png|csv`, `mapas/*.png|csv|txt`.

## 9. Registro de herramientas

| Herramienta | Uso |
|---|---|
| MCP `bcrp` · recurso `bcrp://series-clave` | Identificar los códigos de las series |
| MCP `bcrp` · `resumen` | Máximos, mínimos y promedios (PBI, IPC general y de alimentos) |
| MCP `bcrp` · `serie` | Valores anuales del PBI 2019–2024 |
| MCP `bcrp` · `comparar_periodos` | Contraste 2019/2022 y 2022/2024 de la inflación |
| MCP `bcrp` · `graficar_serie` | Gráfico macro en `figuras/` |
| Skill `limpiando-enaho` | Base validada, pobreza por área y departamento, participación de alimentos |
| Skill `graficando-enaho` | Gráficos de pobreza por área y de alimentos por condición de pobreza |
| Skill `mapeando-enaho` | Mapa departamental y comparación con la referencia del curso |
