// Dashboard "El Niño y el agro peruano": lee data/datos.json y data/mapa.json
// (generados por scripts/analizar_datos.py) y redibuja todo cuando cambia un filtro.
const C = { calido: '#d9480f', calidoSuave: '#f4a261', frio: '#1971c2', gris: '#b8b2a7', verde: '#2f7d4f', tinta: '#1f2a2e', mar: '#0b3d4f' };
const EVENTOS_CLAVE = [1983, 1987, 1992, 1998, 2016, 2017, 2023, 2024];
const NOMBRE_IND = { produccion: 'Producción', rendimiento: 'Rendimiento', area: 'Área cosechada' };
const UNIDAD_IND = { produccion: 't', rendimiento: 't/ha', area: 'ha' };
const CONFIG = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'] };
const BASE = {
  font: { family: 'Inter, system-ui, sans-serif', size: 12, color: C.tinta },
  paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
  margin: { l: 56, r: 16, t: 10, b: 40 },
  hoverlabel: { font: { family: 'Inter, sans-serif' } },
};

const S = { cultivo: 'Mango', indicador: 'produccion', tipo: 'mod', desde: 1961, hasta: 2024, grupo: 'Todos', anioMapa: 2023 };
let D, M, ICEN_ANIO;

const $ = (id) => document.getElementById(id);
const pct = (x, d = 0) => (x == null || isNaN(x) ? '—' : `${x > 0 ? '+' : ''}${(x * 100).toFixed(d)} %`);
const fmt = (x) => (x == null ? '—' : x.toLocaleString('es-PE', { maximumFractionDigits: x < 100 ? 2 : 0 }));
const media = (a) => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : null);

function esNino(anio) {
  const v = ICEN_ANIO[anio];
  if (v == null) return false;
  return S.tipo === 'mod' ? v > 1.0 : v > 0.4;
}
const esNormal = (anio) => ICEN_ANIO[anio] != null && ICEN_ANIO[anio] <= 0.4;
const enRango = (anio) => anio >= S.desde && anio <= S.hasta;

// Desvío promedio en años Niño y sin Niño de un cultivo, dentro del periodo filtrado
function resumen(cultivo, ind = 'produccion') {
  const s = D.peru[cultivo];
  const nino = [], normal = [];
  let peor = null;
  s.anio.forEach((a, i) => {
    const d = s[`${ind}_desvio`][i];
    if (d == null || !enRango(a)) return;
    if (esNino(a)) nino.push(d);
    else if (esNormal(a)) normal.push(d);
    if (!peor || d < peor.d) peor = { a, d };
  });
  const mN = media(nino), mS = media(normal);
  return { nino: mN, normal: mS, dif: mN != null && mS != null ? mN - mS : null, n: nino.length, peor };
}

function filasCultivo() {
  const s = D.peru[S.cultivo];
  return s.anio.map((a, i) => ({ a, i })).filter(({ a }) => enRango(a));
}

// ---------- Alerta y KPIs ----------
function pintarAlerta() {
  const h = D.hallazgos.estado_actual;
  const [y, m] = h.mes.split('-');
  const mes = new Date(+y, +m - 1, 1).toLocaleDateString('es-PE', { month: 'long', year: 'numeric' });
  $('alerta').innerHTML = `<div>🌊 <strong>El Niño costero está en curso.</strong> En ${mes} el mar frente al Perú (Niño 1+2) estaba
    <strong>${h.anomalia_nino12 > 0 ? '+' : ''}${h.anomalia_nino12.toFixed(1)} °C</strong> sobre lo normal (OISST, NOAA). El evento empezó en
    ${h.evento_inicio.replace('-', '/')} y el ICEN ya alcanzó ${h.icen_max.toFixed(2)} °C (categoría ${h.magnitud}). Lo que pasó con los cultivos en los
    Niños anteriores es una pista de lo que puede venir.</div>`;
}

function pintarKPIs() {
  const r = resumen(S.cultivo, S.indicador);
  const anios = D.anios.filter((x) => enRango(x.anio) && x.anio >= 1961);
  const nNino = anios.filter((x) => esNino(x.anio));
  const ranking = D.cultivos.map((c) => ({ c: c.cultivo, ...resumen(c.cultivo) })).filter((x) => x.dif != null && x.n >= 2)
    .sort((a, b) => a.dif - b.dif);
  const peorCult = ranking[0];
  const h = D.hallazgos.estado_actual;
  const ind = NOMBRE_IND[S.indicador].toLowerCase();
  const tarjetas = [
    { lbl: 'Mar frente al Perú hoy', val: `+${h.anomalia_nino12.toFixed(1)} °C`, cls: 'neg', sub: `Anomalía Niño 1+2, ${h.mes} · ICEN máx. 2026: ${h.icen_max.toFixed(2)} °C` },
    { lbl: `${S.cultivo}: ${ind} en años Niño`, val: pct(r.nino), cls: r.nino < 0 ? 'neg' : 'pos', sub: `vs. ${pct(r.normal)} en años sin Niño · ${r.n} años Niño` },
    { lbl: `Peor año del ${S.cultivo.toLowerCase()}`, val: r.peor ? `${r.peor.a}` : '—', cls: '', sub: r.peor ? `${pct(r.peor.d)} vs. tendencia${esNino(r.peor.a) ? ' · año Niño' : ''}` : 'sin datos en el periodo' },
    { lbl: 'Cultivo más golpeado (producción)', val: peorCult ? peorCult.c : '—', cls: 'neg', sub: peorCult ? `${(peorCult.dif * 100).toFixed(0)} pp entre años Niño y sin Niño` : '' },
    { lbl: 'Años Niño en el periodo', val: `${nNino.length} de ${anios.length}`, cls: '', sub: nNino.map((x) => x.anio).join(', ') || 'ninguno' },
  ];
  $('kpis').innerHTML = tarjetas.map((t) => `<div class="kpi"><p class="lbl">${t.lbl}</p><p class="val ${t.cls}">${t.val}</p><p class="sub">${t.sub}</p></div>`).join('');
}

// ---------- Gráficos ----------
function grafICEN() {
  const f = D.icen.fecha.map((x) => `${x}-15`);
  const pos = D.icen.icen.map((v) => (v > 0 ? v : 0));
  const neg = D.icen.icen.map((v) => (v < 0 ? v : 0));
  const oi = { x: D.oisst.fecha.map((x) => `${x}-15`), y: D.oisst.anom };
  const umbrales = [[0.4, 'débil'], [1.0, 'moderado'], [1.7, 'fuerte'], [3.0, 'extraordinario']];
  const shapes = umbrales.map(([u]) => ({ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: u, y1: u, line: { color: C.calido, width: 1, dash: 'dot' } }));
  shapes.push({ type: 'rect', xref: 'x', yref: 'paper', x0: `${S.desde}-01-01`, x1: `${S.hasta}-12-31`, y0: 0, y1: 1, fillcolor: 'rgba(11,61,79,.06)', line: { width: 0 }, layer: 'below' });
  const ann = umbrales.map(([u, t]) => ({ xref: 'paper', x: 0.005, y: u, text: t, showarrow: false, yanchor: 'bottom', xanchor: 'left', font: { size: 10, color: C.calido } }));
  [['1983-06-15', 'Niño 1982-83'], ['1997-11-15', 'Niño 1997-98'], ['2023-07-15', 'Niño 2023'], ['2026-09-15', '2026: hoy']].forEach(([x, t]) => {
    const i = D.icen.fecha.indexOf(x.slice(0, 7));
    const y = i >= 0 ? D.icen.icen[i] : oi.y[oi.y.length - 1];
    ann.push({ x, y, text: t, showarrow: true, arrowhead: 0, ax: 0, ay: -22, font: { size: 11, color: C.tinta } });
  });
  Plotly.react('g-icen', [
    { x: f, y: pos, type: 'scatter', mode: 'lines', fill: 'tozeroy', line: { color: C.calido, width: 1 }, fillcolor: 'rgba(217,72,15,.55)', name: 'ICEN cálido', hovertemplate: '%{x|%b %Y}: %{y:.2f} °C<extra></extra>' },
    { x: f, y: neg, type: 'scatter', mode: 'lines', fill: 'tozeroy', line: { color: C.frio, width: 1 }, fillcolor: 'rgba(25,113,194,.45)', name: 'ICEN frío', hoverinfo: 'skip' },
    { x: oi.x, y: oi.y, type: 'scatter', mode: 'lines+markers', line: { color: C.tinta, width: 1.5, dash: 'dot' }, marker: { size: 4 }, name: 'Anomalía mensual OISST (reciente)', hovertemplate: 'OISST %{x|%b %Y}: %{y:.2f} °C<extra></extra>' },
  ], { ...BASE, shapes, annotations: ann, showlegend: true, legend: { orientation: 'h', y: 1.12, x: 0 },
    yaxis: { title: 'ICEN (°C)', zeroline: true, zerolinecolor: '#999', gridcolor: '#eee' },
    xaxis: { type: 'date', gridcolor: '#f2f2f2', rangeslider: { visible: false } } }, CONFIG);
}

function grafSerie() {
  const s = D.peru[S.cultivo];
  const filas = filasCultivo();
  const ind = S.indicador;
  const x = filas.map(({ a }) => a);
  const y = filas.map(({ i }) => s[ind][i]);
  const tend = filas.map(({ i }) => s[`${ind}_tendencia`][i]);
  const des = filas.map(({ i }) => s[`${ind}_desvio`][i]);
  const color = x.map((a) => (esNino(a) ? C.calido : C.gris));
  $('t-serie').textContent = `2 · ${NOMBRE_IND[ind]} de ${S.cultivo.toLowerCase()} en el Perú (${UNIDAD_IND[ind]}), ${S.desde}-${S.hasta}`;
  Plotly.react('g-serie', [
    { x, y, type: 'bar', marker: { color }, name: NOMBRE_IND[ind], customdata: des.map((d, k) => [pct(d, 1), ICEN_ANIO[x[k]] ?? '—']),
      hovertemplate: `%{x}: %{y:,.2f} ${UNIDAD_IND[ind]}<br>Desvío vs. tendencia: %{customdata[0]}<br>ICEN ene-jun: %{customdata[1]} °C<extra></extra>` },
    { x, y: tend, type: 'scatter', mode: 'lines', line: { color: C.mar, width: 2 }, name: 'Tendencia', hoverinfo: 'skip' },
  ], { ...BASE, showlegend: false, bargap: 0.15, yaxis: { title: UNIDAD_IND[ind], gridcolor: '#eee', separatethousands: true }, xaxis: { gridcolor: '#f5f5f5' } }, CONFIG);
}

function grafRanking() {
  let lista = D.cultivos.filter((c) => S.grupo === 'Todos' || c.grupo === S.grupo)
    .map((c) => ({ ...c, ...resumen(c.cultivo) })).filter((x) => x.dif != null);
  lista.sort((a, b) => b.dif - a.dif); // de menos a más golpeado (Plotly dibuja de abajo hacia arriba)
  Plotly.react('g-ranking', [{
    type: 'bar', orientation: 'h',
    y: lista.map((x) => x.cultivo), x: lista.map((x) => x.dif * 100),
    marker: { color: lista.map((x) => (x.cultivo === S.cultivo ? C.mar : x.dif < 0 ? C.calidoSuave : '#9cc5a1')), line: { color: lista.map((x) => (x.cultivo === S.cultivo ? C.mar : 'rgba(0,0,0,0)')), width: 1.5 } },
    customdata: lista.map((x) => [pct(x.nino, 1), pct(x.normal, 1), x.n, x.grupo, x.zona]),
    hovertemplate: '<b>%{y}</b> (%{customdata[3]}, %{customdata[4]})<br>Años Niño: %{customdata[0]} · sin Niño: %{customdata[1]}<br>Diferencia: %{x:.1f} pp · %{customdata[2]} años Niño<extra></extra>',
  }], { ...BASE, margin: { l: 130, r: 16, t: 10, b: 40 }, xaxis: { title: 'pp (años Niño − años sin Niño)', zeroline: true, zerolinecolor: '#666', gridcolor: '#eee' }, yaxis: { automargin: true, tickfont: { size: 11 } } }, CONFIG);
}

function grafDispersion() {
  const s = D.peru[S.cultivo];
  const ind = S.indicador;
  const pts = filasCultivo().map(({ a, i }) => ({ a, x: ICEN_ANIO[a], y: s[`${ind}_desvio`][i] })).filter((p) => p.x != null && p.y != null);
  const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y * 100);
  const mx = media(xs), my = media(ys);
  let sxy = 0, sxx = 0, syy = 0;
  xs.forEach((x, k) => { sxy += (x - mx) * (ys[k] - my); sxx += (x - mx) ** 2; syy += (ys[k] - my) ** 2; });
  const b = sxy / sxx, a0 = my - b * mx, r = sxy / Math.sqrt(sxx * syy);
  const xr = [Math.min(...xs), Math.max(...xs)];
  const destacar = pts.filter((p) => p.x > 1.0 || p.y < -0.3);
  $('t-disp').textContent = `4 · Intensidad de El Niño vs. desvío (${S.cultivo.toLowerCase()}, r = ${isFinite(r) ? r.toFixed(2) : '—'})`;
  Plotly.react('g-disp', [
    { x: xs, y: ys, mode: 'markers', type: 'scatter', marker: { size: 9, color: pts.map((p) => (esNino(p.a) ? C.calido : C.gris)), line: { color: '#fff', width: 1 } },
      text: pts.map((p) => p.a), hovertemplate: '%{text}: ICEN %{x:.2f} °C · desvío %{y:.1f} %<extra></extra>', name: 'Años' },
    { x: xr, y: xr.map((x) => a0 + b * x), mode: 'lines', line: { color: C.mar, dash: 'dash', width: 1.5 }, hoverinfo: 'skip', name: 'Tendencia lineal' },
    { x: destacar.map((p) => p.x), y: destacar.map((p) => p.y * 100), mode: 'text', text: destacar.map((p) => p.a), textposition: 'top center', textfont: { size: 10 }, hoverinfo: 'skip' },
  ], { ...BASE, showlegend: false, xaxis: { title: 'ICEN promedio enero-junio (°C)', zeroline: true, gridcolor: '#eee' }, yaxis: { title: `Desvío de ${NOMBRE_IND[ind].toLowerCase()} (%)`, zeroline: true, zerolinecolor: '#666', gridcolor: '#eee' } }, CONFIG);
}

function grafMapa() {
  const datos = (M.desvio[S.cultivo] || {})[S.anioMapa] || {};
  const iso = Object.keys(datos);
  const icen = ICEN_ANIO[S.anioMapa];
  $('t-mapa').textContent = `5 · ¿Quién más pierde? ${S.cultivo} en ${S.anioMapa} (ICEN ene-jun: ${icen != null ? icen.toFixed(2) + ' °C' : '—'})`;
  Plotly.react('g-mapa', [{
    type: 'choropleth', locationmode: 'ISO-3', locations: iso, z: iso.map((k) => datos[k]),
    text: iso.map((k) => M.paises[k]), zmin: -60, zmax: 60, zmid: 0,
    colorscale: [[0, '#b2182b'], [0.25, '#ef8a62'], [0.45, '#fddbc7'], [0.5, '#f7f7f7'], [0.55, '#d1e5f0'], [0.75, '#67a9cf'], [1, '#2166ac']],
    marker: { line: { color: '#fff', width: 0.4 } },
    colorbar: { title: { text: 'Desvío (%)', side: 'right' }, ticksuffix: '%', thickness: 12, len: 0.8 },
    hovertemplate: '<b>%{text}</b><br>Desvío vs. tendencia: %{z:.1f} %<extra></extra>',
  }], { ...BASE, margin: { l: 0, r: 0, t: 0, b: 0 },
    geo: { projection: { type: 'natural earth' }, showframe: false, showcoastlines: false, showcountries: true, countrycolor: '#fff', showland: true, landcolor: '#e6e1d6', bgcolor: 'rgba(0,0,0,0)', lataxis: { range: [-58, 80] } } }, CONFIG);
}

function grafCalor() {
  const ind = S.indicador;
  const orden = [...D.vulnerabilidad].sort((a, b) => b.diferencia - a.diferencia).map((v) => v.cultivo);
  // Plotly dibuja la primera fila abajo: los más golpeados quedan arriba
  const cultivos = [...D.cultivos.map((c) => c.cultivo).filter((c) => !orden.includes(c)), ...orden];
  const anios = EVENTOS_CLAVE.filter(enRango);
  const z = cultivos.map((c) => anios.map((a) => {
    const s = D.peru[c]; const i = s.anio.indexOf(a);
    const d = i >= 0 ? s[`${ind}_desvio`][i] : null;
    return d == null ? null : Math.round(d * 1000) / 10;
  }));
  Plotly.react('g-calor', [{
    type: 'heatmap', x: anios.map(String), y: cultivos, z,
    zmin: -50, zmax: 50, zmid: 0, xgap: 2, ygap: 2,
    colorscale: [[0, '#b2182b'], [0.3, '#ef8a62'], [0.5, '#f7f7f7'], [0.7, '#67a9cf'], [1, '#2166ac']],
    colorbar: { title: { text: '%', side: 'right' }, thickness: 12 },
    texttemplate: '%{z:.0f}', textfont: { size: 10 },
    hovertemplate: '%{y} · %{x}: %{z:.1f} % vs. tendencia<extra></extra>',
  }], { ...BASE, margin: { l: 140, r: 16, t: 10, b: 40 }, xaxis: { type: 'category', title: 'Año (ICEN ene-jun > 1.0 °C, más 2017 y 2024)', side: 'bottom' }, yaxis: { automargin: true, tickfont: { size: 11 } } }, CONFIG);
}

function actualizar() {
  $('v-desde').textContent = S.desde;
  $('v-hasta').textContent = S.hasta;
  pintarKPIs();
  grafICEN();
  grafSerie();
  grafRanking();
  grafDispersion();
  grafMapa();
  grafCalor();
}

function descargarCSV() {
  const s = D.peru[S.cultivo];
  const cab = ['anio', 'cultivo', 'produccion_t', 'area_ha', 'rendimiento_t_ha', 'desvio_produccion', 'desvio_area', 'desvio_rendimiento', 'icen_ene_jun', 'anio_nino', 'flag_fao'];
  const filas = filasCultivo().map(({ a, i }) => [a, S.cultivo, s.produccion[i], s.area[i], s.rendimiento[i], s.produccion_desvio[i], s.area_desvio[i], s.rendimiento_desvio[i], ICEN_ANIO[a] ?? '', esNino(a) ? 'si' : 'no', s.flag[i]]);
  const csv = [cab, ...filas].map((f) => f.map((v) => (v == null ? '' : v)).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }));
  const a = Object.assign(document.createElement('a'), { href: url, download: `nino_agro_${S.cultivo.toLowerCase().replace(/\s+/g, '_')}_${S.desde}-${S.hasta}.csv` });
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}

function init() {
  ICEN_ANIO = Object.fromEntries(D.anios.map((x) => [x.anio, x.icen_ene_jun]));
  $('f-cultivo').innerHTML = D.cultivos.map((c) => `<option ${c.cultivo === S.cultivo ? 'selected' : ''}>${c.cultivo}</option>`).join('');
  const aniosMapa = Object.keys(M.desvio[S.cultivo] || {}).map(Number).sort((a, b) => b - a);
  $('f-anio-mapa').innerHTML = aniosMapa.map((a) => {
    const v = ICEN_ANIO[a];
    const tag = v > 1.0 ? ' · Niño moderado+' : v > 0.4 ? ' · Niño débil' : '';
    return `<option value="${a}" ${a === S.anioMapa ? 'selected' : ''}>${a}${tag}</option>`;
  }).join('');

  $('f-cultivo').onchange = (e) => { S.cultivo = e.target.value; actualizar(); };
  $('f-indicador').onchange = (e) => { S.indicador = e.target.value; actualizar(); };
  $('f-tipo').onchange = (e) => { S.tipo = e.target.value; actualizar(); };
  $('f-grupo').onchange = (e) => { S.grupo = e.target.value; grafRanking(); };
  $('f-anio-mapa').onchange = (e) => { S.anioMapa = +e.target.value; grafMapa(); };
  $('f-desde').oninput = (e) => { S.desde = Math.min(+e.target.value, S.hasta - 5); e.target.value = S.desde; actualizar(); };
  $('f-hasta').oninput = (e) => { S.hasta = Math.max(+e.target.value, S.desde + 5); e.target.value = S.hasta; actualizar(); };
  $('btn-descargar').onclick = descargarCSV;

  pintarAlerta();
  actualizar();
  $('g-ranking').on('plotly_click', (ev) => {
    S.cultivo = ev.points[0].y;
    $('f-cultivo').value = S.cultivo;
    actualizar();
  });
}

Promise.all([fetch('data/datos.json').then((r) => r.json()), fetch('data/mapa.json').then((r) => r.json())])
  .then(([d, m]) => { D = d; M = m; init(); })
  .catch((err) => {
    document.querySelector('main').insertAdjacentHTML('afterbegin', `<p class="texto">No se pudieron cargar los datos (${err}). Si abriste el archivo directamente, sírvelo con <code>python -m http.server</code> desde la carpeta web/.</p>`);
  });
