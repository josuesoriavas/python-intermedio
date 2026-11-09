"""Limpia la ENAHO 2024 (módulos 34 y 02), arma la base de personas con pobreza y factor de expansión, y la valida.

    uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py            # 2024, descarga los zip si faltan

Pipeline (siempre en este orden; ver reference.md):
  1. Leer los .dta desde los zip del INEI con convert_categoricals=False y las llaves como texto (ceros iniciales).
  2. Normalizar nombres de columna (minúsculas, sin tildes; «aÑo» -> «anio»).
  3. Filtrar residentes habituales: (p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1).
  4. Unir personas (m) con hogares (1) por conglome, vivienda y hogar con merge(validate="m:1").
  5. Construir departamento = ubigeo[:2], área (estrato <= 5 urbana), pobre (pobreza <= 2), sexo, edad, etc.
  6. Validar contra las cifras oficiales; si falla una validación esencial, se detiene con código 1.
  7. Guardar salidas/personas_2024.parquet, salidas/validacion.txt y salidas/indicadores.csv.

Las cifras salen del procesamiento: no hay ningún valor de resultado escrito a mano. Los valores de referencia
(27.6 %, 108,664, 25) solo se usan para comparar y aprobar o rechazar.
"""
import argparse
import io
import sys
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from estimacion import promedio_simple, proporcion  # noqa: E402

PROYECTO = Path(__file__).resolve().parents[4]
URL_INEI = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip"
CODIGO_INEI = {2024: 966}
ARCHIVOS = {"34": "sumaria-{anio}.dta", "02": "enaho01-{anio}-200.dta"}
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
ANCHO_LLAVES = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}

# Valores publicados por el INEI / la Sesión 16 para validar (no se usan como resultados).
REFERENCIAS = {2024: {"hogares": 33_691, "filas_modulo02": 117_721, "residentes": 108_664, "departamentos": 25,
                      "pobreza": 27.6, "pobreza_extrema": 5.5, "urbana": 24.8, "rural": 39.3,
                      "lima_metropolitana": 28.2}}
TOL_NACIONAL = 0.1   # puntos porcentuales, según la consigna
TOL_GRUPOS = 0.15    # área, extrema y Lima Metropolitana: referencias publicadas con un decimal

DEPARTAMENTOS = {"01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
                 "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
                 "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
                 "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
                 "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}
DOMINIOS = {1: "Costa Norte", 2: "Costa Centro", 3: "Costa Sur", 4: "Sierra Norte", 5: "Sierra Centro",
            6: "Sierra Sur", 7: "Selva", 8: "Lima Metropolitana"}
REGION_NATURAL = {1: "Costa", 2: "Costa", 3: "Costa", 4: "Sierra", 5: "Sierra", 6: "Sierra", 7: "Selva",
                  8: "Lima Metropolitana"}
EDADES = [(0, 14, "0-14"), (15, 29, "15-29"), (30, 44, "30-44"), (45, 64, "45-64"), (65, 200, "65 y más")]
CONDICION = {1: "Pobre extremo", 2: "Pobre no extremo", 3: "No pobre"}
# Gasto anual del hogar en alimentos (grupo 1), como en el do-file oficial del INEI
# (ConstVarGasto 2024, 01.ConstrVarGastoIngreso2014-2024.do: gpcrg3 + gpcrg8 + gpcrg9, sin deflactar):
# dentro del hogar (comprado, autoconsumo, especie, donaciones, otros) + fuera del hogar.
ALIMENTOS = ["gru11hd", "gru12hd1", "gru12hd2", "gru13hd1", "gru13hd2", "gru13hd3",          # dentro del hogar
             "sg23", "sig24",                                                                # fuera del hogar
             "gru14hd", "gru14hd1", "gru14hd2", "gru14hd3", "gru14hd4", "gru14hd5", "sg25", "sig26", "sg27", "sig28"]


class ValidacionFallida(Exception):
    pass


# ------------------------------------------------------------------------------------------------ lectura

def asegurar_zip(carpeta, anio, modulo):
    ruta = carpeta / f"{CODIGO_INEI[anio]}-Modulo{modulo}.zip"
    if not ruta.exists():
        url = URL_INEI.format(codigo=CODIGO_INEI[anio], modulo=modulo)
        print(f"Descargando {url} ...")
        carpeta.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
            r.raise_for_status()
            with open(ruta, "wb") as f:
                for trozo in r.iter_bytes():
                    f.write(trozo)
    return ruta


def normalizar(columnas):
    def limpio(c):
        c = str(c).strip().lower().replace("ñ", "ni")
        return unicodedata.normalize("NFD", c).encode("ascii", "ignore").decode()
    return [limpio(c) for c in columnas]


def leer_stata(zip_path, interno, columnas):
    with zipfile.ZipFile(zip_path) as z:
        nombre = next((n for n in z.namelist() if n.lower().endswith("/" + interno.lower())), None)
        if nombre is None:
            raise ValidacionFallida(f"No encuentro {interno} dentro de {zip_path.name}")
        datos = io.BytesIO(z.read(nombre))
    df = pd.read_stata(datos, convert_categoricals=False)
    df.columns = normalizar(df.columns)
    faltan = set(columnas) - set(df.columns)
    if faltan:
        raise ValidacionFallida(f"Faltan columnas en {interno}: {sorted(faltan)}")
    df = df[columnas].copy()
    for llave, ancho in ANCHO_LLAVES.items():   # las llaves deben seguir siendo texto con sus ceros iniciales
        if llave in df.columns:
            df[llave] = df[llave].astype(str).str.strip()
    return df, nombre


# ------------------------------------------------------------------------------------------------ pipeline

def construir(anio, carpeta_datos):
    zip34 = asegurar_zip(carpeta_datos, anio, "34")
    zip02 = asegurar_zip(carpeta_datos, anio, "02")
    sumaria, arch34 = leer_stata(zip34, ARCHIVOS["34"].format(anio=anio),
                                 LLAVES_HOGAR + ["ubigeo", "dominio", "estrato", "pobreza", "mieperho", "factor07",
                                                 "gashog2d", "linea", "linpe"] + ALIMENTOS)
    sumaria["gasto_alimentos"] = sumaria[ALIMENTOS].fillna(0).sum(axis=1)
    sumaria["participacion_alimentos"] = (100 * sumaria.gasto_alimentos / sumaria.gashog2d).where(sumaria.gashog2d > 0)
    sumaria = sumaria.drop(columns=ALIMENTOS)
    miembros, arch02 = leer_stata(zip02, ARCHIVOS["02"].format(anio=anio),
                                  LLAVES_HOGAR + ["codperso", "ubigeo", "p203", "p204", "p205", "p206", "p207",
                                                  "p208a", "facpob07"])
    filas_modulo02 = len(miembros)

    # Sexo del jefe de hogar (p203 == 1) para todos los miembros del hogar
    jefes = miembros.loc[miembros.p203 == 1, LLAVES_HOGAR + ["p207"]].rename(columns={"p207": "sexo_jefe_cod"})

    residente = ((miembros.p204 == 1) & (miembros.p205 == 2)) | ((miembros.p204 == 2) & (miembros.p206 == 1))
    personas = miembros[residente].copy()
    n_residentes = len(personas)

    base = personas.merge(sumaria.drop(columns="ubigeo"), on=LLAVES_HOGAR, how="left", validate="m:1",
                          indicator=True)
    sin_hogar = int((base._merge != "both").sum())
    base = base.drop(columns="_merge")
    base = base.merge(jefes, on=LLAVES_HOGAR, how="left", validate="m:1")

    base["departamento"] = base.ubigeo.str[:2]
    base["nombre_departamento"] = base.departamento.map(DEPARTAMENTOS)
    base["area"] = (base.estrato <= 5).map({True: "Urbana", False: "Rural"})
    base["pobre"] = (base.pobreza <= 2).astype("int8")
    base["pobre_extremo"] = (base.pobreza == 1).astype("int8")
    base["condicion_pobreza"] = base.pobreza.map(CONDICION)
    base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    base["sexo_jefe"] = base.sexo_jefe_cod.map({1: "Jefe hombre", 2: "Jefa mujer"})
    base["edad"] = base.p208a
    base["grupo_edad"] = pd.cut(base.edad, [a - 0.5 for a, _, _ in EDADES] + [EDADES[-1][1]],
                                labels=[e for _, _, e in EDADES]).astype(str)
    base["nombre_dominio"] = base.dominio.map(DOMINIOS)
    base["region_natural"] = base.dominio.map(REGION_NATURAL)
    base["gasto_pc_mensual"] = base.gashog2d / base.mieperho / 12
    base["anio"] = anio
    columnas = ["anio", "conglome", "vivienda", "hogar", "codperso", "ubigeo", "departamento", "nombre_departamento",
                "dominio", "nombre_dominio", "region_natural", "estrato", "area", "p203", "sexo", "edad",
                "grupo_edad", "sexo_jefe", "pobreza", "condicion_pobreza", "pobre", "pobre_extremo", "gasto_pc_mensual",
                "gasto_alimentos", "participacion_alimentos", "linea", "linpe", "mieperho", "facpob07", "factor07"]
    # Base de hogares para el método oficial del INEI: cada hogar pesa factor07 × mieperho (miembros del hogar)
    hogares = sumaria.copy()
    hogares["departamento"] = hogares.ubigeo.str[:2]
    hogares["nombre_departamento"] = hogares.departamento.map(DEPARTAMENTOS)
    hogares["area"] = (hogares.estrato <= 5).map({True: "Urbana", False: "Rural"})
    hogares["pobre"] = (hogares.pobreza <= 2).astype("int8")
    hogares["pobre_extremo"] = (hogares.pobreza == 1).astype("int8")
    hogares["condicion_pobreza"] = hogares.pobreza.map(CONDICION)
    hogares["nombre_dominio"] = hogares.dominio.map(DOMINIOS)
    hogares["region_natural"] = hogares.dominio.map(REGION_NATURAL)
    hogares["peso_inei"] = hogares.factor07 * hogares.mieperho
    hogares = hogares[hogares.mieperho > 0]
    hogares["anio"] = anio

    contexto = {"sumaria": sumaria, "miembros_filas": filas_modulo02, "n_residentes": n_residentes,
                "sin_hogar": sin_hogar, "archivos": (f"{zip34.name}:{arch34}", f"{zip02.name}:{arch02}"),
                "miembros": miembros, "hogares": hogares}
    return base[columnas], contexto


def validar(base, ctx, anio):
    ref = REFERENCIAS[anio]
    sumaria, miembros = ctx["sumaria"], ctx["miembros"]
    checks = []

    def check(nombre, ok, detalle, esencial=True):
        checks.append({"nombre": nombre, "ok": bool(ok), "detalle": detalle, "esencial": esencial})

    dup_h = int(sumaria.duplicated(LLAVES_HOGAR).sum())
    check("Llaves de hogar únicas en la sumaria (conglome, vivienda, hogar)", dup_h == 0 and len(sumaria) == ref["hogares"],
          f"{len(sumaria):,} hogares (ref. {ref['hogares']:,}), {dup_h} duplicados")
    dup_p = int(miembros.duplicated(LLAVES_HOGAR + ["codperso"]).sum())
    check("Llaves de persona únicas en el módulo 02 (+ codperso)", dup_p == 0 and ctx["miembros_filas"] == ref["filas_modulo02"],
          f"{ctx['miembros_filas']:,} filas (ref. {ref['filas_modulo02']:,}), {dup_p} duplicados")
    malos = {k: int((base[k].str.len() != w).sum()) for k, w in ANCHO_LLAVES.items()}
    check("Llaves leídas como texto con ceros iniciales", sum(malos.values()) == 0,
          ", ".join(f"{k}: {w} car. ({malos[k]} mal)" for k, w in ANCHO_LLAVES.items()))
    check("Residentes habituales", ctx["n_residentes"] == ref["residentes"],
          f"{ctx['n_residentes']:,} (ref. {ref['residentes']:,}) con (p204==1 & p205==2) | (p204==2 & p206==1)")
    check("Unión m:1 personas-hogares sin duplicar ni perder filas",
          len(base) == ctx["n_residentes"] and ctx["sin_hogar"] == 0,
          f"{ctx['n_residentes']:,} antes, {len(base):,} después, {ctx['sin_hogar']} personas sin hogar en la sumaria")
    deps = sorted(base.departamento.unique())
    check("25 códigos departamentales (ubigeo[:2] = 01..25, Lima 15 y Callao 07 separados)",
          deps == sorted(DEPARTAMENTOS) and len(deps) == ref["departamentos"],
          f"{len(deps)} códigos: {deps[0]}..{deps[-1]}")
    pesos_ok = base.facpob07.gt(0).all() and base.factor07.gt(0).all()
    check("Factores de expansión válidos (facpob07 y factor07 > 0, sin nulos)", pesos_ok and base.facpob07.notna().all(),
          f"población expandida (Σ facpob07) = {base.facpob07.sum():,.0f} personas")

    nac = proporcion(base, "pobre").iloc[0]
    check("Pobreza monetaria nacional (personas, facpob07)", abs(nac.valor_pct - ref["pobreza"]) <= TOL_NACIONAL,
          f"{nac.valor_pct:.2f} % (ref. {ref['pobreza']} %, tol. ±{TOL_NACIONAL}); IC95 {nac.ic95_inf:.2f}–{nac.ic95_sup:.2f}")
    hogares = ctx["hogares"]
    hog = proporcion(hogares, "pobre", peso="peso_inei").iloc[0].valor_pct
    check("Pobreza monetaria nacional (método INEI: sumaria, factor07 × mieperho)",
          abs(hog - ref["pobreza"]) <= TOL_NACIONAL, f"{hog:.2f} % (ref. {ref['pobreza']} %, tol. ±{TOL_NACIONAL})")
    simple = promedio_simple(base, "pobre")
    check("La ponderación cambia el resultado (promedio simple ≠ ponderado)", abs(simple - nac.valor_pct) > 0.5,
          f"sin ponderar daría {simple:.2f} %: {simple - nac.valor_pct:+.2f} pp de sesgo", esencial=False)
    ext = proporcion(base, "pobre_extremo").iloc[0]
    check("Pobreza extrema nacional (personas, facpob07)", abs(ext.valor_pct - ref["pobreza_extrema"]) <= TOL_GRUPOS,
          f"{ext.valor_pct:.2f} % (ref. {ref['pobreza_extrema']} %)", esencial=False)
    # Área y Lima Metropolitana: se aprueban si el método INEI reproduce la cifra oficial; se informa también la
    # estimación con residentes habituales para que la diferencia quede a la vista.
    area_p = proporcion(base, "pobre", por="area").set_index("grupo").valor_pct
    area_h = proporcion(hogares, "pobre", peso="peso_inei", por="area").set_index("grupo").valor_pct
    for g, k in (("Urbana", "urbana"), ("Rural", "rural")):
        check(f"Pobreza {k}", abs(area_h[g] - ref[k]) <= TOL_NACIONAL,
              f"método INEI {area_h[g]:.2f} % · residentes habituales {area_p[g]:.2f} % (ref. {ref[k]} %)",
              esencial=False)
    pa = hogares.participacion_alimentos
    check("Participación de alimentos en el gasto entre 0 y 100 % (gashog2d > 0)",
          pa.notna().all() and pa.between(0, 100).all(),
          f"{pa.notna().sum():,} hogares con dato; rango {pa.min():.1f}–{pa.max():.1f} %", esencial=False)
    lima_p = proporcion(base[base.dominio == 8], "pobre").iloc[0].valor_pct
    lima_h = proporcion(hogares[hogares.dominio == 8], "pobre", peso="peso_inei").iloc[0].valor_pct
    check("Pobreza en Lima Metropolitana (dominio 8)", abs(lima_h - ref["lima_metropolitana"]) <= TOL_NACIONAL,
          f"método INEI {lima_h:.2f} % · residentes habituales {lima_p:.2f} % (ref. {ref['lima_metropolitana']} %)",
          esencial=False)
    return checks, {"nacional": nac, "hogares_metodo_inei": hog, "simple": simple,
                    "miembros_mieperho": int(hogares.mieperho.sum()),
                    "miembros_p204": int((miembros.p204 == 1).sum()),
                    "ausentes": int(((miembros.p204 == 1) & (miembros.p205 == 1)).sum()),
                    "no_miembros_presentes": int(((miembros.p204 == 2) & (miembros.p206 == 1)).sum())}


def indicadores(base, hogares, anio):
    """Tabla larga de indicadores. metodo = personas (residentes habituales, facpob07; principal) o
    inei_hogares (sumaria, factor07 × mieperho; reproduce las cifras oficiales, solo dimensiones del hogar)."""
    filas = []
    dims_hogar = [("nacional", None), ("area", "area"), ("region_natural", "region_natural"),
                  ("dominio", "nombre_dominio"), ("departamento", "departamento")]
    dims_persona = dims_hogar + [("sexo", "sexo"), ("grupo_edad", "grupo_edad"), ("sexo_jefe", "sexo_jefe")]
    for metodo, df, peso, dims, n_unidad in (("personas", base, "facpob07", dims_persona, "personas"),
                                             ("inei_hogares", hogares, "peso_inei", dims_hogar, "hogares")):
        for indicador in ("pobre", "pobre_extremo"):
            for dim, col in dims:
                t = proporcion(df, indicador, peso=peso, por=col)
                t.insert(0, "dimension", dim)
                t.insert(2, "indicador", "pobreza" if indicador == "pobre" else "pobreza_extrema")
                t["nombre"] = t.grupo.map(DEPARTAMENTOS) if dim == "departamento" else t.grupo
                t["metodo"], t["peso"], t["unidad_muestra"] = metodo, peso, n_unidad
                filas.append(t)
    out = pd.concat(filas, ignore_index=True)
    out["anio"] = anio
    out["fuente"] = f"INEI, ENAHO {anio} (módulos 34 y 02)"
    for c in ("valor_pct", "ee_pct", "ic95_inf", "ic95_sup"):
        out[c] = out[c].round(3)
    out["poblacion_expandida"] = out.poblacion_expandida.round(0).astype("int64")
    return out[["anio", "metodo", "dimension", "grupo", "nombre", "indicador", "valor_pct", "ee_pct", "ic95_inf",
                "ic95_sup", "n_muestra", "unidad_muestra", "poblacion_expandida", "peso", "fuente"]]


def escribir_validacion(ruta, checks, resumen, ctx, anio):
    fallidas = [c for c in checks if not c["ok"]]
    esenciales = [c for c in fallidas if c["esencial"]]
    lineas = [f"VALIDACIÓN ENAHO {anio} · skill limpiando-enaho",
              f"Generado: {datetime.now():%Y-%m-%d %H:%M} · script: .claude/skills/limpiando-enaho/scripts/limpiar.py",
              f"Fuente: INEI, ENAHO {anio} (código {CODIGO_INEI[anio]}): {ctx['archivos'][0]} y {ctx['archivos'][1]}",
              "Unidad de análisis: personas residentes habituales. Peso: facpob07 (factor de expansión poblacional).",
              "E = validación esencial (si falla, el proceso se detiene); A = advertencia.", ""]
    for c in checks:
        estado = "APROBADA" if c["ok"] else "FALLIDA "
        lineas.append(f"[{estado}] {'E' if c['esencial'] else 'A'}  {c['nombre']}")
        lineas.append(f"              {c['detalle']}")
    lineas += ["", f"Resumen: {len(checks) - len(fallidas)} de {len(checks)} aprobadas; "
                   f"{len(fallidas)} fallidas ({len(esenciales)} esenciales).",
               "Resultado: " + ("BASE VÁLIDA" if not esenciales else "BASE RECHAZADA: no usar estas cifras"),
               "", f"Pobreza nacional {anio}: {resumen['nacional'].valor_pct:.2f} % de las personas (facpob07) · "
                   f"{resumen['hogares_metodo_inei']:.2f} % con el método INEI (factor07 × mieperho).",
               "",
               "Nota sobre los dos métodos. La base principal son los residentes habituales del módulo 02 "
               f"({ctx['n_residentes']:,} personas) ponderados con facpob07. El INEI publica la pobreza con la sumaria, "
               f"donde cada hogar pesa factor07 × mieperho (Σ mieperho = {resumen['miembros_mieperho']:,}; en el "
               f"módulo 02 hay {resumen['miembros_p204']:,} personas con p204 == 1, miembros del hogar). Los "
               f"residentes habituales excluyen a {resumen['ausentes']:,} miembros ausentes 30 días o más "
               f"(p204 == 1 y p205 == 1) e incluyen a {resumen['no_miembros_presentes']:,} no miembros presentes 30 "
               "días o más (p204 == 2 y p206 == 1). Por eso sus cifras difieren unas décimas de las oficiales. El "
               "método INEI se usa para validar contra las cifras publicadas y está en indicadores.csv con "
               "metodo = inei_hogares."]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return esenciales


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--anio", type=int, default=2024, choices=sorted(CODIGO_INEI))
    p.add_argument("--datos", default=str(PROYECTO / "datos" / "inei"))
    p.add_argument("--salidas", default=str(PROYECTO / "salidas"))
    a = p.parse_args()
    salidas = Path(a.salidas)
    salidas.mkdir(parents=True, exist_ok=True)

    try:
        base, ctx = construir(a.anio, Path(a.datos))
    except ValidacionFallida as e:
        (salidas / "validacion.txt").write_text(f"BASE RECHAZADA: {e}\n", encoding="utf-8")
        sys.exit(f"ERROR: {e}")
    checks, resumen = validar(base, ctx, a.anio)
    esenciales = escribir_validacion(salidas / "validacion.txt", checks, resumen, ctx, a.anio)
    print((salidas / "validacion.txt").read_text(encoding="utf-8"))
    if esenciales:
        destino = salidas / f"personas_{a.anio}.parquet"
        destino.unlink(missing_ok=True)   # que nadie use una base que no pasó la validación
        sys.exit("ERROR: fallaron validaciones esenciales: " + "; ".join(c["nombre"] for c in esenciales))

    base.to_parquet(salidas / f"personas_{a.anio}.parquet", index=False)
    hogares = ctx["hogares"]
    hogares.to_parquet(salidas / f"hogares_{a.anio}.parquet", index=False)
    ind = indicadores(base, hogares, a.anio)
    ind.to_csv(salidas / "indicadores.csv", index=False, encoding="utf-8")
    print(f"OK: salidas/personas_{a.anio}.parquet ({len(base):,} personas), salidas/hogares_{a.anio}.parquet "
          f"({len(hogares):,} hogares), salidas/indicadores.csv ({len(ind)} filas), salidas/validacion.txt")


if __name__ == "__main__":
    main()
