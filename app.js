const cards = document.getElementById('cards'), upd = document.getElementById('upd');
let updated = null;
const ago = t => { const m = Math.round((Date.now() - new Date(t)) / 60000); return m < 2 ? 'just now' : m < 90 ? m + ' min ago' : Math.round(m / 60) + ' h ago'; };
const el = (c, x) => { const e = document.createElement('div'); e.className = c; e.textContent = x; return e; };
function tick() { if (updated) upd.textContent = 'Updated ' + ago(updated); }
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
      if (g.stale) c.append(el('stale', 'Couldn’t refresh this one. Showing the last known value.'));
      return c;
    }));
    tick();
  } catch (e) { upd.textContent = 'Couldn’t load stats.'; }
}
load(); setInterval(load, 60000); setInterval(tick, 30000);
