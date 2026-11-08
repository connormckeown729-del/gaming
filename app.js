const cards = document.getElementById('cards'), upd = document.getElementById('upd');
let updated = null;
const ago = t => { const m = Math.round((Date.now() - new Date(t)) / 60000); return m < 2 ? 'just now' : m < 90 ? m + ' min ago' : Math.round(m / 60) + ' h ago'; };
const el = (c, x) => { const e = document.createElement('div'); e.className = c; e.textContent = x; return e; };
function tick() { if (updated) upd.textContent = 'Updated ' + ago(updated); }
function tableEl(T) {
  const det = document.createElement('details'), sm = document.createElement('summary');
  sm.textContent = T.title; det.append(sm);
  const wrap = document.createElement('div'); wrap.className = 'scroll';
  const tb = document.createElement('table'), head = document.createElement('tr'), body = document.createElement('tbody');
  let rows = T.rows.slice(), dir = -1, last = -1;
  const cell = v => v == null ? '-' : typeof v === 'number' ? v.toLocaleString() : v;
  const draw = () => { body.replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); r.forEach(v => { const td = document.createElement('td'); td.textContent = cell(v); tr.append(td); }); return tr; })); };
  T.columns.forEach((h, i) => {
    const th = document.createElement('th'); th.textContent = h;
    th.onclick = () => {
      dir = last === i ? -dir : (typeof rows[0]?.[i] === 'number' ? -1 : 1); last = i;
      rows.sort((a, b) => { const x = a[i], y = b[i]; return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))) * dir; });
      draw();
    };
    head.append(th);
  });
  const th = document.createElement('thead'); th.append(head); tb.append(th, body); draw();
  wrap.append(tb); det.append(wrap); return det;
}
async function load() {
  try {
    const D = await (await fetch('stats.json?' + Date.now(), { cache: 'no-store' })).json();
    updated = D.updated;
    cards.replaceChildren(...Object.values(D.games).map(g => {
      const c = document.createElement('article'); c.className = 'card';
      c.append(el('t', g.title + (g.metric ? ' · ' + g.metric : '')),
               el('v', g.value == null ? '—' : g.value.toLocaleString()),
               el('n', g.name || ''), el('s', g.sub || ''));
      if (g.details && g.details.length) {
        const dl = document.createElement('dl');
        g.details.forEach(([k, v]) => { const r = document.createElement('div'), a = document.createElement('dt'), b = document.createElement('dd'); a.textContent = k; b.textContent = v; r.append(a, b); dl.append(r); });
        c.append(dl);
      }
      if (g.top && g.top.length) {
        c.append(el('tt', g.top_title || ''));
        const ol = document.createElement('ol');
        g.top.forEach(x => { const li = document.createElement('li'); li.textContent = x; ol.append(li); });
        c.append(ol);
      }
      if (g.table) c.append(tableEl(g.table));
      if (g.stale) c.append(el('stale', 'Couldn’t refresh this one. Showing the last known value.'));
      return c;
    }));
    tick();
  } catch (e) { upd.textContent = 'Couldn’t load stats.'; }
}
load(); setInterval(load, 60000); setInterval(tick, 30000);
