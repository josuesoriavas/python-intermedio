# Verificación manual de cifras del informe

Revisé 15 cifras de `informe_final.md` (6 del BCRP y 9 de la ENAHO) por un camino distinto al del agente. El agente obtuvo las cifras con el servidor MCP `bcrp` y con los scripts de las skills. La verificación no usa ninguno de los dos:

1. **Recálculo independiente.** `scripts/verificar_informe.py` llama directamente a la API del BCRP con `httpx` y lee los `.dta` del INEI con `pandas`, con tasas ponderadas escritas aparte. No importa `mcp/server.py`, `limpiar.py`, `estimacion.py` ni `consultar.py`. El resultado está en [`verificacion_cifras.csv`](verificacion_cifras.csv): **15 de 15 cifras coinciden** con el valor del informe redondeado a un decimal.
2. **Consulta a mano en la web del BCRP.** El 9/11/2026 abrí las tablas HTML de BCRPData en el navegador y leí los valores en pantalla.
3. **Contraste con cifras publicadas.** Para la ENAHO usé las cifras oficiales del INEI (informe técnico de pobreza monetaria 2024) y la referencia departamental de la sesión 16 (`.claude/skills/mapeando-enaho/referencias/pobreza_departamento_2024.csv`).

## Cifras revisadas

| # | Afirmación del informe | Fuente | Informe | Recálculo independiente | Revisión manual | ¿Coincide? |
|---|---|---|---|---|---|---|
| 1 | El PBI real creció 3.5 % en 2024 y cayó 10.9 % en 2020 | BCRP `PM04923AA` | 3.5 / −10.9 | 3.5153 / −10.9333 | Tabla web anual 2019–2024: «2020 -10,9 … 2024 3,5» | Sí |
| 2 | La inflación de alimentos tocó su máximo de 13.2 % en feb-2023 | BCRP `PN09822PM` | 13.2 (feb-2023) | 13.1637, máximo de 72 meses en Feb.2023 | Tabla web dic-2022 a abr-2023: «Feb23 13.16», con 12.93 en enero y 12.81 en marzo | Sí |
| 3 | La inflación general tocó su máximo de 8.8 % en jun-2022 | BCRP `PN01273PM` | 8.8 (jun-2022) | 8.8126 en Jun.2022 | Tabla web may–jul 2022: «Jun22 8.81», con 8.09 en mayo y 8.74 en julio | Sí |
| 4 | Promedio 2022 de la inflación de alimentos: 10.8 %, con una caída de 8.8 pp hacia 2024 | BCRP `PN09822PM` (`comparar_periodos`) | 10.8 / −8.8 | 10.7757 / −8.7610 | — | Sí |
| 5 | Pobreza nacional: 27.5 % con residentes y `facpob07`, 27.6 % con el método INEI | ENAHO 2024 | 27.5 / 27.6 | 27.5287 / 27.5795 | Cifra oficial del INEI: 27.6 % | Sí |
| 6 | Pobreza rural 39.4 %, urbana 24.7 %, Sierra 31.1 % | ENAHO 2024 | 39.4 / 24.7 / 31.1 | 39.4417 / 24.7352 / 31.1231 | Oficial INEI: rural 39.3 %, urbana 24.8 %. Hay una diferencia de 0.1 pp por la población de referencia (ver abajo) | Sí* |
| 7 | Cajamarca tiene la mayor pobreza (45.0 %) e Ica la menor (5.9 %) | ENAHO 2024 | 45.0 / 5.9 | 44.9950 / 5.9139 | Referencia de la sesión 16: Cajamarca 45.0, Ica 6.0 | Sí* |
| 8 | Peso de los alimentos en el gasto: 51.7 % en pobres extremos y 33.6 % en no pobres | ENAHO 2024 | 51.7 / 33.6 | 51.6872 / 33.6310 | — | Sí |

\* El recálculo con la misma población (residentes habituales con `facpob07`) da exactamente las cifras del informe. Las publicadas por el INEI y la referencia del curso usan miembros del hogar con `factor07 × mieperho`. Esa diferencia de definición explica las décimas (0.1 pp en rural, urbana e Ica). Con el método INEI, el proyecto reproduce las 25 cifras departamentales de la referencia (`mapas/comparacion_referencia.txt`) y las nacionales oficiales (`salidas/validacion.txt`). El informe advierte esta diferencia en «Limitaciones» y en «Reproducibilidad».

## Resultado

- **Coincidencias:** las 15 cifras revisadas coinciden con el recálculo independiente (diferencia menor a 0.05, es decir, solo de redondeo). Las 4 cifras del BCRP revisadas en la web coinciden con la tabla publicada.
- **Diferencias:** solo hay diferencias de 0.1 pp frente a las cifras oficiales del INEI, y se deben a la definición de población, no a un error.
- **No encontré** cifras del informe que no vengan de una herramienta ni cifras inventadas.

Para reproducir:

```bash
uv run python scripts/verificar_informe.py
```
