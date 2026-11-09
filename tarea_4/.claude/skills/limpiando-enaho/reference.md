# Referencia: ENAHO 2024 para la skill limpiando-enaho

## Archivos del INEI

| Zip (código 966 = 2024) | Archivo .dta | Una fila por | Filas | Llaves | Factor |
|---|---|---|---|---|---|
| [966-Modulo34.zip](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip) | `sumaria-2024.dta` | hogar | 33,691 | `conglome`, `vivienda`, `hogar` | `factor07` |
| [966-Modulo02.zip](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip) | `enaho01-2024-200.dta` | persona | 117,721 | las tres + `codperso` | `facpob07` |

El zip 34 también trae `sumaria-2024-12g.dta` (gasto en 12 grupos): no se usa.

## Reglas del pipeline (scripts/limpiar.py)

1. `pd.read_stata(..., convert_categoricals=False)`: códigos numéricos, no etiquetas.
2. Llaves como texto: `conglome` (6 caracteres), `vivienda` (3), `hogar` (2), `codperso` (2), `ubigeo` (6). Si se leen
   como número se pierden los ceros iniciales y la unión falla en silencio.
3. Nombres en minúscula y sin tildes: `aÑo` pasa a `anio`.
4. Residentes habituales: `((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))` → 108,664 personas.
5. `personas.merge(sumaria, on=["conglome","vivienda","hogar"], how="left", validate="m:1", indicator=True)`:
   cada persona encuentra exactamente un hogar; se verifica que no se dupliquen ni pierdan filas.
6. Variables construidas: ver tabla de abajo.
7. Validaciones esenciales (si una falla, el script termina con código 1 y borra el parquet): llaves únicas, ceros
   iniciales, 108,664 residentes, unión sin duplicados, 25 departamentos, pesos válidos, pobreza nacional a ±0.1 pp de
   27.6 % con los dos métodos.

## Variables de la base limpia (`salidas/personas_2024.parquet`)

| Variable | Origen | Valores |
|---|---|---|
| `departamento` | `ubigeo[:2]` | `01` Amazonas … `07` Callao … `15` Lima … `25` Ucayali (25 códigos) |
| `nombre_departamento` | diccionario del script | con tildes |
| `area` | `estrato <= 5` | `Urbana` (estratos 1–5) / `Rural` (6–8) |
| `dominio`, `nombre_dominio` | `dominio` | 1 Costa Norte, 2 Costa Centro, 3 Costa Sur, 4 Sierra Norte, 5 Sierra Centro, 6 Sierra Sur, 7 Selva, 8 Lima Metropolitana |
| `region_natural` | `dominio` | Costa (1–3), Sierra (4–6), Selva (7), Lima Metropolitana (8) |
| `pobreza` | sumaria | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `pobre` | `pobreza <= 2` | 0/1 |
| `pobre_extremo` | `pobreza == 1` | 0/1 |
| `sexo` | `p207` | Hombre (1) / Mujer (2) |
| `edad`, `grupo_edad` | `p208a` | años; 0-14, 15-29, 30-44, 45-64, 65 y más |
| `p203` | parentesco con el jefe | 1 jefe/a, 2 cónyuge, 3 hijo/a, … |
| `sexo_jefe` | `p207` del jefe (`p203 == 1`) | Jefe hombre / Jefa mujer |
| `condicion_pobreza` | `pobreza` | Pobre extremo / Pobre no extremo / No pobre |
| `gasto_pc_mensual` | `gashog2d / mieperho / 12` | soles corrientes por persona al mes |
| `gasto_alimentos` | suma del grupo 1 (ver abajo) | soles corrientes al año, por hogar |
| `participacion_alimentos` | `100 × gasto_alimentos / gashog2d` | % del gasto total bruto del hogar destinado a alimentos |
| `linea`, `linpe` | sumaria | línea de pobreza total y extrema (S/ por persona al mes) |
| `facpob07` | módulo 02 | factor de expansión de personas |
| `factor07`, `mieperho` | sumaria | factor del hogar y número de miembros |

`salidas/hogares_2024.parquet` tiene la sumaria con las mismas variables territoriales y `peso_inei = factor07 × mieperho`.

## Por qué hay dos métodos

- **personas** (principal): residentes habituales del módulo 02, `facpob07`. Es la unidad de análisis correcta para
  atributos individuales (sexo, edad) y es lo que pide la consigna.
- **inei_hogares**: la sumaria con `factor07 × mieperho`, que es como el INEI publica la pobreza oficial. `mieperho`
  cuenta a los miembros del hogar (`p204 == 1`, 109,842 personas), incluidos 1,787 ausentes 30 días o más; el filtro
  de residentes los excluye e incluye a 609 no miembros presentes. Esa diferencia de población explica que los
  departamentos difieran hasta 0.5 pp (Puno 40.4 % frente a 39.9 % oficial).

| Cifra 2024 | personas | inei_hogares | Referencia |
|---|---|---|---|
| Pobreza nacional | 27.53 % | 27.58 % | 27.6 % |
| Urbana / rural | 24.74 % / 39.44 % | 24.81 % / 39.30 % | 24.8 % / 39.3 % |
| Pobreza extrema | 5.50 % | — | 5.5 % |
| Lima Metropolitana | 28.03 % | 28.21 % | 28.2 % |

## Gasto en alimentos (grupo 1)

Se construye como en el do-file oficial del INEI que viene en el zip 34
(`ConstVarGasto-Metodologia actualizada.zip` → `01.ConstrVarGastoIngreso2014-2024.do`, variables `gpcrg3`, `gpcrg8` y
`gpcrg9`), pero en soles corrientes y sin deflactar:

- dentro del hogar: `gru11hd + gru12hd1 + gru12hd2 + gru13hd1 + gru13hd2 + gru13hd3`
- fuera del hogar: `sg23 + sig24 + gru14hd + gru14hd1 + gru14hd2 + gru14hd3 + gru14hd4 + gru14hd5 + sg25 + sig26 + sg27 + sig28`

`participacion_alimentos` es ese total entre `gashog2d` (gasto total bruto). Indica qué tan expuesto está el
presupuesto del hogar a los precios de los alimentos; promediada por persona con `facpob07`.

## Error estándar

`scripts/estimacion.py` calcula el EE por linealización de Taylor con conglomerado `conglome` dentro de estrato
`estrato` (equivalente a `svyset conglome [pw=facpob07], strata(estrato)` en Stata). El IC 95 % es ±1.96 EE.
