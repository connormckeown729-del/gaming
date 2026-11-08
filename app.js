const cards = document.getElementById('cards'), upd = document.getElementById('upd');
let updated = null, data = null, current = location.hash.slice(1) || null;
const ui = {};
const ago = t => { const m = Math.round((Date.now() - new Date(t)) / 60000); return m < 2 ? 'just now' : m < 90 ? m + ' min ago' : Math.round(m / 60) + ' h ago'; };
const mk = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const el = (c, x) => mk('div', c, x);
function tick() { if (updated) upd.textContent = 'Updated ' + ago(updated); }

function tableEl(T, key) {
  const st = ui[key] || (ui[key] = { open: false, col: -1, dir: 1 });
  const det = mk('details'); det.open = st.open;
  det.addEventListener('toggle', () => { st.open = det.open; });
  det.append(mk('summary', '', T.title));
  const wrap = el('scroll'), tb = mk('table'), head = mk('tr'), body = mk('tbody');
  const rows = T.rows.slice();
  const cell = v => v == null ? '-' : typeof v === 'number' ? v.toLocaleString() : v;
  const sort = () => { if (st.col < 0) return; rows.sort((a, b) => { const x = a[st.col], y = b[st.col]; return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))) * st.dir; }); };
  const draw = () => body.replaceChildren(...rows.map(r => { const tr = mk('tr'); r.forEach(v => tr.append(mk('td', '', cell(v)))); return tr; }));
  T.columns.forEach((h, i) => {
    const th = mk('th', '', h);
    th.onclick = () => { st.dir = st.col === i ? -st.dir : (typeof rows[0]?.[i] === 'number' ? -1 : 1); st.col = i; sort(); draw(); };
    head.append(th);
  });
  const thead = mk('thead'); thead.append(head); tb.append(thead, body);
  sort(); draw(); wrap.append(tb); det.append(wrap);
  return det;
}

function cardEl(g, key) {
  const c = mk('article', 'card');
  c.append(el('t', g.title + (g.metric ? ' · ' + g.metric : '')),
           el('v', g.value == null ? '—' : g.value.toLocaleString()),
           el('n', g.name || ''), el('s', g.sub || ''));
  if (g.details && g.details.length) {
    const dl = mk('dl');
    g.details.forEach(([k, v]) => { const r = mk('div'); r.append(mk('dt', '', k), mk('dd', '', v)); dl.append(r); });
    c.append(dl);
  }
  if (g.top && g.top.length) {
    c.append(el('tt', g.top_title || ''));
    const ol = mk('ol'); g.top.forEach(x => ol.append(mk('li', '', x))); c.append(ol);
  }
  if (g.table) c.append(tableEl(g.table, key));
  if (g.stale) c.append(el('stale', 'Couldn’t refresh this one. Showing the last known value.'));
  return c;
}

function render() {
  const keys = Object.keys(data.games);
  if (!keys.includes(current)) current = keys[0];
  const bar = el('tabs'); bar.setAttribute('role', 'tablist');
  keys.forEach(k => {
    const g = data.games[k], b = mk('button', 'tabbtn');
    b.setAttribute('role', 'tab'); b.setAttribute('aria-selected', k === current);
    b.append(mk('span', 'tn', g.title), mk('span', 'tv', g.value == null ? '—' : g.value.toLocaleString()));
    b.onclick = () => { current = k; history.replaceState(null, '', '#' + k); render(); };
    bar.append(b);
  });
  cards.replaceChildren(bar, cardEl(data.games[current], current));
}

async function load() {
  try {
    const D = await (await fetch('stats.json?' + Date.now(), { cache: 'no-store' })).json();
    updated = D.updated;
    if (!data || data.updated !== D.updated) { data = D; render(); }
    tick();
  } catch (e) { upd.textContent = 'Couldn’t load stats.'; }
}
load(); setInterval(load, 60000); setInterval(tick, 30000);
