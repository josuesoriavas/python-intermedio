# Desarrollo de las Skills de ENAHO

Parte de `conversacion_completa.md` (fase «skills»).

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\estimacion.py",
 "content": "\"\"\"Estimaciones ponderadas de la ENAHO con su error estándar de diseño (lo usan las tres skills).\n\nproporcion(df, \"pobre\", peso=\"facpob07\", por=\"area\") devuelve, para cada grupo, el % ponderado, el error estándar\npor linealización de Taylor (diseño: conglomerado `conglome` dentro de estrato `estrato`, como en el svyset del INEI),\nel intervalo de confianza al 95 %, el n muestral y la población expandida. Nunca un promedio simple.\n\"\"\"\nimport numpy as np\nimport pandas as pd\n\nZ95 = 1.959964\n\n\ndef _varianza_diseno(z, psu, estrato):\n    \"\"\"Varianza con reemplazo de un total linealizado z: sum_h n_h/(n_h-1) * sum_i (z_hi - zbar_h)^2.\"\"\"\n    t = pd.DataFrame({\"z\": z, \"psu\": psu, \"h\": estrato}).groupby([\"h\", \"psu\"], observed=True).z.sum().reset_index()\n    var = 0.0\n    for _, g in t.groupby(\"h\", observed=True):\n        n = len(g)\n        if n > 1:\n            var += n / (n - 1) * ((g.z - g.z.mean()) ** 2).sum()\n    return var\n\n\ndef proporcion(df, variable, peso=\"facpob07\", por=None, psu=\"conglome\", estrato=\"estrato\"):\n    \"\"\"% ponderado de `variable` (0/1) en toda la base o por grupos, con EE de diseño e IC 95 %.\"\"\"\n    if df[peso].isna().any() or (df[peso] <= 0).any():\n        raise ValueError(f\"El factor {peso} tiene valores nulos o no positivos.\")\n    y = df[variable].astype(float).to_numpy()\n    w = df[peso].astype(float).to_numpy()\n    grupos = [(\"Total\", np.ones(len(df), dtype=bool))] if por is None else \\\n        [(g, (df[por] == g).to_numpy()) for g in sorted(df[por].dropna().unique())]\n    filas = []\n    for g, d in grupos:\n        wd = w * d\n        W = wd.sum()\n        p = (wd * y).sum() / W\n        z = wd * (y - p) / W          # linealización del cociente; cero fuera del dominio\n        ee = np.sqrt(_varianza_diseno(z, df[psu].to_numpy(), df[estrato].to_numpy()))\n        filas.append({\"grupo\": g, \"valor_pct\": 100 * p, \"ee_pct\": 100 * ee,\n                      \"ic95_inf\": 100 * (p - Z95 * ee), \"ic95_sup\": 100 * (p + Z95 * ee),\n                      \"n_muestra\": int(d.sum()), \"poblacion_expandida\": W})\n    return pd.DataFrame(filas)\n\n\ndef promedio_simple(df, variable, por=None):\n    \"\"\"Solo para mostrar en la validación cuánto se equivoca no ponderar. No usar para reportar.\"\"\"\n    if por is 
… [recortado: 103 caracteres más]
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\estimacion.py (file state is current in your context — no need to Read it back)
```
</details>

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "content": "\"\"\"Limpia la ENAHO 2024 (módulos 34 y 02), arma la base de personas con pobreza y factor de expansión, y la valida.\n\n    uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py            # 2024, descarga los zip si faltan\n\nPipeline (siempre en este orden; ver reference.md):\n  1. Leer los .dta desde los zip del INEI con convert_categoricals=False y las llaves como texto (ceros iniciales).\n  2. Normalizar nombres de columna (minúsculas, sin tildes; «aÑo» -> «anio»).\n  3. Filtrar residentes habituales: (p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1).\n  4. Unir personas (m) con hogares (1) por conglome, vivienda y hogar con merge(validate=\"m:1\").\n  5. Construir departamento = ubigeo[:2], área (estrato <= 5 urbana), pobre (pobreza <= 2), sexo, edad, etc.\n  6. Validar contra las cifras oficiales; si falla una validación esencial, se detiene con código 1.\n  7. Guardar salidas/personas_2024.parquet, salidas/validacion.txt y salidas/indicadores.csv.\n\nLas cifras salen del procesamiento: no hay ningún valor de resultado escrito a mano. Los valores de referencia\n(27.6 %, 108,664, 25) solo se usan para comparar y aprobar o rechazar.\n\"\"\"\nimport argparse\nimport io\nimport sys\nimport unicodedata\nimport zipfile\nfrom datetime import datetime\nfrom pathlib import Path\n\nimport httpx\nimport pandas as pd\n\nsys.path.insert(0, str(Path(__file__).parent))\nfrom estimacion import promedio_simple, proporcion  # noqa: E402\n\nPROYECTO = Path(__file__).resolve().parents[4]\nURL_INEI = \"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip\"\nCODIGO_INEI = {2024: 966}\nARCHIVOS = {\"34\": \"sumaria-{anio}.dta\", \"02\": \"enaho01-{anio}-200.dta\"}\nLLAVES_HOGAR = [\"conglome\", \"vivienda\", \"hogar\"]\nANCHO_LLAVES = {\"conglome\": 6, \"vivienda\": 3, \"hogar\": 2, \"codperso\": 2, \"ubigeo\": 6}\n\n# Valores publicados por el INEI / la Sesión 16 para validar (no se usan como resultados).\nREFERENCIAS = {2024: {\"hogares\": 33_691, \"filas_modulo02\": 117_721, \"residentes\": 108_664, \"departamentos\": 25,\n                      \"pobreza\": 27.6, \"pobreza_extrema\": 5.5, \"urbana\": 24.8, \"rural\": 39.3,\n                      \"lima_metropolitana\": 28.2}}\nTOL_NACIONAL = 0.1   # puntos porcentuales, según la consigna\nTOL_GRUPOS = 0.15    # área, extrema
… [recortado: 14,880 caracteres más]
```

**🔧 Bash**

```json
{
 "command": "time PYTHONIOENCODING=utf-8 uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py; echo \"exit=$?\"",
 "description": "Run the ENAHO cleaning script and validations",
 "timeout": 600000
}
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
VALIDACIÓN ENAHO 2024 · skill limpiando-enaho
Generado: 2026-11-09 11:47 · script: .claude/skills/limpiando-enaho/scripts/limpiar.py
Fuente: INEI, ENAHO 2024 (código 966): 966-Modulo34.zip:966-Modulo34/sumaria-2024.dta y 966-Modulo02.zip:966-Modulo02/enaho01-2024-200.dta
Unidad de análisis: personas residentes habituales. Peso: facpob07 (factor de expansión poblacional).
E = validación esencial (si falla, el proceso se detiene); A = advertencia.

[APROBADA] E  Llaves de hogar únicas en la sumaria (conglome, vivienda, hogar)
              33,691 hogares (ref. 33,691), 0 duplicados
[APROBADA] E  Llaves de persona únicas en el módulo 02 (+ codperso)
              117,721 filas (ref. 117,721), 0 duplicados
[APROBADA] E  Llaves leídas como texto con ceros iniciales
              conglome: 6 car. (0 mal), vivienda: 3 car. (0 mal), hogar: 2 car. (0 mal), codperso: 2 car. (0 mal), ubigeo: 6 car. (0 mal)
[APROBADA] E  Residentes habituales
              108,664 (ref. 108,664) con (p204==1 & p205==2) | (p204==2 & p206==1)
[APROBADA] E  Unión m:1 personas-hogares sin duplicar ni perder filas
              108,664 antes, 108,664 después, 0 personas sin hogar en la sumaria
[APROBADA] E  25 códigos departamentales (ubigeo[:2] = 01..25, Lima 15 y Callao 07 separados)
              25 códigos: 01..25
[APROBADA] E  Factores de expansión válidos (facpob07 y factor07 > 0, sin nulos)
              población expandida (Σ facpob07) = 34,147,768 personas
[APROBADA] E  Pobreza mo
… [recortado: 1,062 caracteres más]
```
</details>

**🔧 Bash**

```json
{
 "command": "cp \"/c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref16/pobreza_departamento_2024.csv\" datos/ref_s16.csv && PYTHONIOENCODING=utf-8 uv run python - <<'EOF'\nimport pandas as pd, zipfile, io\nb = pd.read_parquet(\"salidas/personas_2024.parquet\")\nref = pd.read_csv(\"datos/ref_s16.csv\", dtype={\"ccdd\": str}).set_index(\"ccdd\").pobreza_pct\ndef wm(df, w, by):\n    return df.groupby(by).apply(lambda g: 100*(g[w]*g.pobre).sum()/g[w].sum(), include_groups=False)\na = wm(b, \"facpob07\", \"departamento\"); c = wm(b, \"factor07\", \"departamento\")\nwith zipfile.ZipFile(\"datos/inei/966-Modulo34.zip\") as z:\n    s = pd.read_stata(io.BytesIO(z.read(\"966-Modulo34/sumaria-2024.dta\")), convert_categoricals=False, columns=[\"ubigeo\",\"pobreza\",\"factor07\",\"mieperho\",\"estrato\",\"dominio\"])\ns[\"w\"] = s.factor07*s.mieperho; s[\"pobre\"]=(s.pobreza<=2).astype(int); s[\"dep\"]=s.ubigeo.str[:2]\nd = wm(s, \"w\", \"dep\")\nt = pd.DataFrame({\"ref\": ref, \"facpob07\": a.round(1), \"factor07_pers\": c.round(1), \"sumaria\": d.round(1)})\nprint(t.to_string())\nfor col in [\"facpob07\",\"factor07_pers\",\"sumaria\"]:\n    print(col, \"max|dif|\", (t[col]-t.ref).abs().max(), \"n coinciden\", (t[col]==t.ref).sum())\nprint(\"factor07 personas nacional\", (b.factor07*b.pobre).sum()/b.factor07.sum()*100)\nprint(\"area facpob07/factor07:\", wm(b,\"facpob07\",\"area\").round(2).to_dict(), wm(b,\"factor07\",\"area\").round(2).to_dict(), \"sumaria\", wm(s.assign(area=(s.estrato<=5)),\"w\",\"area\").round(2).to_dict())\nprint(\"lima met sumaria\", wm(s,\"w\",\"dominio\").round(2).to_dict())\nprint(\"residentes vs mieperho:\", len(b), s.mieperho.sum())\nEOF",
 "description": "Compare department poverty by weighting method vs reference",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
ref   facpob07  factor07_pers  sumaria
01  25.7  26.100000      26.100000     25.7
02  22.8  22.900000      22.900000     22.8
03  24.0  24.100000      24.100000     24.0
04  15.8  15.800000      15.800000     15.8
05  32.8  33.000000      33.000000     32.8
06  45.0  45.000000      45.000000     45.0
07  33.9  33.799999      33.799999     33.9
08  18.5  18.500000      18.500000     18.5
09  33.4  33.599998      33.599998     33.4
10  39.0  39.500000      39.500000     39.0
11   6.0   5.900000       5.900000      6.0
12  18.5  18.600000      18.600000     18.5
13  30.2  30.100000      30.100000     30.2
14  14.0  14.100000      14.100000     14.0
15  27.1  26.900000      26.900000     27.1
16  43.0  42.599998      42.599998     43.0
17  11.1  11.100000      11.100000     11.1
18  11.0  10.900000      10.900000     11.0
19  39.0  39.299999      39.299999     39.0
20  31.9  31.799999      31.799999     31.9
21  39.9  40.400002      40.400002     39.9
22  22.0  22.000000      22.000000     22.0
23  24.0  23.900000      23.900000     24.0
24  26.9  26.600000      26.600000     26.9
25  27.1  27.100000      27.100000     27.1
facpob07 max|dif| 0.5000015258789077 n coinciden 3
factor07_pers max|dif| 0.5000015258789077 n coinciden 3
sumaria max|dif| 0.0 n coinciden 25
factor07 personas nacional 27.528732
area facpob07/factor07: {'Rural': 39.439998626708984, 'Urbana': 24.739999771118164} {'Rural': 39.439998626708984, 'Urbana': 24.739999771118164} sumaria
… [recortado: 162 caracteres más]
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "    contexto = {\"sumaria\": sumaria, \"miembros_filas\": filas_modulo02, \"n_residentes\": n_residentes,\n                \"sin_hogar\": sin_hogar, \"archivos\": (f\"{zip34.name}:{arch34}\", f\"{zip02.name}:{arch02}\"),\n                \"miembros\": miembros}\n    return base[columnas], contexto",
 "new_string": "    # Base de hogares para el método oficial del INEI: cada hogar pesa factor07 × mieperho (miembros del hogar)\n    hogares = sumaria.copy()\n    hogares[\"departamento\"] = hogares.ubigeo.str[:2]\n    hogares[\"nombre_departamento\"] = hogares.departamento.map(DEPARTAMENTOS)\n    hogares[\"area\"] = (hogares.estrato <= 5).map({True: \"Urbana\", False: \"Rural\"})\n    hogares[\"pobre\"] = (hogares.pobreza <= 2).astype(\"int8\")\n    hogares[\"pobre_extremo\"] = (hogares.pobreza == 1).astype(\"int8\")\n    hogares[\"nombre_dominio\"] = hogares.dominio.map(DOMINIOS)\n    hogares[\"region_natural\"] = hogares.dominio.map(REGION_NATURAL)\n    hogares[\"peso_inei\"] = hogares.factor07 * hogares.mieperho\n    hogares = hogares[hogares.mieperho > 0]\n    hogares[\"anio\"] = anio\n\n    contexto = {\"sumaria\": sumaria, \"miembros_filas\": filas_modulo02, \"n_residentes\": n_residentes,\n                \"sin_hogar\": sin_hogar, \"archivos\": (f\"{zip34.name}:{arch34}\", f\"{zip02.name}:{arch02}\"),\n                \"miembros\": miembros, \"hogares\": hogares}\n    return base[columnas], contexto"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "    w = sumaria.factor07 * sumaria.mieperho\n    hog = 100 * (w * (sumaria.pobreza <= 2)).sum() / w.sum()\n    check(\"Pobreza monetaria nacional (método INEI: sumaria, factor07 × mieperho)\",\n          abs(hog - ref[\"pobreza\"]) <= TOL_NACIONAL, f\"{hog:.2f} % (ref. {ref['pobreza']} %, tol. ±{TOL_NACIONAL})\")\n    simple = promedio_simple(base, \"pobre\")\n    check(\"La ponderación cambia el resultado (promedio simple ≠ ponderado)\", abs(simple - nac.valor_pct) > 0.5,\n          f\"sin ponderar daría {simple:.2f} %: {simple - nac.valor_pct:+.2f} pp de sesgo\", esencial=False)\n    ext = proporcion(base, \"pobre_extremo\").iloc[0]\n    check(\"Pobreza extrema nacional\", abs(ext.valor_pct - ref[\"pobreza_extrema\"]) <= TOL_GRUPOS,\n          f\"{ext.valor_pct:.2f} % (ref. {ref['pobreza_extrema']} %)\", esencial=False)\n    area = proporcion(base, \"pobre\", por=\"area\").set_index(\"grupo\").valor_pct\n    for g, k in ((\"Urbana\", \"urbana\"), (\"Rural\", \"rural\")):\n        check(f\"Pobreza {k}\", abs(area[g] - ref[k]) <= TOL_GRUPOS, f\"{area[g]:.2f} % (ref. {ref[k]} %)\", esencial=False)\n    lima = proporcion(base[base.dominio == 8], \"pobre\").iloc[0].valor_pct\n    check(\"Pobreza en Lima Metropolitana (dominio 8)\", abs(lima - ref[\"lima_metropolitana\"]) <= TOL_GRUPOS,\n          f\"{lima:.2f} % (ref. {ref['lima_metropolitana']} %)\", esencial=False)\n    return checks, {\"nacional\": nac, \"hogares_metodo_inei\": hog, \"simple\": simple}",
 "new_string": "    hogares = ctx[\"hogares\"]\n    hog = proporcion(hogares, \"pobre\", peso=\"peso_inei\").iloc[0].valor_pct\n    check(\"Pobreza monetaria nacional (método INEI: sumaria, factor07 × mieperho)\",\n          abs(hog - ref[\"pobreza\"]) <= TOL_NACIONAL, f\"{hog:.2f} % (ref. {ref['pobreza']} %, tol. ±{TOL_NACIONAL})\")\n    simple = promedio_simple(base, \"pobre\")\n    check(\"La ponderación cambia el resultado (promedio simple ≠ ponderado)\", abs(simple - nac.valor_pct) > 0.5,\n          f\"sin ponderar daría {simple:.2f} %: {simple - nac.valor_pct:+.2f} pp de sesgo\", esencial=False)\n    ext = proporcion(base, \"pobre_extremo\").iloc[0]\n    check(\"Pobreza extrema nacional (personas, facpob07)\", abs(ext.valor_pct - ref[\"pobreza_extrema\"]) <= TOL_GRUPOS,\n          f\"{ext.valor_pct:.2f} % (ref. {ref['pobreza_e
… [recortado: 1,326 caracteres más]
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "def indicadores(base, anio):\n    filas = []\n    dims = [(\"nacional\", None), (\"area\", \"area\"), (\"sexo\", \"sexo\"), (\"grupo_edad\", \"grupo_edad\"),\n            (\"sexo_jefe\", \"sexo_jefe\"), (\"region_natural\", \"region_natural\"), (\"dominio\", \"nombre_dominio\"),\n            (\"departamento\", \"departamento\")]\n    for indicador in (\"pobre\", \"pobre_extremo\"):\n        for dim, col in dims:\n            t = proporcion(base, indicador, por=col)\n            t.insert(0, \"dimension\", dim)\n            t.insert(2, \"indicador\", \"pobreza\" if indicador == \"pobre\" else \"pobreza_extrema\")\n            if dim == \"departamento\":\n                t.insert(2, \"nombre\", t.grupo.map(DEPARTAMENTOS))\n            filas.append(t)\n    out = pd.concat(filas, ignore_index=True)\n    out[\"nombre\"] = out[\"nombre\"].fillna(out.grupo)\n    out[\"anio\"] = anio\n    out[\"peso\"] = \"facpob07\"\n    out[\"fuente\"] = f\"INEI, ENAHO {anio} (módulos 34 y 02); residentes habituales\"\n    for c in (\"valor_pct\", \"ee_pct\", \"ic95_inf\", \"ic95_sup\"):\n        out[c] = out[c].round(3)\n    out[\"poblacion_expandida\"] = out.poblacion_expandida.round(0).astype(\"int64\")\n    return out[[\"anio\", \"dimension\", \"grupo\", \"nombre\", \"indicador\", \"valor_pct\", \"ee_pct\", \"ic95_inf\", \"ic95_sup\",\n                \"n_muestra\", \"poblacion_expandida\", \"peso\", \"fuente\"]]",
 "new_string": "def indicadores(base, hogares, anio):\n    \"\"\"Tabla larga de indicadores. metodo = personas (residentes habituales, facpob07; principal) o\n    inei_hogares (sumaria, factor07 × mieperho; reproduce las cifras oficiales, solo dimensiones del hogar).\"\"\"\n    filas = []\n    dims_hogar = [(\"nacional\", None), (\"area\", \"area\"), (\"region_natural\", \"region_natural\"),\n                  (\"dominio\", \"nombre_dominio\"), (\"departamento\", \"departamento\")]\n    dims_persona = dims_hogar + [(\"sexo\", \"sexo\"), (\"grupo_edad\", \"grupo_edad\"), (\"sexo_jefe\", \"sexo_jefe\")]\n    for metodo, df, peso, dims, n_unidad in ((\"personas\", base, \"facpob07\", dims_persona, \"personas\"),\n                                             (\"inei_hogares\", hogares, \"peso_inei\", dims_hogar, \"hogares\")):\n        for indicador in (\"pobre\", \"pobre_extremo\"):\n          
… [recortado: 1,052 caracteres más]
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "               \"\", f\"Pobreza nacional {anio}: {resumen['nacional'].valor_pct:.2f} % de las personas (facpob07) · \"\n                   f\"{resumen['hogares_metodo_inei']:.2f} % con el método INEI (factor07 × mieperho) · \"\n                   f\"redondeado: {round(resumen['nacional'].valor_pct, 1)} %\"]",
 "new_string": "               \"\", f\"Pobreza nacional {anio}: {resumen['nacional'].valor_pct:.2f} % de las personas (facpob07) · \"\n                   f\"{resumen['hogares_metodo_inei']:.2f} % con el método INEI (factor07 × mieperho).\",\n               \"\",\n               \"Nota sobre los dos métodos. La base principal son los residentes habituales del módulo 02 \"\n               f\"({ctx['n_residentes']:,} personas) ponderados con facpob07. El INEI publica la pobreza con la sumaria, \"\n               f\"donde cada hogar pesa factor07 × mieperho ({resumen['miembros_mieperho']:,} miembros del hogar: \"\n               \"incluye a los miembros ausentes más de 30 días, p204 == 1 y p205 == 1, que el filtro de residentes \"\n               \"excluye). Por eso las cifras de residentes difieren unas décimas de las oficiales. El método INEI se \"\n               \"usa para validar contra las cifras publicadas y está en indicadores.csv con metodo = inei_hogares.\"]"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "    base.to_parquet(salidas / f\"personas_{a.anio}.parquet\", index=False)\n    ind = indicadores(base, a.anio)\n    ind.to_csv(salidas / \"indicadores.csv\", index=False, encoding=\"utf-8\")\n    print(f\"OK: salidas/personas_{a.anio}.parquet ({len(base):,} personas), salidas/indicadores.csv ({len(ind)} filas), \"\n          \"salidas/validacion.txt\")",
 "new_string": "    base.to_parquet(salidas / f\"personas_{a.anio}.parquet\", index=False)\n    hogares = ctx[\"hogares\"]\n    hogares.to_parquet(salidas / f\"hogares_{a.anio}.parquet\", index=False)\n    ind = indicadores(base, hogares, a.anio)\n    ind.to_csv(salidas / \"indicadores.csv\", index=False, encoding=\"utf-8\")\n    print(f\"OK: salidas/personas_{a.anio}.parquet ({len(base):,} personas), salidas/hogares_{a.anio}.parquet \"\n          f\"({len(hogares):,} hogares), salidas/indicadores.csv ({len(ind)} filas), salidas/validacion.txt\")"
}
```

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py | tail -32; echo \"exit=$?\"; head -3 salidas/indicadores.csv; grep -c . salidas/indicadores.csv",
 "description": "Re-run cleaning with both estimation methods",
 "timeout": 600000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
conglome: 6 car. (0 mal), vivienda: 3 car. (0 mal), hogar: 2 car. (0 mal), codperso: 2 car. (0 mal), ubigeo: 6 car. (0 mal)
[APROBADA] E  Residentes habituales
              108,664 (ref. 108,664) con (p204==1 & p205==2) | (p204==2 & p206==1)
[APROBADA] E  Unión m:1 personas-hogares sin duplicar ni perder filas
              108,664 antes, 108,664 después, 0 personas sin hogar en la sumaria
[APROBADA] E  25 códigos departamentales (ubigeo[:2] = 01..25, Lima 15 y Callao 07 separados)
              25 códigos: 01..25
[APROBADA] E  Factores de expansión válidos (facpob07 y factor07 > 0, sin nulos)
              población expandida (Σ facpob07) = 34,147,768 personas
[APROBADA] E  Pobreza monetaria nacional (personas, facpob07)
              27.53 % (ref. 27.6 %, tol. ±0.1); IC95 26.51–28.55
[APROBADA] E  Pobreza monetaria nacional (método INEI: sumaria, factor07 × mieperho)
              27.58 % (ref. 27.6 %, tol. ±0.1)
[APROBADA] A  La ponderación cambia el resultado (promedio simple ≠ ponderado)
              sin ponderar daría 25.61 %: -1.92 pp de sesgo
[APROBADA] A  Pobreza extrema nacional (personas, facpob07)
              5.50 % (ref. 5.5 %)
[APROBADA] A  Pobreza urbana
              método INEI 24.81 % · residentes habituales 24.74 % (ref. 24.8 %)
[APROBADA] A  Pobreza rural
              método INEI 39.30 % · residentes habituales 39.44 % (ref. 39.3 %)
[APROBADA] A  Pobreza en Lima Metropolitana (dominio 8)
              método INEI 28.21 % · reside
… [recortado: 1,374 caracteres más]
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "    return checks, {\"nacional\": nac, \"hogares_metodo_inei\": hog, \"simple\": simple,\n                    \"miembros_mieperho\": int(hogares.mieperho.sum())}",
 "new_string": "    return checks, {\"nacional\": nac, \"hogares_metodo_inei\": hog, \"simple\": simple,\n                    \"miembros_mieperho\": int(hogares.mieperho.sum()),\n                    \"miembros_p204\": int((miembros.p204 == 1).sum()),\n                    \"ausentes\": int(((miembros.p204 == 1) & (miembros.p205 == 1)).sum()),\n                    \"no_miembros_presentes\": int(((miembros.p204 == 2) & (miembros.p206 == 1)).sum())}"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "               f\"donde cada hogar pesa factor07 × mieperho ({resumen['miembros_mieperho']:,} miembros del hogar: \"\n               \"incluye a los miembros ausentes más de 30 días, p204 == 1 y p205 == 1, que el filtro de residentes \"\n               \"excluye). Por eso las cifras de residentes difieren unas décimas de las oficiales. El método INEI se \"\n               \"usa para validar contra las cifras publicadas y está en indicadores.csv con metodo = inei_hogares.\"]",
 "new_string": "               f\"donde cada hogar pesa factor07 × mieperho (Σ mieperho = {resumen['miembros_mieperho']:,}; en el \"\n               f\"módulo 02 hay {resumen['miembros_p204']:,} personas con p204 == 1, miembros del hogar). Los \"\n               f\"residentes habituales excluyen a {resumen['ausentes']:,} miembros ausentes 30 días o más \"\n               f\"(p204 == 1 y p205 == 1) e incluyen a {resumen['no_miembros_presentes']:,} no miembros presentes 30 \"\n               \"días o más (p204 == 2 y p206 == 1). Por eso sus cifras difieren unas décimas de las oficiales. El \"\n               \"método INEI se usa para validar contra las cifras publicadas y está en indicadores.csv con \"\n               \"metodo = inei_hogares.\"]"
}
```

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py | tail -5",
 "description": "Re-run cleaning to refresh validation note",
 "timeout": 600000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
Pobreza nacional 2024: 27.53 % de las personas (facpob07) · 27.58 % con el método INEI (factor07 × mieperho).

Nota sobre los dos métodos. La base principal son los residentes habituales del módulo 02 (108,664 personas) ponderados con facpob07. El INEI publica la pobreza con la sumaria, donde cada hogar pesa factor07 × mieperho (Σ mieperho = 109,842; en el módulo 02 hay 109,842 personas con p204 == 1, miembros del hogar). Los residentes habituales excluyen a 1,787 miembros ausentes 30 días o más (p204 == 1 y p205 == 1) e incluyen a 609 no miembros presentes 30 días o más (p204 == 2 y p206 == 1). Por eso sus cifras difieren unas décimas de las oficiales. El método INEI se usa para validar contra las cifras publicadas y está en indicadores.csv con metodo = inei_hogares.

OK: salidas/personas_2024.parquet (108,664 personas), salidas/hogares_2024.parquet (33,691 hogares), salidas/indicadores.csv (178 filas), salidas/validacion.txt
```
</details>

### 🤖 Claude · 2026-11-09 11:50

Las 14 validaciones pasan. Ahora escribo `SKILL.md`, `reference.md` y un script de consulta, para que el agente responda cualquier corte ponderado sin escribir código improvisado.

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\estimacion.py",
 "old_string": "def proporcion(df, variable, peso=\"facpob07\", por=None, psu=\"conglome\", estrato=\"estrato\"):\n    \"\"\"% ponderado de `variable` (0/1) en toda la base o por grupos, con EE de diseño e IC 95 %.\"\"\"",
 "new_string": "def media(df, variable, peso=\"facpob07\", por=None, psu=\"conglome\", estrato=\"estrato\"):\n    \"\"\"Media ponderada de una variable continua (p. ej. gasto_pc_mensual), con EE de diseño. Columnas *_pct en\n    las unidades de la variable (escala 1).\"\"\"\n    return proporcion(df, variable, peso, por, psu, estrato, escala=1.0)\n\n\ndef proporcion(df, variable, peso=\"facpob07\", por=None, psu=\"conglome\", estrato=\"estrato\", escala=100.0):\n    \"\"\"% ponderado de `variable` (0/1) en toda la base o por grupos, con EE de diseño e IC 95 %.\"\"\"\n    df = df[df[variable].notna()]"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\estimacion.py",
 "old_string": "        filas.append({\"grupo\": g, \"valor_pct\": 100 * p, \"ee_pct\": 100 * ee,\n                      \"ic95_inf\": 100 * (p - Z95 * ee), \"ic95_sup\": 100 * (p + Z95 * ee),\n                      \"n_muestra\": int(d.sum()), \"poblacion_expandida\": W})",
 "new_string": "        filas.append({\"grupo\": g, \"valor_pct\": escala * p, \"ee_pct\": escala * ee,\n                      \"ic95_inf\": escala * (p - Z95 * ee), \"ic95_sup\": escala * (p + Z95 * ee),\n                      \"n_muestra\": int(d.sum()), \"poblacion_expandida\": W})"
}
```

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\consultar.py",
 "content": "\"\"\"Consulta ponderada sobre la base limpia de la ENAHO: % de pobres (o media de una variable) por grupos y filtros.\n\n    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py                                  # pobreza nacional\n    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por area\n    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por departamento --orden desc\n    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por sexo --filtro \"area == 'Rural'\"\n    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --indicador pobre_extremo --por region_natural\n    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --media gasto_pc_mensual --por area\n    uv run python .claude/skills/limpiando-enaho/scripts/consultar.py --por departamento --metodo inei_hogares\n\nSiempre pondera (facpob07 en personas; factor07 × mieperho en el método INEI) y da el IC 95 % de diseño.\nSi no existe la base limpia, corre antes limpiar.py.\n\"\"\"\nimport argparse\nimport subprocess\nimport sys\nfrom pathlib import Path\n\nimport pandas as pd\n\nsys.path.insert(0, str(Path(__file__).parent))\nfrom estimacion import media, proporcion  # noqa: E402\n\nPROYECTO = Path(__file__).resolve().parents[4]\n\n\ndef cargar(metodo, anio=2024):\n    archivo = PROYECTO / \"salidas\" / f\"{'personas' if metodo == 'personas' else 'hogares'}_{anio}.parquet\"\n    if not archivo.exists():\n        print(f\"No existe {archivo.relative_to(PROYECTO)}: corro limpiar.py primero...\", file=sys.stderr)\n        r = subprocess.run([sys.executable, str(Path(__file__).parent / \"limpiar.py\"), \"--anio\", str(anio)],\n                           capture_output=True, text=True, encoding=\"utf-8\")\n        if r.returncode != 0:\n            sys.exit(f\"ERROR: la limpieza falló; no hay cifras que reportar.\\n{r.stdout[-1500:]}\\n{r.stderr[-800:]}\")\n    return pd.read_parquet(archivo)\n\n\ndef main():\n    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])\n    p.add_argument(\"--indicador\", default=\"pobre\", help=\"variable 0/1: pobre (defecto) o pobre_extremo\")\n    p.add_argument(\"--media\", help=\"en vez de un %, la media ponderada de esta variable (p. ej. gasto_pc_mensual)\")\n    p.add_argument(\"--por\", help=\"columna para agru
… [recortado: 2,110 caracteres más]
```

**🔧 Bash**

```json
{
 "command": "S=.claude/skills/limpiando-enaho/scripts/consultar.py; export PYTHONIOENCODING=utf-8\nuv run python $S; uv run python $S --por sexo --filtro \"area == 'Rural'\"; uv run python $S --media gasto_pc_mensual --por area; uv run python $S --por departamento --orden desc | head -6; uv run python $S --por departamento --metodo inei_hogares --orden desc | head -4; uv run python $S --por grupo_edad; uv run python $S --por sexo_jefe",
 "description": "Try the weighted query script with several cuts",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\estimacion.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\estimacion.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\consultar.py (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
grupo  valor   ee  ic95_inf  ic95_sup  n_muestra  poblacion_expandida
Total  27.53 0.52     26.51     28.55     108664           34147766.0

Indicador: pobre (% de personas) · peso: facpob07 · filtro: ninguno · n = 108,664 personas
Fuente: INEI, ENAHO 2024 (módulos 34 y 02), procesado con .claude/skills/limpiando-enaho
 grupo  valor   ee  ic95_inf  ic95_sup  n_muestra  poblacion_expandida
Hombre  38.82 0.87     37.10     40.53      17813            3175623.0
 Mujer  40.04 0.88     38.32     41.76      18258            3310762.0

Indicador: pobre (% de personas) · peso: facpob07 · filtro: area == 'Rural' · n = 36,071 personas
Fuente: INEI, ENAHO 2024 (módulos 34 y 02), procesado con .claude/skills/limpiando-enaho
 grupo  valor   ee  ic95_inf  ic95_sup  n_muestra  poblacion_expandida
 Rural 454.84 4.54    445.95    463.73      36071            6486385.0
Urbana 863.75 7.90    848.26    879.23      72593           27661381.0

Indicador: gasto_pc_mensual (gasto_pc_mensual) · peso: facpob07 · filtro: ninguno · n = 108,664 personas
Fuente: INEI, ENAHO 2024 (módulos 34 y 02), procesado con .claude/skills/limpiando-enaho
grupo        nombre  valor   ee  ic95_inf  ic95_sup  n_muestra  poblacion_expandida
   06     Cajamarca  44.99 2.29     40.50     49.49       4468            1547849.0
   16        Loreto  42.61 2.32     38.07     47.15       5678            1121012.0
   21          Puno  40.42 2.36     35.79     45.04       3112            1535441.0
   10       H
… [recortado: 1,538 caracteres más]
```
</details>

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\SKILL.md",
 "content": "---\nname: limpiando-enaho\ndescription: Limpia, une y valida los microdatos de la ENAHO 2024 del INEI (módulo 34 sumaria y módulo 02 miembros) y calcula pobreza monetaria ponderada con factores de expansión. Úsala cuando pidan limpiar, preparar o validar la ENAHO, o cuando una pregunta necesite cifras de pobreza, pobreza extrema o gasto de los hogares peruanos (nacional, urbana o rural, por departamento, región, sexo, edad o jefatura del hogar). También es el paso previo de graficando-enaho y mapeando-enaho si no existe salidas/personas_2024.parquet.\nargument-hint: \"[anio=2024]\"\nallowed-tools: Bash(uv run:*), Read, Glob\n---\n\n# Limpiando la ENAHO 2024\n\nConvierte los zip del INEI en una base de personas validada y responde cifras ponderadas. Lo que no se discute\n(llaves, filtro, unión, pesos, validación) está en `scripts/limpiar.py`; no lo reescribas ni lo reemplaces con código\npropio.\n\n## Pasos\n\n1. **¿Ya hay base válida?** Si existen `salidas/personas_2024.parquet` y `salidas/validacion.txt` dice\n   `Resultado: BASE VÁLIDA`, salta al paso 4 (salvo que pidan rehacer la limpieza).\n2. **Limpiar.** Desde la raíz del proyecto corre exactamente:\n\n   ```bash\n   uv run python ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio 2024\n   ```\n\n   Descarga `966-Modulo34.zip` y `966-Modulo02.zip` a `datos/inei/` si faltan (966 = ENAHO 2024 en el portal del INEI).\n3. **Leer la validación.** Abre `salidas/validacion.txt`. Si el script termina con error o dice `BASE RECHAZADA`,\n   **detente**: informa qué validación falló y no reportes cifras. Nunca ajustes datos ni pesos para que coincidan con\n   las referencias.\n4. **Responder con cifras ponderadas.** Para cualquier corte usa el script de consulta (nunca un promedio simple):\n\n   ```bash\n   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --por area\n   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --por departamento --orden desc\n   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --por sexo --filtro \"area == 'Rural'\"\n   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --indicador pobre_extremo\n   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --media gasto_pc_mensual --por region_natural\n   ```\n\n   Las tablas ya calculadas están en `salidas/indicadores.csv` (columna `metodo`).\n5. **Citar.** Cada cifra va con un decim
… [recortado: 1,101 caracteres más]
```

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\reference.md",
 "content": "# Referencia: ENAHO 2024 para la skill limpiando-enaho\n\n## Archivos del INEI\n\n| Zip (código 966 = 2024) | Archivo .dta | Una fila por | Filas | Llaves | Factor |\n|---|---|---|---|---|---|\n| [966-Modulo34.zip](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip) | `sumaria-2024.dta` | hogar | 33,691 | `conglome`, `vivienda`, `hogar` | `factor07` |\n| [966-Modulo02.zip](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip) | `enaho01-2024-200.dta` | persona | 117,721 | las tres + `codperso` | `facpob07` |\n\nEl zip 34 también trae `sumaria-2024-12g.dta` (gasto en 12 grupos): no se usa.\n\n## Reglas del pipeline (scripts/limpiar.py)\n\n1. `pd.read_stata(..., convert_categoricals=False)`: códigos numéricos, no etiquetas.\n2. Llaves como texto: `conglome` (6 caracteres), `vivienda` (3), `hogar` (2), `codperso` (2), `ubigeo` (6). Si se leen\n   como número se pierden los ceros iniciales y la unión falla en silencio.\n3. Nombres en minúscula y sin tildes: `aÑo` pasa a `anio`.\n4. Residentes habituales: `((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))` → 108,664 personas.\n5. `personas.merge(sumaria, on=[\"conglome\",\"vivienda\",\"hogar\"], how=\"left\", validate=\"m:1\", indicator=True)`:\n   cada persona encuentra exactamente un hogar; se verifica que no se dupliquen ni pierdan filas.\n6. Variables construidas: ver tabla de abajo.\n7. Validaciones esenciales (si una falla, el script termina con código 1 y borra el parquet): llaves únicas, ceros\n   iniciales, 108,664 residentes, unión sin duplicados, 25 departamentos, pesos válidos, pobreza nacional a ±0.1 pp de\n   27.6 % con los dos métodos.\n\n## Variables de la base limpia (`salidas/personas_2024.parquet`)\n\n| Variable | Origen | Valores |\n|---|---|---|\n| `departamento` | `ubigeo[:2]` | `01` Amazonas … `07` Callao … `15` Lima … `25` Ucayali (25 códigos) |\n| `nombre_departamento` | diccionario del script | con tildes |\n| `area` | `estrato <= 5` | `Urbana` (estratos 1–5) / `Rural` (6–8) |\n| `dominio`, `nombre_dominio` | `dominio` | 1 Costa Norte, 2 Costa Centro, 3 Costa Sur, 4 Sierra Norte, 5 Sierra Centro, 6 Sierra Sur, 7 Selva, 8 Lima Metropolitana |\n| `region_natural` | `dominio` | Costa (1–3), Sierra (4–6), Selva (7), Lima Metropolitana (8) |\n| `pobreza` | sumaria | 1 pobre extremo, 2 pobre n
… [recortado: 2,021 caracteres más]
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\SKILL.md (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\reference.md (file state is current in your context — no need to Read it back)
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
Plan updated: step 4 of 7 is in progress. App actions available now: commit, create_pr.
```
</details>

**🔧 Skill**

```json
{
 "skill": "dataviz"
}
```

<details><summary>resultado</summary>

```text
Launching skill: dataviz
```
</details>

**🔧 Bash**

```json
{
 "command": "D=\"C:/Users/<usuario>/AppData/Local/Temp/claude/bundled-skills/2.1.317/15215c8148a492e379cb23c3a2ff5aa3/dataviz\"; sed -n 1,200p \"$D/references/palette.md\" | head -150",
 "description": "Read the dataviz reference palette"
}
```

<details><summary>resultado</summary>

```text
# Reference palette

This is the **reference instance** of the data-viz method: every parameter the
method needs, filled in with a validated default palette. The rest of the skill
is system-agnostic - **to target your brand, substitute this file's values** and
re-run the validator. Nothing else changes.

## How to use these values

Everything below is plain hex. In an HTML chart, **define the slots you use as
CSS custom properties in a local `<style>` block** at the top of the file, then
reference them by role throughout - so the light/dark values swap in one place,
and the chart body is written against roles rather than raw hex:

```css
.viz-root {
  color-scheme: light;
  --surface-1:      #fcfcfb;   /* chart surface */
  --text-primary:   #0b0b0b;
  --text-secondary: #52514e;
  --series-1:       #2a78d6;   /* categorical slot 1 */
  /* ...only the roles this chart uses */
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --text-primary:   #f0efec;
    --text-secondary: #c3c2b7;
    --series-1:       #3987e5;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --surface-1:      #1a1a19;
  --text-primary:   #f0efec;
  --text-secondary: #c3c2b7;
  --series-1:       #3987e5;
}
```

Declare the dark values under both scopes as above - the media query covers
the OS setting; the `data-theme` scope covers the viewer's theme toggle,
which must win both ways (the `:n
… [recortado: 5,832 caracteres más]
```
</details>

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python -c \"\nimport geopandas as gpd\ng = gpd.read_file('datos/geo/peru_departamental_simple.geojson')\nprint(g.shape, g.crs); print(g.drop(columns='geometry').head(3)); print(g.dtypes); print(sorted(g.FIRST_IDDP)[:5], g.FIRST_IDDP.nunique())\n\"",
 "description": "Inspect the departmental GeoJSON fields"
}
```

<details><summary>resultado</summary>

```text
(25, 5) EPSG:4326
    NOMBDEP  COUNT FIRST_IDDP     HECTARES
0  AMAZONAS     84         01  3930646.567
1    ANCASH    166         02  3596224.600
2  APURIMAC     80         03  2111415.170
NOMBDEP            str
COUNT            int32
FIRST_IDDP         str
HECTARES       float64
geometry      geometry
dtype: object
['01', '02', '03', '04', '05'] 25
```
</details>

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "content": "\"\"\"Gráficos de pobreza monetaria con la ENAHO 2024, siempre ponderados y con IC 95 %, título analítico y fuente.\n\n    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por area\n    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por sexo\n    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por departamento\n    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por grupo_edad --dividir area\n    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por sexo --filtro \"area == 'Rural'\"\n    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --indicador pobre_extremo --por region_natural\n    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --todos      # área, sexo, departamento y edad\n\nCada gráfico se guarda en figuras/<nombre>.png (200 dpi) junto con figuras/<nombre>.csv, la tabla exacta que se graficó.\nSi no existe la base limpia, corre antes la skill limpiando-enaho (scripts/limpiar.py).\n\"\"\"\nimport argparse\nimport re\nimport subprocess\nimport sys\nfrom pathlib import Path\n\nimport matplotlib\n\nmatplotlib.use(\"Agg\")\nimport matplotlib.pyplot as plt  # noqa: E402\nimport pandas as pd  # noqa: E402\n\nPROYECTO = Path(__file__).resolve().parents[4]\nLIMPIEZA = PROYECTO / \".claude\" / \"skills\" / \"limpiando-enaho\" / \"scripts\"\nsys.path.insert(0, str(LIMPIEZA))\nfrom estimacion import proporcion  # noqa: E402\n\nFIGURAS = PROYECTO / \"figuras\"\nAZUL, NARANJA, GRIS, TINTA, TINTA2, FONDO = \"#2a78d6\", \"#eb6834\", \"#8a8984\", \"#0b0b0b\", \"#52514e\", \"#fcfcfb\"\nORDEN = {\"grupo_edad\": [\"0-14\", \"15-29\", \"30-44\", \"45-64\", \"65 y más\"], \"area\": [\"Urbana\", \"Rural\"],\n         \"region_natural\": [\"Lima Metropolitana\", \"Costa\", \"Sierra\", \"Selva\"]}\nETIQUETA = {\"area\": \"área de residencia\", \"sexo\": \"sexo\", \"grupo_edad\": \"grupo de edad\",\n            \"sexo_jefe\": \"sexo del jefe de hogar\", \"region_natural\": \"región natural\", \"nombre_dominio\": \"dominio\",\n            \"departamento\": \"departamento\"}\nINDICADOR = {\"pobre\": \"Pobreza monetaria\", \"pobre_extremo\": \"Pobreza monetaria extrema\"}\n\n\ndef cargar_base(anio=2024):\n    archivo = PROYECTO / \"salidas\" / f\"personas_{anio}.parquet\"\n    if not archivo.exi
… [recortado: 7,869 caracteres más]
```

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python .claude/skills/graficando-enaho/scripts/graficar.py --todos 2>&1 | grep -v \"^ \" | head; ls figuras",
 "description": "Generate the four basic ENAHO charts",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
Guardado figuras\pobreza_area.png (+ .csv). Título: La pobreza rural (39.4 %) supera en 14.7 puntos a la urbana (24.7 %)
serie  grupo  valor_pct  ic95_inf  ic95_sup  n_muestra
Total  Rural      39.44     37.78     41.10      36071
Total Urbana      24.74     23.53     25.94      72593
Guardado figuras\pobreza_sexo.png (+ .csv). Título: Sin diferencia concluyente en la pobreza entre mujer (27.7 %) y hombre (27.4 %)
serie  grupo  valor_pct  ic95_inf  ic95_sup  n_muestra
Total Hombre      27.37     26.29     28.45      52587
Total  Mujer      27.68     26.63     28.72      56077
Guardado figuras\pobreza_departamento.png (+ .csv). Título: Cajamarca tiene la mayor pobreza (45.0 %), 7.6 veces la de Ica (5.9 %)
serie         grupo  valor_pct  ic95_inf  ic95_sup  n_muestra
pobreza_area.csv
pobreza_area.png
pobreza_departamento.csv
pobreza_departamento.png
pobreza_grupo_edad_area.csv
pobreza_grupo_edad_area.png
pobreza_sexo.csv
pobreza_sexo.png
```
</details>

### 🤖 Claude · 2026-11-09 11:52

Avance: la Skill de limpieza ya está lista y validada, y la de gráficos produce sus primeras cuatro figuras. Las reviso visualmente.

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\figuras\\pobreza_departamento.png"
}
```

<details><summary>resultado</summary>

```text
[imagen]
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\figuras\\pobreza_grupo_edad_area.png"
}
```

<details><summary>resultado</summary>

```text
[imagen]
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "old_string": "def titulo_automatico(t, indicador, por):\n    \"\"\"Un título que dice el hallazgo, calculado con los mismos números del gráfico.\"\"\"\n    nombre = INDICADOR[indicador].lower().replace(\"pobreza monetaria\", \"pobreza\")\n    t = t[t.serie == t.serie.iloc[0]].sort_values(\"valor_pct\", ascending=False)\n    alto, bajo = t.iloc[0], t.iloc[-1]\n    se_cruzan = alto.ic95_inf <= bajo.ic95_sup\n    if len(t) == 2:\n        if se_cruzan:\n            return (f\"Sin diferencia concluyente en la {nombre} entre {alto.grupo.lower()} ({alto.valor_pct:.1f} %) \"\n                    f\"y {bajo.grupo.lower()} ({bajo.valor_pct:.1f} %)\")\n        return (f\"La {nombre} {articulo(alto.grupo)} ({alto.valor_pct:.1f} %) supera en \"\n                f\"{alto.valor_pct - bajo.valor_pct:.1f} puntos a la {articulo(bajo.grupo, True)} ({bajo.valor_pct:.1f} %)\")\n    veces = alto.valor_pct / bajo.valor_pct if bajo.valor_pct else float(\"nan\")\n    return (f\"{alto.grupo} tiene la mayor {nombre} ({alto.valor_pct:.1f} %), {veces:.1f} veces la de \"\n            f\"{bajo.grupo} ({bajo.valor_pct:.1f} %)\")\n\n\ndef articulo(grupo, sin_prefijo=False):\n    g = str(grupo).lower()\n    if g in (\"urbana\", \"rural\"):\n        return g if sin_prefijo else g\n    return f\"de {g}\" if not sin_prefijo else f\"de {g}\"",
 "new_string": "FRASE = {\"Hombre\": \"los hombres\", \"Mujer\": \"las mujeres\", \"Urbana\": \"el área urbana\", \"Rural\": \"el área rural\",\n         \"Jefe hombre\": \"los hogares con jefe hombre\", \"Jefa mujer\": \"los hogares con jefa mujer\"}\n\n\ndef frase(grupo, por):\n    if grupo in FRASE:\n        return FRASE[grupo]\n    if por == \"grupo_edad\":\n        return f\"el grupo de {grupo} años\".replace(\"de 65 y más años\", \"de 65 años y más\")\n    return str(grupo)\n\n\ndef titulo_automatico(t, indicador, por):\n    \"\"\"Un título que dice el hallazgo, calculado con los mismos números del gráfico.\"\"\"\n    nombre = INDICADOR[indicador].lower().replace(\"pobreza monetaria\", \"pobreza\")\n    series = list(dict.fromkeys(t.serie))\n    if len(series) == 2:   # barras agrupadas: ¿una serie supera a la otra en todos los grupos?\n        a = t[t.serie == series[0]].set_index(\"grupo\")\n        b = t[t.serie == series[1]].set_index(\"grupo\")\n        dif = (b.valor_pct - a.valor
… [recortado: 1,441 caracteres más]
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "old_string": "    alto_fig = max(3.2, 0.36 * len(grupos) * len(series) + 1.9)\n    fig, ax = plt.subplots(figsize=(9, alto_fig), facecolor=FONDO)\n    ax.set_facecolor(FONDO)\n    colores = [AZUL, NARANJA]\n    ancho = 0.8 / len(series)\n    for i, (s, color) in enumerate(zip(series, colores)):\n        d = t[t.serie == s].set_index(\"grupo\").reindex(grupos)\n        y = [k + (i - (len(series) - 1) / 2) * ancho for k in range(len(grupos))]\n        ax.barh(y, d.valor_pct, height=ancho * 0.9, color=color, label=None if s == \"Total\" else s, zorder=2)\n        ax.errorbar(d.valor_pct, y, xerr=[d.valor_pct - d.ic95_inf, d.ic95_sup - d.valor_pct], fmt=\"none\",\n                    ecolor=GRIS, elinewidth=1, capsize=2, zorder=3)\n        for yy, v, sup in zip(y, d.valor_pct, d.ic95_sup):\n            ax.text(sup + 0.6, yy, f\"{v:.1f} %\", va=\"center\", ha=\"left\", fontsize=8.5, color=TINTA)",
 "new_string": "    lineas_titulo = textwrap.wrap(titulo, 88)\n    cabecera = 0.32 + 0.24 * len(lineas_titulo) + 0.3    # pulgadas para título y subtítulo\n    alto_fig = max(3.2, 0.34 * len(grupos) * len(series) + 1.2) + cabecera\n    fig, ax = plt.subplots(figsize=(9, alto_fig), facecolor=FONDO)\n    ax.set_facecolor(FONDO)\n    colores = [AZUL, NARANJA]\n    ancho = 0.8 / len(series)\n    for i, (s, color) in enumerate(zip(series, colores)):\n        d = t[t.serie == s].set_index(\"grupo\").reindex(grupos)\n        y = [k - (i - (len(series) - 1) / 2) * ancho for k in range(len(grupos))]   # la 1.ª serie arriba\n        ax.barh(y, d.valor_pct, height=ancho * 0.9, color=color, label=None if s == \"Total\" else s, zorder=2)\n        ax.errorbar(d.valor_pct, y, xerr=[d.valor_pct - d.ic95_inf, d.ic95_sup - d.valor_pct], fmt=\"none\",\n                    ecolor=GRIS, elinewidth=1, capsize=2, zorder=3)\n        for yy, v, sup in zip(y, d.valor_pct, d.ic95_sup):\n            ax.text(sup + 0.6, yy, f\"{v:.1f} %\", va=\"center\", ha=\"left\", fontsize=8.5, color=TINTA, zorder=4,\n                    bbox={\"facecolor\": FONDO, \"edgecolor\": \"none\", \"pad\": 0.5})"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "old_string": "    fig.suptitle(titulo, x=0.01, ha=\"left\", fontsize=11.5, fontweight=\"bold\", color=TINTA, wrap=True)\n    sub = (f\"{INDICADOR[indicador]} según {ETIQUETA.get(por, por)}\"\n           + (f\" y {ETIQUETA.get(dividir, dividir)}\" if dividir else \"\")\n           + f\", Perú 2024 (% de personas; barras grises: IC 95 %)\" + (f\". Filtro: {filtro}\" if filtro else \"\"))\n    ax.set_title(sub, loc=\"left\", fontsize=9, color=TINTA2, pad=8)\n    fig.text(0.01, 0.01, \"Fuente: INEI, ENAHO 2024 (módulos 34 y 02). Residentes habituales ponderados con facpob07; \"\n             \"IC de diseño (conglome dentro de estrato). Elaboración: skill graficando-enaho.\",\n             fontsize=7, color=TINTA2)\n    fig.tight_layout(rect=(0, 0.035, 1, 0.95))",
 "new_string": "    sub = (f\"{INDICADOR[indicador]} según {ETIQUETA.get(por, por)}\"\n           + (f\" y {ETIQUETA.get(dividir, dividir)}\" if dividir else \"\")\n           + f\", Perú 2024 (% de personas; líneas grises: IC 95 %)\" + (f\". Filtro: {filtro}\" if filtro else \"\"))\n    pulg = 1 / alto_fig   # una pulgada en coordenadas de figura\n    fig.text(0.015, 1 - 0.22 * pulg, \"\\n\".join(lineas_titulo), ha=\"left\", va=\"top\", fontsize=11.5,\n             fontweight=\"bold\", color=TINTA, linespacing=1.25)\n    fig.text(0.015, 1 - (0.3 + 0.24 * len(lineas_titulo)) * pulg, sub, ha=\"left\", va=\"top\", fontsize=9,\n             color=TINTA2)\n    fig.text(0.015, 0.12 * pulg, \"Fuente: INEI, ENAHO 2024 (módulos 34 y 02). Residentes habituales ponderados con \"\n             \"facpob07; IC de diseño (conglome dentro de estrato). Elaboración: skill graficando-enaho.\",\n             fontsize=7, color=TINTA2)\n    fig.tight_layout(rect=(0, 0.35 * pulg, 1, 1 - cabecera * pulg))"
}
```

**🔧 Bash**

```json
{
 "command": "sed -i 's/^import argparse$/import argparse\\nimport textwrap/' .claude/skills/graficando-enaho/scripts/graficar.py && PYTHONIOENCODING=utf-8 uv run python .claude/skills/graficando-enaho/scripts/graficar.py --todos 2>&1 | grep \"Guardado\"",
 "description": "Regenerate charts with fixed layout and titles",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
Guardado figuras\pobreza_area.png (+ .csv). Título: La pobreza en el área rural (39.4 %) supera en 14.7 puntos a la de el área urbana (24.7 %)
Guardado figuras\pobreza_sexo.png (+ .csv). Título: Sin diferencia concluyente en la pobreza entre las mujeres (27.7 %) y los hombres (27.4 %)
Guardado figuras\pobreza_departamento.png (+ .csv). Título: Cajamarca tiene la mayor pobreza (45.0 %), 7.6 veces la de Ica (5.9 %)
Guardado figuras\pobreza_grupo_edad_area.png (+ .csv). Título: La pobreza en el área rural supera a la de el área urbana en todos los grupos; la brecha mayor está en el grupo de 65 años y más (35.2 % frente a 19.1 %)
[This command modified 1 file you've previously read: .claude\skills\graficando-enaho\scripts\graficar.py. Call Read before editing.]
```
</details>

**🔧 Bash**

```json
{
 "command": "F=.claude/skills/graficando-enaho/scripts/graficar.py && sed -i 's/    titulo = titulo or titulo_automatico(t, indicador, por)/    titulo = titulo or re.sub(r\"\\\\bde el\\\\b\", \"del\", titulo_automatico(t, indicador, por))/' $F && grep -n \"titulo = titulo or\" $F && PYTHONIOENCODING=utf-8 uv run python $F --todos 2>&1 | grep \"Guardado\"",
 "description": "Fix 'de el' contraction in titles and regenerate",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
175:    titulo = titulo or re.sub(r"bde elb", "del", titulo_automatico(t, indicador, por))
Guardado figuras\pobreza_area.png (+ .csv). Título: La pobreza en el área rural (39.4 %) supera en 14.7 puntos a la de el área urbana (24.7 %)
Guardado figuras\pobreza_sexo.png (+ .csv). Título: Sin diferencia concluyente en la pobreza entre las mujeres (27.7 %) y los hombres (27.4 %)
Guardado figuras\pobreza_departamento.png (+ .csv). Título: Cajamarca tiene la mayor pobreza (45.0 %), 7.6 veces la de Ica (5.9 %)
Guardado figuras\pobreza_grupo_edad_area.png (+ .csv). Título: La pobreza en el área rural supera a la de el área urbana en todos los grupos; la brecha mayor está en el grupo de 65 años y más (35.2 % frente a 19.1 %)
[This command modified 1 file you've previously read: .claude\skills\graficando-enaho\scripts\graficar.py. Call Read before editing.]
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "offset": 170,
 "limit": 10
}
```

<details><summary>resultado</summary>

```text
170	    sub = df.query(filtro) if filtro else df
171	    if sub.empty:
172	        sys.exit(f"ERROR: el filtro {filtro!r} no deja observaciones.")
173	    t = estimar(sub, indicador, por, dividir)
174	    nacional = proporcion(sub, indicador).valor_pct.iloc[0]
175	    titulo = titulo or re.sub(r"bde elb", "del", titulo_automatico(t, indicador, por))
176	    archivo = archivo or "_".join(x for x in [indicador.replace("pobre", "pobreza"), por, dividir,
177	                                                re.sub(r"\W+", "_", filtro or "").strip("_").lower()] if x)
178	    png = graficar(t, indicador, por, dividir, filtro, titulo, nacional, archivo)
179	    print(f"Guardado {png.relative_to(PROYECTO)} (+ .csv). Título: {titulo}")
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "old_string": "    titulo = titulo or re.sub(r\"bde elb\", \"del\", titulo_automatico(t, indicador, por))",
 "new_string": "    titulo = titulo or re.sub(r\"\\bde el\\b\", \"del\", titulo_automatico(t, indicador, por))"
}
```

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python .claude/skills/graficando-enaho/scripts/graficar.py --todos 2>&1 | grep \"Guardado\"",
 "description": "Regenerate charts after title fix",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py has been updated successfully.
```
</details>

<details><summary>resultado</summary>

```text
Guardado figuras\pobreza_area.png (+ .csv). Título: La pobreza en el área rural (39.4 %) supera en 14.7 puntos a la del área urbana (24.7 %)
Guardado figuras\pobreza_sexo.png (+ .csv). Título: Sin diferencia concluyente en la pobreza entre las mujeres (27.7 %) y los hombres (27.4 %)
Guardado figuras\pobreza_departamento.png (+ .csv). Título: Cajamarca tiene la mayor pobreza (45.0 %), 7.6 veces la de Ica (5.9 %)
Guardado figuras\pobreza_grupo_edad_area.png (+ .csv). Título: La pobreza en el área rural supera a la del área urbana en todos los grupos; la brecha mayor está en el grupo de 65 años y más (35.2 % frente a 19.1 %)
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\figuras\\pobreza_grupo_edad_area.png"
}
```

<details><summary>resultado</summary>

```text
[imagen]
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\figuras\\pobreza_sexo.png"
}
```

<details><summary>resultado</summary>

```text
[imagen]
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "old_string": "    lineas_titulo = textwrap.wrap(titulo, 88)",
 "new_string": "    lineas_titulo = textwrap.wrap(titulo.replace(\" %\", \" %\"), 88)   # «27.4 %» no se parte"
}
```

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python .claude/skills/graficando-enaho/scripts/graficar.py --todos 2>&1 | grep -c \"Guardado\"",
 "description": "Regenerate charts with non-breaking percent",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py has been updated successfully.
```
</details>

<details><summary>resultado</summary>

```text
4
```
</details>

### 🤖 Claude · 2026-11-09 11:54

Avance: los cuatro gráficos de ENAHO ya están bien. Ahora escribo la Skill del mapa coroplético, que une por código y se compara con la referencia de la sesión 16.

**🔧 Bash**

```json
{
 "command": "mkdir -p .claude/skills/mapeando-enaho/referencias && mv datos/ref_s16.csv .claude/skills/mapeando-enaho/referencias/pobreza_departamento_2024.csv && head -3 .claude/skills/mapeando-enaho/referencias/pobreza_departamento_2024.csv",
 "description": "Move session 16 reference CSV into the map skill"
}
```

<details><summary>resultado</summary>

```text
ccdd,departamento,pobreza_pct
01,AMAZONAS,25.7
02,ANCASH,22.8
```
</details>

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\mapeando-enaho\\scripts\\mapear.py",
 "content": "\"\"\"Mapa coroplético de la pobreza monetaria por departamento (ENAHO 2024), unido por código y comparado con la referencia.\n\n    uv run python .claude/skills/mapeando-enaho/scripts/mapear.py                       # residentes habituales, facpob07\n    uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --metodo inei_hogares # método oficial del INEI\n    uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --indicador pobre_extremo\n\nUne ubigeo[:2] (departamento) con FIRST_IDDP del GeoJSON, nunca por nombre. Exige 25 unidades con dato y Lima (15) y\nCallao (07) separados; si no, se detiene. Guarda en mapas/ el PNG, la tabla graficada y la comparación con\nreferencias/pobreza_departamento_2024.csv (Sesión 16).\n\"\"\"\nimport argparse\nimport subprocess\nimport sys\nimport textwrap\nfrom pathlib import Path\n\nimport geopandas as gpd\nimport httpx\nimport matplotlib\n\nmatplotlib.use(\"Agg\")\nimport matplotlib.pyplot as plt  # noqa: E402\nimport pandas as pd  # noqa: E402\nfrom matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402\nfrom matplotlib.patches import Patch  # noqa: E402\n\nSKILL = Path(__file__).resolve().parents[1]\nPROYECTO = Path(__file__).resolve().parents[4]\nLIMPIEZA = PROYECTO / \".claude\" / \"skills\" / \"limpiando-enaho\" / \"scripts\"\nsys.path.insert(0, str(LIMPIEZA))\nfrom estimacion import proporcion  # noqa: E402\n\nGEOJSON = PROYECTO / \"datos\" / \"geo\" / \"peru_departamental_simple.geojson\"\nURL_GEOJSON = (\"https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/\"\n               \"peru_departamental_simple.geojson\")\nREFERENCIA = SKILL / \"referencias\" / \"pobreza_departamento_2024.csv\"\nMAPAS = PROYECTO / \"mapas\"\n# Rampa secuencial de un solo tono (azul), de claro a oscuro, en clases de 10 puntos desde 0\nCORTES = [0, 10, 20, 30, 40, 50]\nCOLORES = [\"#cde2fb\", \"#86b6ef\", \"#3987e5\", \"#1c5cab\", \"#0d366b\"]\nTINTA, TINTA2, FONDO = \"#0b0b0b\", \"#52514e\", \"#fcfcfb\"\nINDICADOR = {\"pobre\": \"pobreza monetaria\", \"pobre_extremo\": \"pobreza monetaria extrema\"}\n\n\nclass ErrorDeUnion(Exception):\n    pass\n\n\ndef cargar(metodo, anio=2024):\n    archivo = PROYECTO / \"salidas\" / f\"{'personas' if metodo == 'personas' else 'hogares'}_{anio}.parquet\"\n    if not archivo.exists(
… [recortado: 8,937 caracteres más]
```

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python .claude/skills/mapeando-enaho/scripts/mapear.py && PYTHONIOENCODING=utf-8 uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --metodo inei_hogares | head -2; ls mapas",
 "description": "Generate the department poverty choropleth maps",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\mapeando-enaho\scripts\mapear.py (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
Mapa: mapas/pobreza_departamento_2024.png · 25/25 unidades con dato · unión por FIRST_IDDP = ubigeo[:2] · Lima (15) y Callao (07) separados
Título: Cajamarca (45.0 %) y Loreto (42.6 %) tienen la mayor pobreza monetaria; Ica (5.9 %), la menor
Traceback (most recent call last):
  File "C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\mapeando-enaho\scripts\mapear.py", line 189, in <module>
    main()
  File "C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\mapeando-enaho\scripts\mapear.py", line 173, in main
    c = comparar(tablas["personas"][0], tablas["inei_hogares"][0])
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\mapeando-enaho\scripts\mapear.py", line 87, in comparar
    c = ref.merge(tabla_personas[["departamento", "nombre", "valor_pct"]].rename(columns={"valor_pct": "personas"}),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.venv\Lib\site-packages\pandas\core\frame.py", line 16192, in merge
    return merge(
           ^^^^^^
  File "C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.venv\Lib\site-packages\pandas\core\reshape\merge.py", line 391, in merge
    op = _MergeOperation(
         ^^^^^^^^^^^^^^^^
  File "C:\Users\<usuario>\Documents\GitHub\python-intermedi
… [recortado: 721 caracteres más]
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\mapeando-enaho\\scripts\\mapear.py",
 "old_string": "    ref = pd.read_csv(REFERENCIA, dtype={\"ccdd\": str}).rename(columns={\"ccdd\": \"departamento\",\n                                                                       \"pobreza_pct\": \"referencia_s16\"})",
 "new_string": "    ref = pd.read_csv(REFERENCIA, dtype={\"ccdd\": str}).rename(columns={\"departamento\": \"nombre_ref\"})\n    ref = ref.rename(columns={\"ccdd\": \"departamento\", \"pobreza_pct\": \"referencia_s16\"})"
}
```

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --metodo inei_hogares | head -2 && PYTHONIOENCODING=utf-8 uv run python .claude/skills/mapeando-enaho/scripts/mapear.py; ls mapas",
 "description": "Re-run maps and reference comparison",
 "timeout": 300000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\mapeando-enaho\scripts\mapear.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
Mapa: mapas/pobreza_departamento_2024_inei.png · 25/25 unidades con dato · unión por FIRST_IDDP = ubigeo[:2] · Lima (15) y Callao (07) separados
Título: Cajamarca (45.0 %) y Loreto (43.0 %) tienen la mayor pobreza monetaria; Ica (6.0 %), la menor
Mapa: mapas/pobreza_departamento_2024.png · 25/25 unidades con dato · unión por FIRST_IDDP = ubigeo[:2] · Lima (15) y Callao (07) separados
Título: Cajamarca (45.0 %) y Loreto (42.6 %) tienen la mayor pobreza monetaria; Ica (5.9 %), la menor
Comparación con referencias/pobreza_departamento_2024.csv (Sesión 16), redondeado a 1 decimal:
  método INEI (factor07 × mieperho): 25/25 iguales, máx. |dif| = 0.0 pp
  residentes habituales (facpob07): 6/25 iguales, máx. |dif| = 0.5 pp (Amazonas, Huánuco, Loreto, Pasco, Puno, Tumbes con |dif| ≥ 0.3), correlación de rangos = 0.999
  La diferencia viene de la población: residentes habituales frente a miembros del hogar (mieperho). Ver salidas/validacion.txt.
comparacion_referencia.csv
comparacion_referencia.txt
pobreza_departamento_2024.csv
pobreza_departamento_2024.png
pobreza_departamento_2024_inei.csv
pobreza_departamento_2024_inei.png
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\mapas\\pobreza_departamento_2024.png"
}
```

<details><summary>resultado</summary>

```text
[imagen]
```
</details>

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\SKILL.md",
 "content": "---\nname: graficando-enaho\ndescription: Hace gráficos de barras de la pobreza monetaria del Perú con la ENAHO 2024 del INEI, siempre ponderados con factores de expansión y con intervalos de confianza, título analítico, unidades y fuente. Úsala cuando pidan graficar, visualizar o comparar en un gráfico la pobreza (o pobreza extrema) por área urbana y rural, sexo, edad, jefatura del hogar, región natural, dominio o departamento.\nargument-hint: \"[por: area|sexo|grupo_edad|sexo_jefe|region_natural|nombre_dominio|departamento]\"\nallowed-tools: Bash(uv run:*), Read, Glob\n---\n\n# Graficando la ENAHO 2024\n\n## Antes de graficar\n\nSi no existe `salidas/personas_2024.parquet`, usa primero la skill **limpiando-enaho** (o deja que el script la\nejecute: si no encuentra la base corre `limpiar.py` y se detiene si la validación falla). Nunca grafiques con una base\nque no pasó `salidas/validacion.txt`.\n\n## Traducir el pedido a argumentos\n\n| Pedido en lenguaje natural | Comando |\n|---|---|\n| «pobreza urbana y rural», «por área» | `--por area` |\n| «por sexo», «hombres y mujeres» | `--por sexo` |\n| «por departamento», «regiones», «comparar departamentos» | `--por departamento` |\n| «por edad», «niños y adultos mayores» | `--por grupo_edad` |\n| «según el sexo del jefe de hogar» | `--por sexo_jefe` |\n| «costa, sierra y selva» | `--por region_natural` |\n| «por edad y área», «sexo dentro de cada área» | `--por grupo_edad --dividir area` |\n| «solo en zonas rurales» | `--filtro \"area == 'Rural'\"` |\n| «pobreza extrema» | `--indicador pobre_extremo` |\n| «los gráficos básicos» | `--todos` (área, sexo, departamento, edad × área) |\n\nCorre desde la raíz del proyecto:\n\n```bash\nuv run python ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por area\n```\n\nSi el usuario da un título, pásalo con `--titulo \"...\"`; si no, el script escribe uno con el hallazgo principal\ncalculado con los mismos números (y dice «sin diferencia concluyente» cuando los IC 95 % se superponen).\n\n## Qué produce\n\n- `figuras/<nombre>.png` a 200 dpi y `figuras/<nombre>.csv` con la tabla exacta graficada (valor, IC 95 %, n).\n- Barras horizontales desde cero, un solo color (dos si hay `--dividir`), valor escrito en cada barra, IC 95 % en gris,\n  línea punteada con el promedio nacional, subtítulo con indicador, período y unidad (% de personas), y not
… [recortado: 296 caracteres más]
```

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\mapeando-enaho\\SKILL.md",
 "content": "---\nname: mapeando-enaho\ndescription: Construye el mapa coroplético de la pobreza monetaria por departamento del Perú con la ENAHO 2024 del INEI (25 departamentos, Lima y Callao separados), uniendo por código ubigeo y no por nombre, y lo compara con la referencia del curso. Úsala cuando pidan un mapa, mapear o ver la distribución territorial o geográfica de la pobreza por departamento o región.\nargument-hint: \"[--metodo personas|inei_hogares] [--indicador pobre|pobre_extremo]\"\nallowed-tools: Bash(uv run:*), Read, Glob\n---\n\n# Mapeando la ENAHO 2024\n\n## Antes de mapear\n\nSi no existe `salidas/personas_2024.parquet`, usa primero la skill **limpiando-enaho**. El script también lo hace\nsolo: si falta la base, corre `limpiar.py` y se detiene si la validación falla.\n\n## Correr\n\nDesde la raíz del proyecto:\n\n```bash\nuv run python ${CLAUDE_SKILL_DIR}/scripts/mapear.py                          # residentes habituales (facpob07)\nuv run python ${CLAUDE_SKILL_DIR}/scripts/mapear.py --metodo inei_hogares    # cifras oficiales del INEI\nuv run python ${CLAUDE_SKILL_DIR}/scripts/mapear.py --indicador pobre_extremo\n```\n\nBaja el GeoJSON del curso a `datos/geo/` si falta.\n\n## Reglas que el script garantiza (no las rehagas a mano)\n\n- Une `ubigeo[:2]` con `FIRST_IDDP` como texto de dos dígitos, `validate=\"1:1\"`. Nunca por nombre: «APURIMAC» no es\n  «Apurímac».\n- Exige 25 unidades con dato y Lima (15) y Callao (07) separados; si no, termina con error y no dibuja nada.\n- Escala secuencial de un solo tono (azul claro a oscuro) en clases de 10 puntos desde 0; leyenda con la unidad\n  («% de personas en pobreza monetaria») y el número de departamentos por clase. Nunca arcoíris.\n- Compara con `referencias/pobreza_departamento_2024.csv` (Sesión 16) y escribe `mapas/comparacion_referencia.csv`\n  y `.txt`.\n\n## Qué produce\n\n`mapas/pobreza_departamento_2024.png`, la tabla graficada `mapas/pobreza_departamento_2024.csv` (valor, IC 95 %, n) y\nla comparación con la referencia.\n\n## Al responder\n\nCita la ruta del mapa, los departamentos con mayor y menor pobreza (un decimal, % de personas) y el resultado de la\ncomparación con la referencia: con `inei_hogares` coincide 25/25; con residentes habituales difiere hasta 0.5 pp\npor la definición de población (ver `salidas/validacion.txt`). Describe patrones territorial
… [recortado: 19 caracteres más]
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\SKILL.md (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\mapeando-enaho\SKILL.md (file state is current in your context — no need to Read it back)
```
</details>

### 🤖 Claude · 2026-11-09 11:55

Las tres Skills ya están escritas. Antes de las demostraciones con Claude Code, verifico que las 8 pruebas originales no cambiaron y registro un commit con el avance.

**🔧 Bash**

```json
{
 "command": "diff <(head -71 mcp/test_server.py) /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/ref04/test_server.py && echo \"ORIGINALES IDENTICAS\" ; cd .. && git status --short | head -40 && git check-ignore -v tarea_4/datos/inei/966-Modulo34.zip tarea_4/salidas/personas_2024.parquet tarea_4/.venv",
 "description": "Verify original tests unchanged and check git status"
}
```

<details><summary>resultado</summary>

```text
ORIGINALES IDENTICAS
?? .claude/
?? tarea_4/
tarea_4/.gitignore:7:datos/	tarea_4/datos/inei/966-Modulo34.zip
tarea_4/.gitignore:8:salidas/*.parquet	tarea_4/salidas/personas_2024.parquet
tarea_4/.gitignore:2:.venv/	tarea_4/.venv
```
</details>

**🔧 Bash**

```json
{
 "command": "git add tarea_4/pyproject.toml tarea_4/uv.lock tarea_4/.python-version tarea_4/.gitignore tarea_4/.mcp.json tarea_4/mcp tarea_4/scripts && git commit -q -m \"tarea_4: servidor MCP del BCRP (serie, resumen, comparar_periodos, graficar_serie, recurso y prompts) con 10 pruebas\n\nCompleta el esqueleto de la Sesión 04: las 8 pruebas originales sin cambios y 2 nuevas\npara la herramienta propia comparar_periodos. .mcp.json conecta el servidor a Claude Code.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\" && git add tarea_4/.claude/skills tarea_4/salidas/validacion.txt tarea_4/salidas/indicadores.csv tarea_4/figuras tarea_4/mapas && git commit -q -m \"tarea_4: skills limpiando-enaho, graficando-enaho y mapeando-enaho con validación ENAHO 2024\n\nLimpieza con residentes habituales (108,664), unión m:1 y pobreza 27.53 % (facpob07) /\n27.58 % (método INEI); gráficos ponderados con IC 95 %; mapa de 25 departamentos unido\npor ubigeo[:2] = FIRST_IDDP y comparado con la referencia de la Sesión 16.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\" && git log --oneline -3 && git status --short",
 "description": "Commit MCP server and ENAHO skills"
}
```

<details><summary>resultado</summary>

```text
warning: in the working copy of 'tarea_4/.gitignore', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/.mcp.json', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/.python-version', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/mcp/server.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/mcp/test_extras.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/mcp/test_server.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/pyproject.toml', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/scripts/resumir_traza.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/uv.lock', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/.claude/skills/graficando-enaho/SKILL.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/.claude/skills/graficando-enaho/scripts/graficar.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tarea_4/.claude/skills/limpiando-enaho/SKILL.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy o
… [recortado: 1,198 caracteres más]
```
</details>

**🔧 Write**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\scripts\\ejecutar_agente.py",
 "content": "\"\"\"Ejecuta Claude Code en modo no interactivo (claude -p) con una configuración controlada y guarda la traza completa.\n\n    uv run python scripts/ejecutar_agente.py --modo mcp_skills --prompt-file informes/pregunta.md \\\n        --salida evidencias_ia/integracion/ejecucion_integrada\n\nEscribe <salida>.jsonl (stream-json: cada mensaje, llamada a herramienta y resultado) y <salida>.md (resumen legible\ncon las herramientas MCP y las skills que usó). Es la evidencia de que Claude Code coordinó las herramientas.\n\nModos (todos con --strict-mcp-config: ningún otro servidor MCP del usuario entra en juego):\n    base        sin MCP ni skills del proyecto y sin herramientas: solo el conocimiento del modelo\n    skills      skills del proyecto + Bash limitado a `uv run` + lectura de archivos\n    mcp         servidor MCP bcrp, sin herramientas de archivos ni terminal\n    mcp_skills  servidor MCP bcrp + skills + Bash(uv run) + lectura y escritura de archivos\n\"\"\"\nimport argparse\nimport json\nimport subprocess\nimport sys\nimport time\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).parent))\nfrom resumir_traza import a_markdown, leer, resumir  # noqa: E402\n\nPROYECTO = Path(__file__).resolve().parents[1]\nLECTURA = \"Read,Glob,Grep\"\nMODOS = {\n    \"base\": [\"--tools\", \"\", \"--strict-mcp-config\"],\n    \"skills\": [\"--strict-mcp-config\", \"--allowedTools\", f\"Skill,Bash(uv run:*),{LECTURA}\"],\n    \"mcp\": [\"--tools\", \"\", \"--strict-mcp-config\", \"--mcp-config\", \".mcp.json\", \"--allowedTools\", \"mcp__bcrp\"],\n    \"mcp_skills\": [\"--strict-mcp-config\", \"--mcp-config\", \".mcp.json\",\n                   \"--allowedTools\", f\"mcp__bcrp,Skill,Bash(uv run:*),{LECTURA},Write,Edit\"],\n}\n\n\ndef ejecutar(prompt, modo, salida, modelo=\"sonnet\", cwd=PROYECTO, sistema=None, timeout=1800, esquema=None):\n    \"\"\"Corre claude -p y devuelve el resumen de la traza (dict). salida: ruta sin extensión.\"\"\"\n    salida = Path(salida)\n    salida.parent.mkdir(parents=True, exist_ok=True)\n    cmd = [\"claude\", \"-p\", prompt, \"--model\", modelo, \"--output-format\", \"stream-json\", \"--verbose\",\n           \"--no-session-persistence\", *MODOS[modo]]\n    if sistema:\n        cmd += [\"--append-system-prompt\", sistema]\n    if esquema:\n        cmd += [\"--json-schema\", json.dumps(esquema)]\
… [recortado: 2,510 caracteres más]
```

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && export PYTHONIOENCODING=utf-8 && uv run python scripts/ejecutar_agente.py --modo skills --prompt \"/limpiando-enaho 2024\" --salida evidencias_ia/skills/01_invocacion_directa_limpiando 2>&1 | tail -30",
 "description": "Demo: invoke limpiando-enaho skill directly via slash command",
 "timeout": 900000
}
```

<details><summary>resultado</summary>

```text
File created successfully at: C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\scripts\ejecutar_agente.py (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
18.3 s · MCP [] · skills ['limpiando-enaho'] · errores 0 · salida 0
La base ya existe y es válida, así que no repetí la limpieza. Leí `salidas/validacion.txt` y no corrí ningún script.

**Resultado: BASE VÁLIDA.** Pasaron las 14 validaciones, y no falló ninguna.

| Indicador (ENAHO 2024) | Residentes habituales (`facpob07`) | Método INEI (`factor07 × mieperho`) | Referencia |
|---|---|---|---|
| Pobreza nacional | 27.5 % (IC 95 %: 26.5–28.6) | 27.6 % | 27.6 % |
| Pobreza extrema nacional | 5.5 % | — | 5.5 % |
| Pobreza urbana | 24.7 % | 24.8 % | 24.8 % |
| Pobreza rural | 39.4 % | 39.3 % | 39.3 % |
| Lima Metropolitana (dominio 8) | 28.0 % | 28.2 % | 28.2 % |

- **Ponderación:** sin factores de expansión la pobreza nacional saldría 25.6 %, es decir 1.9 puntos porcentuales menos.
- **Diferencia entre métodos:** son pocas décimas. La base de personas tiene 108,664 residentes habituales. Excluye 1,787 miembros ausentes 30 días o más e incluye 609 no miembros presentes 30 días o más. El método INEI usa los 109,842 miembros del hogar de la sumaria.

Todas las cifras tienen la fuente INEI, ENAHO 2024, módulos 34 y 02.

Si quiere, puedo sacar un corte concreto, por ejemplo por departamento o por sexo, o rehacer la limpieza desde los zip.
```
</details>

### 🤖 Claude · 2026-11-09 11:56

Invocación directa: funciona. Ahora la activación por lenguaje natural (gráfico) y la coordinación (mapa sin base procesada).

**🔧 Bash**

```json
{
 "command": "export PYTHONIOENCODING=utf-8 && uv run python scripts/ejecutar_agente.py --modo skills --prompt \"Grafica la pobreza monetaria por sexo del jefe de hogar en el Perú con la ENAHO 2024 y dime si la diferencia es importante.\" --salida evidencias_ia/skills/02_lenguaje_natural_graficando 2>&1 | tail -20; echo; echo \"=========== quitando base procesada\"; rm -f salidas/personas_2024.parquet salidas/hogares_2024.parquet; ls salidas; uv run python scripts/ejecutar_agente.py --modo skills --prompt \"Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.\" --salida evidencias_ia/skills/03_coordinacion_limpieza_y_mapa 2>&1 | tail -25; ls salidas",
 "description": "Demo: natural-language chart request and map with missing base",
 "timeout": 1200000
}
```

<details><summary>resultado</summary>

```text
17.1 s · MCP [] · skills ['graficando-enaho'] · errores 0 · salida 0
Gráfico guardado en `tarea_4/figuras/pobreza_sexo_jefe.png`. La tabla exacta está en `figuras/pobreza_sexo_jefe.csv`.

**Pobreza monetaria por sexo del jefe de hogar, ENAHO 2024 (% de personas, con IC 95 %)**

| Jefatura | Pobreza | IC 95 % | n |
|---|---|---|---|
| Jefe hombre | 28.3 % | 27.1–29.5 | 73 855 |
| Jefa mujer | 26.0 % | 24.5–27.6 | 34 809 |

**¿La diferencia es importante?** Es pequeña y no es concluyente.
- **Tamaño:** los hogares con jefa mujer tienen 2.3 puntos porcentuales menos de pobreza que los de jefe hombre. Eso es una diferencia chica frente a las brechas por área o departamento.
- **Intervalos:** los IC 95 % se superponen (27.1–27.6), así que el gráfico dice «sin diferencia concluyente».
- **Matiz:** superponerse es un criterio conservador. Una prueba aproximada de la diferencia da un error estándar de unos 1.0 punto y un z de unos 2.3. Eso sugiere una diferencia al límite de ser significativa al 5 %. No la calculé con el diseño muestral completo, así que no la daría por establecida.
- **Interpretación:** es una asociación descriptiva. No dice que la jefatura femenina «reduzca» la pobreza. Los hogares con jefa mujer difieren en composición, por ejemplo en tamaño del hogar, en ser unipersonales o en el área de residencia. Esos factores no están controlados aquí.

=========== quitando base procesada
indicadores.csv
validacion.txt
32.4 s · MCP [] · skills ['mapeando-enaho'
… [recortado: 1,482 caracteres más]
```
</details>

**🔧 Bash**

```json
{
 "command": "sed -n '/## Llamadas/,/## Respuesta/p' evidencias_ia/skills/03_coordinacion_limpieza_y_mapa.md",
 "description": "Show tool calls of the map coordination demo"
}
```

<details><summary>resultado</summary>

```text
## Llamadas a herramientas, en orden

| # | Herramienta | Entrada |
|---|---|---|
| 1 | `Skill` | `{"skill": "mapeando-enaho"}` |
| 2 | `Bash` | `{"command": "cd C:/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && uv run python .claude/skills/mapeando-enaho/scripts/mapear.py 2>&1 \| tail -40; cat mapas/comparacion_referencia.txt 2>/dev/null \| head -40"}` |

## Respuesta final
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\mapeando-enaho\\SKILL.md",
 "old_string": "## Antes de mapear\n\nSi no existe `salidas/personas_2024.parquet`, usa primero la skill **limpiando-enaho**. El script también lo hace\nsolo: si falta la base, corre `limpiar.py` y se detiene si la validación falla.",
 "new_string": "## Antes de mapear (obligatorio)\n\n1. Comprueba con Glob si existe `salidas/personas_2024.parquet`.\n2. **Si no existe, invoca primero la skill `limpiando-enaho`** (herramienta Skill) y sigue sus pasos hasta que\n   `salidas/validacion.txt` diga `BASE VÁLIDA`. Si la limpieza falla, detente e informa: no hay mapa sin base válida.\n3. Recién entonces corre el mapa. (Como red de seguridad, `mapear.py` también se niega a dibujar sin base válida.)"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\SKILL.md",
 "old_string": "## Antes de graficar\n\nSi no existe `salidas/personas_2024.parquet`, usa primero la skill **limpiando-enaho** (o deja que el script la\nejecute: si no encuentra la base corre `limpiar.py` y se detiene si la validación falla). Nunca grafiques con una base\nque no pasó `salidas/validacion.txt`.",
 "new_string": "## Antes de graficar (obligatorio)\n\n1. Comprueba con Glob si existe `salidas/personas_2024.parquet`.\n2. **Si no existe, invoca primero la skill `limpiando-enaho`** (herramienta Skill) y sigue sus pasos hasta que\n   `salidas/validacion.txt` diga `BASE VÁLIDA`. Si la limpieza falla, detente e informa.\n3. Recién entonces grafica. Nunca grafiques con una base que no pasó la validación (el script también se niega)."
}
```

**🔧 Bash**

```json
{
 "command": "export PYTHONIOENCODING=utf-8 && rm -f salidas/personas_2024.parquet salidas/hogares_2024.parquet && uv run python scripts/ejecutar_agente.py --modo skills --prompt \"Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.\" --salida evidencias_ia/skills/03_coordinacion_limpieza_y_mapa 2>&1 | head -3; sed -n '/## Llamadas/,/## Respuesta/p' evidencias_ia/skills/03_coordinacion_limpieza_y_mapa.md; ls salidas",
 "description": "Re-run map coordination demo with explicit skill chaining",
 "timeout": 1200000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\mapeando-enaho\SKILL.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\SKILL.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
39.2 s · MCP [] · skills ['mapeando-enaho', 'limpiando-enaho'] · errores 0 · salida 0
Hice el mapa de pobreza monetaria por departamento con la ENAHO 2024: `mapas/pobreza_departamento_2024.png`. La tabla que se graficó está en `mapas/pobreza_departamento_2024.csv` (valor, IC 95 % y n por departamento).

## Llamadas a herramientas, en orden

| # | Herramienta | Entrada |
|---|---|---|
| 1 | `Skill` | `{"skill": "mapeando-enaho"}` |
| 2 | `Glob` | `{"pattern": "salidas/*"}` |
| 3 | `Bash` | `{"command": "cat salidas/validacion.txt \| head -30"}` |
| 4 | `Skill` | `{"skill": "limpiando-enaho"}` |
| 5 | `Bash` | `{"command": "cd C:/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 2>&1 \| tail -30; tail -5 salidas/validacion.txt; ls salidas", "tim` |
| 6 | `Bash` | `{"command": "cd C:/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && uv run python .claude/skills/mapeando-enaho/scripts/mapear.py 2>&1 \| tail -40; cat mapas/pobreza_departamento_2024.csv \| head -30; cat mapas/` |

## Respuesta final
hogares_2024.parquet
indicadores.csv
personas_2024.parquet
validacion.txt
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
Plan updated: step 5 of 7 is in progress. App actions available now: create_pr.
```
</details>

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python - <<'EOF'\nimport zipfile, io, pandas as pd\nwith zipfile.ZipFile(\"datos/inei/966-Modulo34.zip\") as z:\n    b = io.BytesIO(z.read(\"966-Modulo34/sumaria-2024.dta\"))\nr = pd.io.stata.StataReader(b)\nlab = r.variable_labels()\nfor k, v in lab.items():\n    if k.lower().startswith((\"gru1\", \"gashog\", \"g05\", \"ia0\", \"gru\") ) and (\"1\" in k[:5] or \"gashog\" in k):\n        print(k, \"|\", v)\nEOF",
 "description": "List sumaria food-expenditure variable labels",
 "timeout": 200000
}
```

<details><summary>resultado</summary>

```text
ia01hd | ingreso alquiler imputado de la vivienda
gru11hd | grupo 1: alimentos - gasto
gru12hd1 | grupo 1: alimentos - autoconsumo, autosuministro
gru12hd2 | grupo 1: alimentos - pago en especie
gru13hd1 | grupo 1: alimentos - donacion publica
gru13hd2 | grupo 1: alimentos - donacion privada
gru13hd3 | grupo 1: alimentos - otros gastos
gru13hd4 | grupo 1: alimentos consumidos dentro hogar -bienes libres
gru14hd | alimentos preparados consumir en el hogar - pagado
gru14hd1 | alimentos preparados consumir en el hogar - autoconsumo , autosuministro
gru14hd2 | alimentos preparados consumir en el hogar - especie
gru14hd3 | alimentos preparados consumir en el hogar - donado  publico
gru14hd4 | alimentos preparados consumir en el hogar - donado privado
gru14hd5 | alimentos preparados consumir en el hogar - otros
gru14hd6 | grupo 1: alimentos consumidos fuera del hogar -bienes libres
gru21hd | grupo 2: vestido y calzado - gasto
gru31hd | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi
gru41hd | grupo 4: muebles, enseres y mantenimiento de la vivienda - gasto
gru51hd | grupo 5: cuidado, conservacion de la salud y servicios medicos - gasto
gru61hd | grupo 6: transportes y comunicaciones - gasto
gru71hd | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - gasto
gru81hd | grupo 8: otros bienes y servicios - gasto
gashog1d | gasto monetario
gashog2d | gasto total bruto
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad && mkdir -p constvar && cd constvar && unzip -o -q /c/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4/datos/inei/966-Modulo34.zip \"966-Modulo34/ConstVarGasto-Metodologia actualizada.zip\" && unzip -o -q \"966-Modulo34/ConstVarGasto-Metodologia actualizada.zip\" && find . -type f | head; f=$(find . -type f -iname \"*.do\" -o -type f -iname \"*.txt\" -o -type f -iname \"*.sps\" | head -1); echo \"== $f\"; grep -n -i \"gru1\\|alimen\" \"$f\" | head -40",
 "description": "Inspect INEI expenditure-construction methodology file"
}
```

<details><summary>resultado</summary>

```text
./966-Modulo34/ConstVarGasto-Metodologia actualizada.zip
./Gasto2024/00_Instruccion_para_la_construccion_gasto-real.txt
./Gasto2024/01.ConstrVarGastoIngreso2014-2024.do
./Gasto2024/Bases/deflactores_base2024_new.dta
./Gasto2024/Bases/despacial_ldnew.dta
== ./Gasto2024/00_Instruccion_para_la_construccion_gasto-real.txt
Shell cwd was reset to C:\Users\<usuario>\Documents\GitHub\python-intermedio
```
</details>

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/AppData/Local/Temp/claude/bc7051f169b5b1c2/5744c2ba-c365-40c4-a4c4-547ea7d6a5ba/scratchpad/constvar/Gasto2024 && grep -n -i \"gru1\\|gpcrg3\\|alimen\\|sg23\\|sig24\\|sg25\\|sig26\" \"01.ConstrVarGastoIngreso2014-2024.do\" | head -40",
 "description": "Find food-group construction in INEI do-file"
}
```

<details><summary>resultado</summary>

```text
103:gen 		gpcrg3= (gru11hd + gru12hd1 + gru12hd2 + gru13hd1 + gru13hd2 + gru13hd3 )/(p*mieperho*ld*i01) 
105:gen 		gpcrg8= ((sg23 + sig24)/(p*mieperho*ld*i01)) 
106:gen 		gpcrg9= ((gru14hd + gru14hd1 +  gru14hd2 + gru14hd3 + gru14hd4 + gru14hd5 + sg25 + sig26 + sg27 + sig28)/(p*mieperho*ld*i01)) 
115:label var gpcrg3	"Preparados dentro del hogar"
129:gen 	gpgru2= gpcrg3
137:gen		gpgru10 = gpcrg21 
138:gen 	gpgru1 = gpgru2 + gpgru3
139:gen  	gpgru0 = gpgru1 + gpgru4 + gpgru5 + gpgru6 + gpgru7 + gpgru8 + gpgru9 + gpgru10 
141:label var gpgru1 "G01.Total en Alimentos real"
142:label var gpgru2 "G011.Alimentos dentro del hogar real"
143:label var gpgru3 "G012.Alimentos fuera del hogar real"
150:label var gpgru10 "G08.otros gastos en bienes y servicios real"
155:gen   	  	gpcnr1 =(((gru11hd +gru14hd + sg23 + g05hd + g05hd1 + g05hd2 + g05hd3 + g05hd4 + g05hd5 + g05hd6 + sg25 + sg27)/(p*mieperho *  ld*i01))/*
161:gen     	gpcnr2 =(((gru12hd1 + gru14hd1)/(p*mieperho *  ld*i01)) + (gru22hd1/(p*mieperho *  ld*i02)) + /*
166:gen     	gpcnr3 = (((gru12hd2 + gru14hd2)/(p*mieperho *  ld*i01)) + (gru22hd2/(p*mieperho *  ld*i02)) + /*
171:gen    		gpcnr4 =(((gru13hd1 + gru14hd3+ sig24 + sig26 + sig28)/(p*mieperho *  ld*i01)) + (gru23hd1/(p*mieperho *  ld*i02)) + /*
176:gen     	gpcnr5 =(((gru13hd2 + gru14hd4 + ig06hd)/(p*mieperho *  ld*i01)) + (gru23hd2/(p*mieperho *  ld*i02)) + /*
181:gen   		  gpcnr6 =(((gru13hd3 + gru14hd5)/(p*mieperho *  ld*i01)) + (gru23hd3/(p*mieperho *  ld*i02)) + /*

… [recortado: 1,166 caracteres más]
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "EDADES = [(0, 14, \"0-14\"), (15, 29, \"15-29\"), (30, 44, \"30-44\"), (45, 64, \"45-64\"), (65, 200, \"65 y más\")]",
 "new_string": "EDADES = [(0, 14, \"0-14\"), (15, 29, \"15-29\"), (30, 44, \"30-44\"), (45, 64, \"45-64\"), (65, 200, \"65 y más\")]\nCONDICION = {1: \"Pobre extremo\", 2: \"Pobre no extremo\", 3: \"No pobre\"}\n# Gasto anual del hogar en alimentos (grupo 1), como en el do-file oficial del INEI\n# (ConstVarGasto 2024, 01.ConstrVarGastoIngreso2014-2024.do: gpcrg3 + gpcrg8 + gpcrg9, sin deflactar):\n# dentro del hogar (comprado, autoconsumo, especie, donaciones, otros) + fuera del hogar.\nALIMENTOS = [\"gru11hd\", \"gru12hd1\", \"gru12hd2\", \"gru13hd1\", \"gru13hd2\", \"gru13hd3\",          # dentro del hogar\n             \"sg23\", \"sig24\",                                                                # fuera del hogar\n             \"gru14hd\", \"gru14hd1\", \"gru14hd2\", \"gru14hd3\", \"gru14hd4\", \"gru14hd5\", \"sg25\", \"sig26\", \"sg27\", \"sig28\"]"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "                                 LLAVES_HOGAR + [\"ubigeo\", \"dominio\", \"estrato\", \"pobreza\", \"mieperho\", \"factor07\",\n                                                 \"gashog2d\", \"linea\", \"linpe\"])",
 "new_string": "                                 LLAVES_HOGAR + [\"ubigeo\", \"dominio\", \"estrato\", \"pobreza\", \"mieperho\", \"factor07\",\n                                                 \"gashog2d\", \"linea\", \"linpe\"] + ALIMENTOS)\n    sumaria[\"gasto_alimentos\"] = sumaria[ALIMENTOS].fillna(0).sum(axis=1)\n    sumaria[\"participacion_alimentos\"] = (100 * sumaria.gasto_alimentos / sumaria.gashog2d).where(sumaria.gashog2d > 0)\n    sumaria = sumaria.drop(columns=ALIMENTOS)"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "    base[\"pobre_extremo\"] = (base.pobreza == 1).astype(\"int8\")\n    base[\"sexo\"] = base.p207.map({1: \"Hombre\", 2: \"Mujer\"})",
 "new_string": "    base[\"pobre_extremo\"] = (base.pobreza == 1).astype(\"int8\")\n    base[\"condicion_pobreza\"] = base.pobreza.map(CONDICION)\n    base[\"sexo\"] = base.p207.map({1: \"Hombre\", 2: \"Mujer\"})"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "                \"grupo_edad\", \"sexo_jefe\", \"pobreza\", \"pobre\", \"pobre_extremo\", \"gasto_pc_mensual\", \"linea\", \"linpe\",\n                \"mieperho\", \"facpob07\", \"factor07\"]",
 "new_string": "                \"grupo_edad\", \"sexo_jefe\", \"pobreza\", \"condicion_pobreza\", \"pobre\", \"pobre_extremo\", \"gasto_pc_mensual\",\n                \"gasto_alimentos\", \"participacion_alimentos\", \"linea\", \"linpe\", \"mieperho\", \"facpob07\", \"factor07\"]"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "    hogares[\"pobre_extremo\"] = (hogares.pobreza == 1).astype(\"int8\")\n    hogares[\"nombre_dominio\"] = hogares.dominio.map(DOMINIOS)",
 "new_string": "    hogares[\"pobre_extremo\"] = (hogares.pobreza == 1).astype(\"int8\")\n    hogares[\"condicion_pobreza\"] = hogares.pobreza.map(CONDICION)\n    hogares[\"nombre_dominio\"] = hogares.dominio.map(DOMINIOS)"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\scripts\\limpiar.py",
 "old_string": "    lima_p = proporcion(base[base.dominio == 8], \"pobre\").iloc[0].valor_pct",
 "new_string": "    pa = hogares.participacion_alimentos\n    check(\"Participación de alimentos en el gasto entre 0 y 100 % (gashog2d > 0)\",\n          pa.notna().all() and pa.between(0, 100).all(),\n          f\"{pa.notna().sum():,} hogares con dato; rango {pa.min():.1f}–{pa.max():.1f} %\", esencial=False)\n    lima_p = proporcion(base[base.dominio == 8], \"pobre\").iloc[0].valor_pct"
}
```

**🔧 Bash**

```json
{
 "command": "cd /c/Users/<usuario>/Documents/GitHub/python-intermedio/tarea_4 && export PYTHONIOENCODING=utf-8 && uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py | grep -E \"Participación|Resumen|Resultado|OK:\" -A1 && S=.claude/skills/limpiando-enaho/scripts/consultar.py && uv run python $S --media participacion_alimentos --por condicion_pobreza && uv run python $S --media participacion_alimentos --por area",
 "description": "Rebuild base with food share and query it",
 "timeout": 400000
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\scripts\limpiar.py has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
[APROBADA] A  Participación de alimentos en el gasto entre 0 y 100 % (gashog2d > 0)
              33,691 hogares con dato; rango 0.0–96.5 %
--
Resumen: 15 de 15 aprobadas; 0 fallidas (0 esenciales).
Resultado: BASE VÁLIDA

--
OK: salidas/personas_2024.parquet (108,664 personas), salidas/hogares_2024.parquet (33,691 hogares), salidas/indicadores.csv (178 filas), salidas/validacion.txt
           grupo  valor   ee  ic95_inf  ic95_sup  n_muestra  poblacion_expandida
        No pobre  33.63 0.16     33.32     33.94      80837           24747319.0
   Pobre extremo  51.69 0.66     50.40     52.97       6526            1878051.0
Pobre no extremo  44.82 0.30     44.24     45.41      21301            7522396.0

Indicador: participacion_alimentos (participacion_alimentos) · peso: facpob07 · filtro: ninguno · n = 108,664 personas
Fuente: INEI, ENAHO 2024 (módulos 34 y 02), procesado con .claude/skills/limpiando-enaho
 grupo  valor   ee  ic95_inf  ic95_sup  n_muestra  poblacion_expandida
 Rural  49.47 0.27     48.94     49.99      36071            6486385.0
Urbana  34.19 0.17     33.84     34.53      72593           27661381.0

Indicador: participacion_alimentos (participacion_alimentos) · peso: facpob07 · filtro: ninguno · n = 108,664 personas
Fuente: INEI, ENAHO 2024 (módulos 34 y 02), procesado con .claude/skills/limpiando-enaho
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "offset": 25,
 "limit": 40
}
```

<details><summary>resultado</summary>

```text
25	import pandas as pd  # noqa: E402
26	
27	PROYECTO = Path(__file__).resolve().parents[4]
28	LIMPIEZA = PROYECTO / ".claude" / "skills" / "limpiando-enaho" / "scripts"
29	sys.path.insert(0, str(LIMPIEZA))
30	from estimacion import proporcion  # noqa: E402
31	
32	FIGURAS = PROYECTO / "figuras"
33	AZUL, NARANJA, GRIS, TINTA, TINTA2, FONDO = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b", "#52514e", "#fcfcfb"
34	ORDEN = {"grupo_edad": ["0-14", "15-29", "30-44", "45-64", "65 y más"], "area": ["Urbana", "Rural"],
35	         "region_natural": ["Lima Metropolitana", "Costa", "Sierra", "Selva"]}
36	ETIQUETA = {"area": "área de residencia", "sexo": "sexo", "grupo_edad": "grupo de edad",
37	            "sexo_jefe": "sexo del jefe de hogar", "region_natural": "región natural", "nombre_dominio": "dominio",
38	            "departamento": "departamento"}
39	INDICADOR = {"pobre": "Pobreza monetaria", "pobre_extremo": "Pobreza monetaria extrema"}
40	
41	
42	def cargar_base(anio=2024):
43	    archivo = PROYECTO / "salidas" / f"personas_{anio}.parquet"
44	    if not archivo.exists():
45	        print("No existe salidas/personas_2024.parquet: ejecuto primero limpiando-enaho (limpiar.py)...")
46	        r = subprocess.run([sys.executable, str(LIMPIEZA / "limpiar.py"), "--anio", str(anio)])
47	        if r.returncode != 0 or not archivo.exists():
48	            sys.exit("ERROR: la limpieza no produjo una base válida (ver salidas/validacion.txt). No grafico nada.")
49	    return pd.read_parquet(arch
… [recortado: 615 caracteres más]
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\scripts\\graficar.py",
 "offset": 64,
 "limit": 150
}
```

<details><summary>resultado</summary>

```text
64	        t["grupo"] = t.grupo.map(df.drop_duplicates("departamento").set_index("departamento").nombre_departamento)
65	    return t
66	
67	
68	FRASE = {"Hombre": "los hombres", "Mujer": "las mujeres", "Urbana": "el área urbana", "Rural": "el área rural",
69	         "Jefe hombre": "los hogares con jefe hombre", "Jefa mujer": "los hogares con jefa mujer"}
70	
71	
72	def frase(grupo, por):
73	    if grupo in FRASE:
74	        return FRASE[grupo]
75	    if por == "grupo_edad":
76	        return f"el grupo de {grupo} años".replace("de 65 y más años", "de 65 años y más")
77	    return str(grupo)
78	
79	
80	def titulo_automatico(t, indicador, por):
81	    """Un título que dice el hallazgo, calculado con los mismos números del gráfico."""
82	    nombre = INDICADOR[indicador].lower().replace("pobreza monetaria", "pobreza")
83	    series = list(dict.fromkeys(t.serie))
84	    if len(series) == 2:   # barras agrupadas: ¿una serie supera a la otra en todos los grupos?
85	        a = t[t.serie == series[0]].set_index("grupo")
86	        b = t[t.serie == series[1]].set_index("grupo")
87	        dif = (b.valor_pct - a.valor_pct).dropna()
88	        g = dif.abs().idxmax()
89	        mayor, menor = (series[1], series[0]) if dif[g] > 0 else (series[0], series[1])
90	        todos = "en todos los grupos" if (dif > 0).all() or (dif < 0).all() else "en la mayoría de grupos"
91	        return (f"La {nombre} en {frase(mayor, '')} supera a la de {frase(menor, '')} {todos}; la brecha mayor está "
9
… [recortado: 7,309 caracteres más]
```
</details>

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python - <<'EOF'\nfrom pathlib import Path\np = Path(\".claude/skills/graficando-enaho/scripts/graficar.py\")\ns = p.read_text(encoding=\"utf-8\")\ndef rep(old, new, count=1):\n    global s\n    assert s.count(old) == count, (old, s.count(old))\n    s = s.replace(old, new)\nrep(\"from estimacion import proporcion  # noqa: E402\", \"from estimacion import media, proporcion  # noqa: E402\")\nrep('''         \"region_natural\": [\"Lima Metropolitana\", \"Costa\", \"Sierra\", \"Selva\"]}''',\n    '''         \"region_natural\": [\"Lima Metropolitana\", \"Costa\", \"Sierra\", \"Selva\"],\n         \"condicion_pobreza\": [\"Pobre extremo\", \"Pobre no extremo\", \"No pobre\"]}''')\nrep('''            \"departamento\": \"departamento\"}\nINDICADOR = {\"pobre\": \"Pobreza monetaria\", \"pobre_extremo\": \"Pobreza monetaria extrema\"}''',\n    '''            \"departamento\": \"departamento\", \"condicion_pobreza\": \"condición de pobreza\"}\n# Qué se grafica: un % de personas (pobreza) o la media ponderada de una variable continua.\nMETA = {\n    \"pobre\": {\"nombre\": \"Pobreza monetaria\", \"eje\": \"% de personas en pobreza monetaria\",\n              \"unidad\": \"% de personas\", \"fmt\": \"{:.1f} %\", \"media\": False},\n    \"pobre_extremo\": {\"nombre\": \"Pobreza monetaria extrema\", \"eje\": \"% de personas en pobreza monetaria extrema\",\n                      \"unidad\": \"% de personas\", \"fmt\": \"{:.1f} %\", \"media\": False},\n    \"participacion_alimentos\": {\"nombre\": \"Participación de los alimentos en el gasto del hogar\",\n                                \"eje\": \"% del gasto total del hogar destinado a alimentos\",\n                                \"unidad\": \"% del gasto del hogar, promedio por persona\", \"fmt\": \"{:.1f} %\",\n                                \"media\": True},\n    \"gasto_pc_mensual\": {\"nombre\": \"Gasto per cápita mensual\", \"eje\": \"soles por persona al mes\",\n                         \"unidad\": \"soles corrientes por persona al mes\", \"fmt\": \"S/ {:,.0f}\", \"media\": True},\n}\nINDICADOR = {k: v[\"nombre\"] for k, v in META.items()}\n\n\ndef fmt(indicador, v):\n    return META[indicador][\"fmt\"].format(v)\n\n\ndef estimador(indicador):\n    return media if META[indicador][\"media\"] else proporcion''')\nrep('''            t = proporcion(df[df[dividir] == g], indicador, por=por)''',\n    '''            t = estimador(indicador)(df[df[dividir] == g], indicador, p
… [recortado: 3,320 caracteres más]
```

<details><summary>resultado</summary>

```text
ok
Guardado figuras\participacion_alimentos_condicion_pobreza_area.png (+ .csv). Título: Participación de los alimentos en el gasto del hogar en el área urbana: 46.7 % en las personas en pobreza extrema frente a 31.3 % en las personas no pobres
 serie            grupo  valor_pct  ic95_inf  ic95_sup  n_muestra
Urbana         No pobre      31.34     31.00     31.67      57838
Guardado figuras\participacion_alimentos_condicion_pobreza.png (+ .csv). Título: Participación de los alimentos en el gasto del hogar: 51.7 % en las personas en pobreza extrema frente a 33.6 % en las personas no pobres
serie            grupo  valor_pct  ic95_inf  ic95_sup  n_muestra
4
```
</details>

**🔧 Read**

```json
{
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\figuras\\participacion_alimentos_condicion_pobreza_area.png"
}
```

<details><summary>resultado</summary>

```text
[imagen]
```
</details>

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python - <<'EOF'\nfrom pathlib import Path\np = Path(\".claude/skills/graficando-enaho/scripts/graficar.py\")\ns = p.read_text(encoding=\"utf-8\")\nold_sub = '''    sub = (f\"{INDICADOR[indicador]} según {ETIQUETA.get(por, por)}\"\n           + (f\" y {ETIQUETA.get(dividir, dividir)}\" if dividir else \"\")\n           + f\", Perú 2024 ({META[indicador]['unidad']}; líneas grises: IC 95 %)\"\n           + (f\". Filtro: {filtro}\" if filtro else \"\"))\n'''\nassert s.count(old_sub) == 1\ns = s.replace(old_sub, \"\")\nold_head = '''    cabecera = 0.32 + 0.24 * len(lineas_titulo) + 0.3    # pulgadas para título y subtítulo'''\nnew_head = old_sub + '''    lineas_sub = textwrap.wrap(sub, 118)\n    cabecera = 0.32 + 0.24 * len(lineas_titulo) + 0.18 * len(lineas_sub) + 0.12   # pulgadas para título y subtítulo'''\nassert s.count(old_head) == 1\ns = s.replace(old_head, new_head)\nold_txt = '''    fig.text(0.015, 1 - (0.3 + 0.24 * len(lineas_titulo)) * pulg, sub, ha=\"left\", va=\"top\", fontsize=9,'''\nassert s.count(old_txt) == 1\ns = s.replace(old_txt, '''    fig.text(0.015, 1 - (0.3 + 0.24 * len(lineas_titulo)) * pulg, \"\\\\n\".join(lineas_sub), ha=\"left\", va=\"top\", fontsize=9,''')\np.write_text(s, encoding=\"utf-8\")\nEOF\nexport PYTHONIOENCODING=utf-8; G=.claude/skills/graficando-enaho/scripts/graficar.py\nuv run python $G --indicador participacion_alimentos --por condicion_pobreza --dividir area 2>&1 | head -1 && uv run python $G --todos | grep -c Guardado",
 "description": "Wrap long subtitles in chart script and regenerate",
 "timeout": 400000
}
```

<details><summary>resultado</summary>

```text
File "C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py", line 186
  File "C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\scripts\graficar.py", line 186
    fig.text(0.015, 1 - (0.3 + 0.24 * len(lineas_titulo)) * pulg, "
                                                                  ^
SyntaxError: unterminated string literal (detected at line 186)
0
```
</details>

**🔧 Bash**

```json
{
 "command": "sed -n 180,192p .claude/skills/graficando-enaho/scripts/graficar.py | cat -A | cut -c1-150",
 "description": "Inspect the broken lines in the chart script"
}
```

<details><summary>resultado</summary>

```text
if len(series) > 1:$
        ax.legend(title=ETIQUETA.get(dividir, dividir).capitalize(), fontsize=8, title_fontsize=8, frameon=False,$
                  loc="lower right")$
    pulg = 1 / alto_fig   # una pulgada en coordenadas de figura$
    fig.text(0.015, 1 - 0.22 * pulg, "\n".join(lineas_titulo), ha="left", va="top", fontsize=11.5,$
             fontweight="bold", color=TINTA, linespacing=1.25)$
    fig.text(0.015, 1 - (0.3 + 0.24 * len(lineas_titulo)) * pulg, "$
".join(lineas_sub), ha="left", va="top", fontsize=9,$
             color=TINTA2)$
    fig.text(0.015, 0.12 * pulg, "Fuente: INEI, ENAHO 2024 (mM-CM-3dulos 34 y 02). Residentes habituales ponderados con "$
             "facpob07; IC de diseM-CM-1o (conglome dentro de estrato). ElaboraciM-CM-3n: skill graficando-enaho.",$
             fontsize=7, color=TINTA2)$
    fig.tight_layout(rect=(0, 0.35 * pulg, 1, 1 - cabecera * pulg))$
```
</details>

**🔧 Bash**

```json
{
 "command": "PYTHONIOENCODING=utf-8 uv run python -c \"\nfrom pathlib import Path\np = Path('.claude/skills/graficando-enaho/scripts/graficar.py')\ns = p.read_text(encoding='utf-8')\nbad = 'pulg, \\\"\\n\\\".join(lineas_sub)'\nassert s.count(bad) == 1\ns = s.replace(bad, 'pulg, chr(10).join(lineas_sub)')\np.write_text(s, encoding='utf-8')\n\" && export PYTHONIOENCODING=utf-8 && G=.claude/skills/graficando-enaho/scripts/graficar.py && uv run python $G --indicador participacion_alimentos --por condicion_pobreza --dividir area 2>&1 | head -1 && uv run python $G --todos | grep -c Guardado",
 "description": "Fix the broken newline literal and regenerate charts",
 "timeout": 400000
}
```

<details><summary>resultado</summary>

```text
Guardado figuras\participacion_alimentos_condicion_pobreza_area.png (+ .csv). Título: Participación de los alimentos en el gasto del hogar en el área urbana: 46.7 % en las personas en pobreza extrema frente a 31.3 % en las personas no pobres
4
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\graficando-enaho\\SKILL.md",
 "old_string": "| «pobreza extrema» | `--indicador pobre_extremo` |\n| «los gráficos básicos» | `--todos` (área, sexo, departamento, edad × área) |",
 "new_string": "| «pobreza extrema» | `--indicador pobre_extremo` |\n| «cuánto gastan en alimentos los pobres», «peso de la comida en el gasto» | `--indicador participacion_alimentos --por condicion_pobreza` (añade `--dividir area` para urbano/rural) |\n| «gasto per cápita por región» | `--indicador gasto_pc_mensual --por region_natural` |\n| «los gráficos básicos» | `--todos` (área, sexo, departamento, edad × área) |"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\reference.md",
 "old_string": "| `gasto_pc_mensual` | `gashog2d / mieperho / 12` | soles corrientes por persona al mes |",
 "new_string": "| `condicion_pobreza` | `pobreza` | Pobre extremo / Pobre no extremo / No pobre |\n| `gasto_pc_mensual` | `gashog2d / mieperho / 12` | soles corrientes por persona al mes |\n| `gasto_alimentos` | suma del grupo 1 (ver abajo) | soles corrientes al año, por hogar |\n| `participacion_alimentos` | `100 × gasto_alimentos / gashog2d` | % del gasto total bruto del hogar destinado a alimentos |"
}
```

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\reference.md",
 "old_string": "## Error estándar",
 "new_string": "## Gasto en alimentos (grupo 1)\n\nSe construye como en el do-file oficial del INEI que viene en el zip 34\n(`ConstVarGasto-Metodologia actualizada.zip` → `01.ConstrVarGastoIngreso2014-2024.do`, variables `gpcrg3`, `gpcrg8` y\n`gpcrg9`), pero en soles corrientes y sin deflactar:\n\n- dentro del hogar: `gru11hd + gru12hd1 + gru12hd2 + gru13hd1 + gru13hd2 + gru13hd3`\n- fuera del hogar: `sg23 + sig24 + gru14hd + gru14hd1 + gru14hd2 + gru14hd3 + gru14hd4 + gru14hd5 + sg25 + sig26 + sg27 + sig28`\n\n`participacion_alimentos` es ese total entre `gashog2d` (gasto total bruto). Indica qué tan expuesto está el\npresupuesto del hogar a los precios de los alimentos; promediada por persona con `facpob07`.\n\n## Error estándar"
}
```

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\graficando-enaho\SKILL.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\reference.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

<details><summary>resultado</summary>

```text
The file C:\Users\<usuario>\Documents\GitHub\python-intermedio\tarea_4\.claude\skills\limpiando-enaho\reference.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

**🔧 Edit**

```json
{
 "replace_all": false,
 "file_path": "C:\\Users\\<usuario>\\Documents\\GitHub\\python-intermedio\\tarea_4\\.claude\\skills\\limpiando-enaho\\SKILL.md",
 "old_string": "   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --media gasto_pc_mensual --por region_natural\n   ```",
 "new_string": "   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --media gasto_pc_mensual --por region_natural\n   uv run python ${CLAUDE_SKILL_DIR}/scripts/consultar.py --media participacion_alimentos --por condicion_pobreza\n   ```"
}
```
