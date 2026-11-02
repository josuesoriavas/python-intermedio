# 🌊🌾 El Niño y el agro peruano

**Tarea 3 – Python Intermedio · Del dato a la historia: dashboard interactivo y reel con IA**

| | |
|---|---|
| **Dashboard público** | https://josuesoriavas.github.io/python-intermedio/tarea_3/web/ |
| **Publicación de LinkedIn** | _(pendiente: se agrega al publicar el reel)_ |
| **Código y datos** | esta carpeta (`tarea_3/`) |

## Tema y pregunta de investigación

**Tema:** impacto de El Niño costero en la agricultura del Perú.

**Pregunta:** *¿Cómo afectan los eventos El Niño costero a la producción agrícola del Perú y qué cultivos son más vulnerables?*

- **Cobertura geográfica:** Perú (27 cultivos). El mapa compara 198 países.
- **Cobertura temporal:** producción agrícola 1961-2024 y temperatura del mar de enero de 1950 a septiembre de 2026.

El tema es de actualidad: en septiembre de 2026 el mar frente al Perú (región Niño 1+2) estaba **4.7 °C por encima de lo normal** y hay un Niño costero fuerte en curso. Los Niños anteriores ayudan a anticipar qué cultivos están en riesgo.

## Descripción del proyecto

1. `scripts/obtener_datos.py` descarga las fuentes originales: dos archivos de texto de NOAA y el archivo masivo de FAOSTAT.
2. `scripts/procesar_datos.py` reconstruye el **ICEN** (Índice Costero El Niño de ENFEN), identifica los eventos El Niño costero, limpia FAOSTAT y calcula el **desvío de cada año respecto a su tendencia** para cada cultivo y país.
3. `scripts/analizar_datos.py` compara los años Niño con los años sin Niño, calcula la significancia con una prueba de permutación y exporta los JSON del dashboard.
4. `web/` es el dashboard: HTML, CSS y JavaScript con Plotly.js, publicado en GitHub Pages. Incluye 5 KPIs, 6 visualizaciones (con un mapa mundial), 7 controles interactivos y descarga de datos en CSV.
5. `reel/` contiene el guion, los subtítulos y los recursos del video.

## Fuentes de datos

| Fuente | Qué aporta | Enlace | Fecha |
|---|---|---|---|
| NOAA CPC – ERSSTv5 | Temperatura del mar mensual en Niño 1+2 y 3.4 desde 1950 (anomalías base 1991-2020) | https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii | Descargado el 01/11/2026 (datos hasta jun-2026) |
| NOAA CPC – OISST v2 | Mismas regiones, datos recientes (estado actual) | https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices | Descargado el 01/11/2026 (datos hasta sep-2026) |
| FAOSTAT (FAO) – QCL | Producción, área cosechada y rendimiento por cultivo, país y año | https://www.fao.org/faostat/es/#data/QCL · [archivo masivo](https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip) | Actualización FAO: 31/12/2025 (datos hasta 2024) |
| ENFEN | Definición y umbrales del ICEN (Nota Técnica 01-2012) | https://www.gob.pe/enfen | — |

Los archivos de NOAA están en `datos/originales/`. El zip de FAOSTAT (34 MB) no se sube; `obtener_datos.py` lo descarga, y `datos/originales/fuentes.json` registra la URL y la fecha de cada descarga.

## Metodología

- **ICEN reconstruido.** Media móvil centrada de 3 meses de la anomalía de temperatura del mar en Niño 1+2 (ERSSTv5), la misma definición que usa ENFEN. Categorías: cálida débil (> 0.4 °C), moderada (> 1.0), fuerte (> 1.7) y extraordinaria (> 3.0). Un **evento El Niño costero** son 3 o más meses seguidos con ICEN > 0.4 °C. Se detectan 26 eventos desde 1950, entre ellos 1982-83 (máximo de 3.96 °C) y 1997-98 (4.13 °C) como extraordinarios, y 2017 (1.34 °C, moderado) y 2023-24 (2.92 °C, fuerte), en línea con las clasificaciones de ENFEN.
- **Intensidad de cada año.** ICEN promedio de enero a junio, la temporada de lluvias en la costa norte y de la mayor parte de las cosechas.
  - **Años Niño moderado o mayor:** promedio > 1.0 °C. Son 6 años: 1983, 1987, 1992, 1998, 2016 y 2023.
  - **Años sin Niño:** promedio ≤ 0.4 °C.
- **Desvío respecto a la tendencia.** `desvío(t) = valor(t) / mediana(valores de t−3…t−1 y t+1…t+3) − 1`, con al menos 3 vecinos con dato. Así se separa el golpe de un mal año del crecimiento de largo plazo (por ejemplo, el boom del arándano).
- **Vulnerabilidad.** Desvío promedio en años Niño menos desvío promedio en años sin Niño. La significancia se estima con una **prueba de permutación** de 20 000 repeticiones (p-valor unilateral).
- **Limpieza.** De 606 043 registros de los cultivos elegidos quedan 583 226: se descartan los que no tienen dato (flag `M`), los valores no positivos y los duplicados. El rendimiento se pasa de kg/ha a t/ha, los países se identifican con su código ISO-3 (sin agregados regionales) y el mapa excluye a los productores con tendencia menor a 500 t.

## Tres hallazgos principales

1. **Hay un Niño costero fuerte en curso.** En septiembre de 2026 la anomalía en Niño 1+2 fue de **+4.69 °C** (OISST). El ICEN llegó a **1.98 °C en mayo de 2026** (categoría fuerte), un nivel que solo superaron seis eventos desde 1950: 1957, 1972, 1982-83, 1997-98, 2015-16 y 2023-24.
2. **Algodón, quinua, mango, cebada y limón son los cultivos más golpeados.** En los años con Niño moderado o mayor, su producción quedó por debajo de la tendencia, mientras que en los años sin Niño estuvo por encima:

   | Cultivo | Años Niño | Años sin Niño | Diferencia | p-valor |
   |---|---|---|---|---|
   | Algodón | −23.9 % | +6.8 % | −30.7 pp | 0.012 |
   | Quinua | −22.4 % | +4.2 % | −26.6 pp | 0.013 |
   | Mango | −17.0 % | +4.6 % | −21.6 pp | 0.007 |
   | Cebada | −13.6 % | +0.7 % | −14.3 pp | 0.005 |
   | Limón | −8.0 % | +2.3 % | −10.3 pp | 0.041 |

   El daño no es solo costero: la quinua y la cebada son altoandinas y sufren la sequía que El Niño suele llevar al sur del país.
3. **La agroexportación moderna resiste mejor, pero el mango no.** Palta, uva, espárrago, café y cacao no muestran pérdidas significativas (p > 0.10). El mango, en cambio, cayó **29 % en 2023 y 25 % en 2024** respecto a su tendencia: un solo evento le costó dos campañas. En 1983, el algodón perdió el 62 % y el limón el 40 %.

El detalle completo está en `datos/procesados/vulnerabilidad_cultivos.csv` y `datos/procesados/hallazgos.json`.

## Limitaciones

- Los datos de FAOSTAT son **anuales y nacionales**: no muestran el daño por región ni por mes, y un año calendario mezcla dos campañas (por ejemplo, la cosecha de mango va de noviembre a marzo).
- Es una **asociación, no una prueba de causalidad**: en los mismos años influyen los precios, las plagas, el crédito, la violencia de los años 80 y la expansión del riego.
- Solo hay **seis años con Niño moderado o mayor** desde 1961, así que cada evento pesa mucho en los promedios.
- El ICEN es una **reconstrucción** con ERSSTv5 (base 1991-2020) y puede diferir unas décimas del valor oficial de ENFEN. El evento de 2026 aún no tiene datos de cosecha.
- Parte de los valores de FAOSTAT son estimados o imputados por la FAO (columna `flag_produccion`).

## Cómo reproducir

```bash
cd tarea_3
python -m venv .venv && .venv/Scripts/activate   # en Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python scripts/obtener_datos.py     # descarga NOAA + FAOSTAT (~34 MB)
python scripts/procesar_datos.py    # ICEN, eventos, desvíos -> datos/procesados/
python scripts/analizar_datos.py    # vulnerabilidad, hallazgos y web/data/*.json
python -m http.server 8000 --directory web   # abre http://localhost:8000
```

El dashboard es estático: GitHub Pages sirve la carpeta `web/` sin servidor ni Python.

## Estructura

```
tarea_3/
├── README.md
├── requirements.txt
├── datos/
│   ├── originales/      # índices NOAA + registro de fuentes (el zip FAOSTAT se descarga)
│   └── procesados/      # ICEN, eventos, cultivos del Perú, desvíos por país, hallazgos
├── scripts/             # obtener_datos.py, procesar_datos.py, analizar_datos.py
├── web/                 # dashboard (index.html, assets/, data/)
└── reel/                # guion, subtítulos y recursos del video
```

## Uso de inteligencia artificial

Usé **Claude Code** (Anthropic) para buscar y comparar fuentes de datos, escribir los scripts de descarga, limpieza y análisis, construir el dashboard y redactar el guion del reel. La narración del reel se genera con un modelo de clonación de voz a partir de una grabación de mi propia voz, y el video lo indica. Revisé las cifras del dashboard, del README y del guion contra los archivos procesados, y la clasificación de eventos contra los registros de ENFEN. La responsabilidad sobre los resultados es mía.
