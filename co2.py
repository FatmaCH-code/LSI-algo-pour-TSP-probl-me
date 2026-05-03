# -*- coding: utf-8 -*-


import sys, math, webbrowser, os, json

# ── distance matrix ───────────────────────────────────────────
M = [
    [0,12,26,11,47,23,46,44,52,35],
    [12,0,44,20,49,43,90,92,27,91],
    [26,44,0,50,35,21,11,82,1,92],
    [11,20,50,0,5,57,69,62,74,91],
    [47,49,35,5,0,61,89,26,28,80],
    [23,43,21,57,61,0,11,8,73,36],
    [46,90,11,69,89,11,0,16,55,61],
    [44,92,82,62,26,8,16,0,83,71],
    [52,27,1,74,28,73,55,83,0,74],
    [35,91,92,91,80,36,61,71,74,0],
]
N = len(M)

# ── core functions ────────────────────────────────────────────
def cost(s):
    return sum(M[s[i]][s[i+1]] for i in range(len(s)-1)) + M[s[-1]][s[0]]

def neighbors(s):
    nb = []
    for i in range(len(s)):
        for j in range(i+1, len(s)):
            n = s[:]
            n[i], n[j] = n[j], n[i]
            nb.append({'sol': n, 'move': [i, j], 'c': cost(n)})
    return nb

def descent(s0):
    cur, cc = s0[:], cost(s0)
    improved = True
    history_rli = [{'iter': 0, 'sol': cur[:], 'c': cc}]
    step = 0
    while improved:
        improved = False
        best, bc = None, cc
        best_move = None
        for nb in neighbors(cur):
            if nb['c'] < bc:
                bc, best, best_move = nb['c'], nb['sol'][:], nb['move']
        if best:
            cur, cc, improved = best, bc, True
            step += 1
            history_rli.append({'iter': step, 'sol': cur[:], 'c': cc, 'move': best_move})
    return cur, cc, history_rli

def tabu_search(s0, tabu_size=10, max_iter=100):
    cur, cc       = s0[:], cost(s0)
    best, bc      = cur[:], cc
    tabu_list     = []
    history       = []
    nb_log        = []
    tabu_snaps    = []

    for it in range(1, max_iter + 1):
        nbs = neighbors(cur)
        best_nb, best_nbc, best_mv, used_asp = None, math.inf, None, False

        for nb in nbs:
            mv = nb['move']
            is_tabu = any(
                (t == mv or t == [mv[1], mv[0]]) for t in tabu_list
            )
            if is_tabu and nb['c'] >= bc:
                continue
            if nb['c'] < best_nbc:
                best_nbc, best_nb, best_mv, used_asp = nb['c'], nb['sol'][:], mv, is_tabu

        if best_nb is None:
            for nb in nbs:
                if nb['c'] < best_nbc:
                    best_nbc, best_nb, best_mv = nb['c'], nb['sol'][:], nb['move']

        cur, cc = best_nb[:], best_nbc
        tabu_list.append(best_mv)
        if len(tabu_list) > tabu_size:
            tabu_list.pop(0)
        if cc < bc:
            best, bc = cur[:], cc

        snap_before = [t[:] for t in tabu_list[:-1]]

        nb_annotated = sorted([
            {
                'sol': nb['sol'],
                'move': nb['move'],
                'c': nb['c'],
                'tabu': any(
                    (t == nb['move'] or t == [nb['move'][1], nb['move'][0]])
                    for t in snap_before
                ),
                'chosen': nb['move'] == best_mv
            }
            for nb in nbs
        ], key=lambda x: x['c'])

        history.append({
            'iter': it, 'cur': cur[:], 'cc': cc,
            'best': best[:], 'bc': bc,
            'move': best_mv, 'aspiration': used_asp
        })
        nb_log.append(nb_annotated)
        tabu_snaps.append([t[:] for t in tabu_list])

    return best, bc, history, nb_log, tabu_snaps

# ── run algorithm ─────────────────────────────────────────────
s0       = list(range(N))
init_c   = cost(s0)
desc_sol, desc_c, rli_history = descent(s0)
tabu_sol, tabu_c, history, nb_log, tabu_snaps = tabu_search(s0, 10, 100)
gain     = init_c - tabu_c
pct      = round(gain / init_c * 100)
rli_gain = init_c - desc_c
rli_pct  = round(rli_gain / init_c * 100)

# ── serialise data for JS ─────────────────────────────────────
js_history    = json.dumps(history)
js_nb_log     = json.dumps(nb_log)
js_tabu_snaps = json.dumps(tabu_snaps)
js_tabu_sol   = json.dumps(tabu_sol)
js_desc_sol   = json.dumps(desc_sol)
js_s0         = json.dumps(s0)
js_rli_history = json.dumps(rli_history)

# ── build HTML ────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Tabu Search — TSP</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',sans-serif;background:#f4f5f7;color:#1a1a2e;min-height:100vh}}
  .topbar{{background:#1a1a2e;color:#fff;padding:18px 32px;display:flex;align-items:center;gap:16px}}
  .topbar h1{{font-size:18px;font-weight:600;letter-spacing:.5px}}
  .topbar .badge{{background:#2ecc71;color:#fff;font-size:11px;padding:3px 10px;border-radius:20px;font-weight:600}}
  .main{{max-width:1100px;margin:0 auto;padding:28px 20px}}
  .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}}
  .card{{background:#fff;border-radius:12px;padding:18px 20px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
  .card .lbl{{font-size:11px;color:#888;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px}}
  .card .val{{font-size:28px;font-weight:700;color:#1a1a2e}}
  .card .sub{{font-size:11px;color:#aaa;margin-top:3px}}
  .card.green .val{{color:#27ae60}}
  .card.red .val{{color:#e74c3c}}
  .section{{background:#fff;border-radius:12px;padding:22px 24px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:20px}}
  .section-title{{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#888;margin-bottom:16px}}
  .chart-wrap{{position:relative;width:100%;height:220px}}
  .route{{display:flex;flex-wrap:wrap;gap:6px;align-items:center}}
  .route-city{{background:#1a1a2e;color:#fff;border-radius:6px;padding:4px 12px;font-size:13px;font-weight:600}}
  .route-arrow{{color:#bbb;font-size:12px}}
  .tabs{{display:flex;gap:8px;margin-bottom:16px}}
  .tab{{padding:7px 18px;border-radius:8px;border:1.5px solid #ddd;background:#fff;font-size:13px;font-weight:500;cursor:pointer;color:#555;transition:all .15s}}
  .tab:hover{{border-color:#1a1a2e;color:#1a1a2e}}
  .tab.active{{background:#1a1a2e;color:#fff;border-color:#1a1a2e}}
  .slider-row{{display:flex;align-items:center;gap:12px;margin-bottom:14px}}
  .slider-row label{{font-size:13px;color:#666;min-width:70px}}
  .slider-row input[type=range]{{flex:1;accent-color:#1a1a2e}}
  .slider-row .val-display{{font-size:15px;font-weight:700;min-width:36px;color:#1a1a2e}}
  .status-bar{{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:14px;padding:10px 14px;background:#f8f9fa;border-radius:8px}}
  .status-item{{font-size:12px;color:#666}}
  .status-item b{{color:#1a1a2e;font-weight:600}}
  .nb-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;max-height:340px;overflow-y:auto;padding-right:4px}}
  .nb-grid::-webkit-scrollbar{{width:4px}}
  .nb-grid::-webkit-scrollbar-thumb{{background:#ddd;border-radius:4px}}
  .nb-card{{border-radius:8px;padding:10px 12px;border:1.5px solid #eee;background:#fafafa}}
  .nb-card.chosen{{border-color:#27ae60;background:#f0faf4}}
  .nb-card.tabu{{border-color:#e74c3c;background:#fff5f5}}
  .nb-card.aspire{{border-color:#f39c12;background:#fffbf0}}
  .nb-card .nb-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}}
  .nb-card .nb-swap{{font-size:11px;font-weight:600;color:#555}}
  .nb-card .nb-cost{{font-size:20px;font-weight:700;color:#1a1a2e}}
  .nb-card .nb-sol{{font-size:10px;color:#aaa;margin-top:3px;word-break:break-all}}
  .pill{{font-size:10px;padding:2px 8px;border-radius:20px;font-weight:600}}
  .pill-green{{background:#e8f8f0;color:#27ae60}}
  .pill-red{{background:#fdecea;color:#e74c3c}}
  .pill-amber{{background:#fef9e7;color:#d4851a}}
  .pill-gray{{background:#f0f0f0;color:#888}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{background:#f4f5f7;color:#888;font-weight:600;font-size:11px;letter-spacing:.05em;text-transform:uppercase;padding:9px 12px;text-align:left;position:sticky;top:0}}
  td{{padding:7px 12px;border-bottom:1px solid #f0f0f0;color:#1a1a2e}}
  tr.best-row td{{background:#f0faf4;color:#27ae60;font-weight:600}}
  tr:hover td{{background:#fafafa}}
  .table-wrap{{max-height:380px;overflow-y:auto;border-radius:8px;border:1px solid #eee}}
  .tabu-chips{{display:flex;flex-wrap:wrap;gap:6px}}
  .tabu-chip{{background:#fdecea;color:#c0392b;border:1px solid #f5b7b1;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600}}
  .legend{{display:flex;gap:16px;font-size:11px;color:#888;margin-bottom:12px}}
  .legend-dot{{width:12px;height:12px;border-radius:2px;display:inline-block;margin-right:4px;vertical-align:middle}}
</style>
</head>
<body>

<div class="topbar">
  <h1>Tabu Search  ·  TSP  ·  10 villes</h1>
  <span class="badge">f* = {tabu_c}</span>
</div>

<div class="main">

  <div class="cards">
    <div class="card">
      <div class="lbl">Solution initiale</div>
      <div class="val">{init_c}</div>
      <div class="sub">f = cout total</div>
    </div>
    <div class="card">
      <div class="lbl">Apres descente</div>
      <div class="val">{desc_c}</div>
      <div class="sub">minimum local</div>
    </div>
    <div class="card green">
      <div class="lbl">Meilleure tabou</div>
      <div class="val">{tabu_c}</div>
      <div class="sub">apres 100 iter</div>
    </div>
    <div class="card green">
      <div class="lbl">Amelioration</div>
      <div class="val">-{gain} ({pct}%)</div>
      <div class="sub">vs initiale</div>
    </div>
  </div>

  <!-- ══ RLI / LSI COMPARISON SECTION ══ -->
  <div class="section" style="border-left: 4px solid #3498db;">
    <div class="section-title" style="color:#2980b9;">&#9654; Comparaison RLI / LSI (Descente)</div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:18px;">

      <!-- RLI summary -->
      <div style="background:#f0f7ff;border-radius:10px;padding:16px 18px;">
        <div style="font-size:11px;font-weight:700;color:#2980b9;letter-spacing:.07em;text-transform:uppercase;margin-bottom:10px;">RLI — Résultat Descente</div>
        <div style="display:flex;gap:18px;flex-wrap:wrap;">
          <div>
            <div style="font-size:11px;color:#888;">Coût initial</div>
            <div style="font-size:22px;font-weight:700;color:#1a1a2e;">{init_c}</div>
          </div>
          <div style="font-size:22px;color:#bbb;align-self:center;">→</div>
          <div>
            <div style="font-size:11px;color:#888;">Minimum local</div>
            <div style="font-size:22px;font-weight:700;color:#2980b9;">{desc_c}</div>
          </div>
          <div style="font-size:22px;color:#bbb;align-self:center;">→</div>
          <div>
            <div style="font-size:11px;color:#888;">Amélioration</div>
            <div style="font-size:22px;font-weight:700;color:#27ae60;">-{rli_gain} ({rli_pct}%)</div>
          </div>
        </div>
        <div style="margin-top:10px;font-size:11px;color:#888;">Nombre d'étapes : <b id="rli-steps" style="color:#1a1a2e;"></b> &nbsp;|&nbsp; Bloqué au minimum local (aucun voisin améliorant)</div>
      </div>

      <!-- Tabu vs RLI -->
      <div style="background:#f0fff4;border-radius:10px;padding:16px 18px;">
        <div style="font-size:11px;font-weight:700;color:#27ae60;letter-spacing:.07em;text-transform:uppercase;margin-bottom:10px;">Tabou vs RLI — Gain supplémentaire</div>
        <div style="display:flex;gap:18px;flex-wrap:wrap;align-items:center;">
          <div>
            <div style="font-size:11px;color:#888;">RLI s'arrête à</div>
            <div style="font-size:22px;font-weight:700;color:#e74c3c;">{desc_c}</div>
          </div>
          <div style="font-size:22px;color:#bbb;">→</div>
          <div>
            <div style="font-size:11px;color:#888;">Tabou trouve</div>
            <div style="font-size:22px;font-weight:700;color:#27ae60;">{tabu_c}</div>
          </div>
          <div style="font-size:22px;color:#bbb;">→</div>
          <div>
            <div style="font-size:11px;color:#888;">Gain extra Tabou</div>
            <div style="font-size:22px;font-weight:700;color:#27ae60;">-{desc_c - tabu_c}</div>
          </div>
        </div>
        <div style="margin-top:10px;font-size:11px;color:#888;">Tabou échappe au minimum local grâce à la liste tabou &amp; aspiration ✓</div>
      </div>
    </div>

    <!-- RLI route step by step -->
    <div style="font-size:11px;font-weight:700;color:#555;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">Étapes RLI (chaque amélioration)</div>
    <div id="rli-steps-list" style="display:flex;flex-direction:column;gap:6px;max-height:220px;overflow-y:auto;padding-right:4px;"></div>

    <!-- RLI final route -->
    <div style="margin-top:14px;">
      <div style="font-size:11px;font-weight:700;color:#2980b9;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">Solution finale RLI (minimum local)</div>
      <div class="route" id="rli-route"></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Evolution du cout</div>
    <div class="legend">
      <span><span class="legend-dot" style="background:#1a1a2e"></span>f meilleur</span>
      <span><span class="legend-dot" style="background:#ccc;border:1px dashed #999"></span>f courant</span>
    </div>
    <div class="chart-wrap"><canvas id="evoChart" role="img" aria-label="Evolution du cout"></canvas></div>
  </div>

  <div class="section">
    <div class="section-title">Meilleure solution trouvee</div>
    <div class="route" id="best-route"></div>
  </div>

  <div class="section">
    <div class="tabs">
      <button class="tab active" onclick="showTab('neighbors')">Voisins par iteration</button>
      <button class="tab" onclick="showTab('history')">Historique complet</button>
      <button class="tab" onclick="showTab('tabu')">Liste tabou</button>
    </div>

    <div id="tab-neighbors">
      <div class="slider-row">
        <label>Iteration</label>
        <input type="range" min="1" max="100" value="1" step="1" id="iter-slider" oninput="onIter(this.value)">
        <span class="val-display" id="iter-val">1</span>
      </div>
      <div class="status-bar" id="iter-status"></div>
      <div class="nb-grid" id="nb-grid"></div>
    </div>

    <div id="tab-history" style="display:none">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Iter</th><th>f courant</th><th>f meilleur</th><th>Mouvement</th><th>Tabu</th><th>Aspiration</th><th>Statut</th></tr></thead>
          <tbody id="hist-body"></tbody>
        </table>
      </div>
    </div>

    <div id="tab-tabu" style="display:none">
      <div class="slider-row">
        <label>Iteration</label>
        <input type="range" min="1" max="100" value="1" step="1" id="tabu-slider" oninput="onTabuSlider(this.value)">
        <span class="val-display" id="tabu-val">1</span>
      </div>
      <p style="font-size:12px;color:#888;margin-bottom:10px">Mouvements interdits a cette iteration :</p>
      <div class="tabu-chips" id="tabu-chips"></div>
    </div>
  </div>

</div>

<script>
const history    = {js_history};
const nbLog      = {js_nb_log};
const tabuSnaps  = {js_tabu_snaps};
const tabuSol    = {js_tabu_sol};
const descSol    = {js_desc_sol};
const s0         = {js_s0};
const initC      = {init_c};
const rliHistory = {js_rli_history};

// ── RLI steps rendering ────────────────────────────────────
document.getElementById('rli-steps').textContent = (rliHistory.length - 1);

const rliList = document.getElementById('rli-steps-list');
rliHistory.forEach((step, i) => {{
  const div = document.createElement('div');
  div.style.cssText = 'display:flex;align-items:center;gap:10px;padding:7px 12px;border-radius:7px;background:' + (i===0 ? '#f4f5f7' : (i===rliHistory.length-1 ? '#e8f8f0' : '#fff')) + ';border:1px solid #eee;';
  const badge = i===0 ? '🔵 Init' : (i===rliHistory.length-1 ? '✅ Final' : `→ Étape ${{i}}`);
  const moveStr = step.move ? `swap(${{step.move[0]}},${{step.move[1]}})` : '—';
  div.innerHTML = `
    <span style="font-size:11px;font-weight:700;color:#2980b9;min-width:70px;">${{badge}}</span>
    <span style="font-size:13px;font-weight:700;color:#1a1a2e;min-width:36px;">${{step.c}}</span>
    <span style="font-size:11px;color:#aaa;min-width:90px;">${{moveStr}}</span>
    <span style="font-size:10px;color:#bbb;">[${{step.sol.join(' → ')}}]</span>
  `;
  rliList.appendChild(div);
}});

// ── RLI final route ────────────────────────────────────────
const rliRouteEl = document.getElementById('rli-route');
descSol.forEach((v, i) => {{
  let c = document.createElement('span');
  c.className = 'route-city';
  c.style.background = '#2980b9';
  c.textContent = v;
  rliRouteEl.appendChild(c);
  let a = document.createElement('span');
  a.className = 'route-arrow';
  a.textContent = '→';
  rliRouteEl.appendChild(a);
}});
let closing = document.createElement('span');
closing.className = 'route-city';
closing.style.cssText = 'opacity:.4;background:#2980b9';
closing.textContent = descSol[0];
rliRouteEl.appendChild(closing);

// ── chart ──────────────────────────────────────────────────
const ctx = document.getElementById('evoChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: history.map(h => h.iter),
    datasets: [
      {{
        label: 'f courant',
        data: history.map(h => h.cc),
        borderColor: '#bbb',
        borderWidth: 1.5,
        borderDash: [5,3],
        pointRadius: 0,
        tension: 0.3,
        fill: false
      }},
      {{
        label: 'f meilleur',
        data: history.map(h => h.bc),
        borderColor: '#1a1a2e',
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.3,
        fill: false
      }}
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 10, color: '#aaa', font: {{size: 11}} }}, grid: {{ color: '#f0f0f0' }} }},
      y: {{ ticks: {{ color: '#aaa', font: {{size: 11}} }}, grid: {{ color: '#f0f0f0' }} }}
    }}
  }}
}});

// ── best route ─────────────────────────────────────────────
function renderRoute(sol, el) {{
  el.innerHTML = '';
  sol.forEach((v, i) => {{
    let c = document.createElement('span');
    c.className = 'route-city'; c.textContent = v; el.appendChild(c);
    let a = document.createElement('span');
    a.className = 'route-arrow'; a.textContent = '→'; el.appendChild(a);
  }});
  let c = document.createElement('span');
  c.className = 'route-city'; c.style.opacity = '.4'; c.textContent = sol[0];
  document.getElementById('best-route').appendChild(c);
}}
renderRoute(tabuSol, document.getElementById('best-route'));

// ── history table ──────────────────────────────────────────
const tbody = document.getElementById('hist-body');
history.forEach((h, i) => {{
  const prev_bc = i > 0 ? history[i-1].bc : initC + 1;
  const isNew   = h.bc < prev_bc;
  const tr      = document.createElement('tr');
  if (isNew) tr.className = 'best-row';
  const asp  = h.aspiration ? '<span class="pill pill-amber">OUI</span>' : '—';
  const prevSnap = i > 0 ? tabuSnaps[i-1] : [];
  const wasTabu  = prevSnap.some(t => (t[0]===h.move[0]&&t[1]===h.move[1])||(t[0]===h.move[1]&&t[1]===h.move[0]));
  const tabuFlag = wasTabu ? '<span class="pill pill-red">OUI</span>' : '—';
  const stat = isNew
    ? '<span class="pill pill-green">new best</span>'
    : h.cc > (i>0 ? history[i-1].cc : initC)
      ? '<span class="pill pill-gray">hausse</span>'
      : '<span class="pill pill-gray">ameliore</span>';
  tr.innerHTML = `<td>${{h.iter}}</td><td>${{h.cc}}</td><td>${{h.bc}}</td><td>swap(${{h.move[0]}},${{h.move[1]}})</td><td>${{tabuFlag}}</td><td>${{asp}}</td><td>${{stat}}</td>`;
  tbody.appendChild(tr);
}});

// ── neighbors ──────────────────────────────────────────────
function onIter(v) {{
  document.getElementById('iter-val').textContent = v;
  const idx = parseInt(v) - 1;
  const h   = history[idx];
  document.getElementById('iter-status').innerHTML =
    `<span class="status-item">Iter <b>${{h.iter}}</b></span>
     <span class="status-item">Solution courante <b>${{h.cur.join('-')}}</b></span>
     <span class="status-item">f courant <b>${{h.cc}}</b></span>
     <span class="status-item">f meilleur <b>${{h.bc}}</b></span>
     <span class="status-item">Mouvement choisi <b>swap(${{h.move[0]}},${{h.move[1]}})</b></span>`;
  const grid = document.getElementById('nb-grid');
  grid.innerHTML = '';
  nbLog[idx].forEach(nb => {{
    let cls = 'nb-card';
    let pill = '';
    if (nb.chosen && !nb.tabu)  {{ cls += ' chosen';  pill = '<span class="pill pill-green">choisi</span>'; }}
    else if (nb.chosen && nb.tabu) {{ cls += ' aspire'; pill = '<span class="pill pill-amber">aspiration</span>'; }}
    else if (nb.tabu)            {{ cls += ' tabu';   pill = '<span class="pill pill-red">tabou</span>'; }}
    const d = document.createElement('div');
    d.className = cls;
    d.innerHTML = `<div class="nb-header"><span class="nb-swap">swap(${{nb.move[0]}},${{nb.move[1]}})</span>${{pill}}</div>
                   <div class="nb-cost">${{nb.c}}</div>
                   <div class="nb-sol">${{JSON.stringify(nb.sol)}}</div>`;
    grid.appendChild(d);
  }});
}}
onIter(1);

// ── tabu list ──────────────────────────────────────────────
function onTabuSlider(v) {{
  document.getElementById('tabu-val').textContent = v;
  const snap = tabuSnaps[parseInt(v) - 1];
  const el   = document.getElementById('tabu-chips');
  el.innerHTML = snap.length === 0
    ? '<span style="font-size:12px;color:#aaa">vide</span>'
    : snap.map(t => `<span class="tabu-chip">swap(${{t[0]}},${{t[1]}})</span>`).join('');
}}
onTabuSlider(1);

// ── tabs ───────────────────────────────────────────────────
function showTab(name) {{
  document.getElementById('tab-neighbors').style.display = name==='neighbors' ? 'block' : 'none';
  document.getElementById('tab-history').style.display   = name==='history'   ? 'block' : 'none';
  document.getElementById('tab-tabu').style.display      = name==='tabu'      ? 'block' : 'none';
  document.querySelectorAll('.tab').forEach((t, i) => {{
    t.classList.toggle('active', ['neighbors','history','tabu'][i] === name);
  }});
}}
</script>
</body>
</html>"""

# ── write & open ──────────────────────────────────────────────
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tabu_tsp_dashboard.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard generated: {out}")
print("Opening in browser...")
webbrowser.open(f'file:///{out}')