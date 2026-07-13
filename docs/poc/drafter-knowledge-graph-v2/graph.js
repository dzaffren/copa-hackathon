/* ============================================================
   Rulebook Radar — interactive knowledge graph (Obsidian-style)
   Self-contained canvas renderer — NO external library, so it
   works offline and over file://. Glowing nodes, curved links,
   drag-to-pan, scroll-to-zoom. Data is derived from the page's
   existing `paras` + `connections` structures (read-only).
   ============================================================ */
window.RR = window.RR || {};

RR.typeColors = {
  doc:      '#a882ff',
  para:     '#c4b5fd',
  standard: '#a78bfa',
  peer:     '#818cf8',
  act:      '#2dd4bf',
  internal: '#94a3b8',
  feedback: '#fb7185',
};

RR.verdictColors = {
  consensus: 'rgba(110,231,183,0.45)',
  conflict:  'rgba(252,165,165,0.50)',
  gap:       'rgba(253,186,116,0.45)',
  duplicate: 'rgba(125,211,252,0.42)',
  partial:   'rgba(252,211,77,0.42)',
};

/* Build {nodes, links} from the page's paras + connections objects. */
RR.buildGraphFromConnections = function (paras, connections) {
  const nodes = [], links = [], seen = {};
  const DOC = '__doc__';
  nodes.push({ id: DOC, label: 'AI Discussion Paper', type: 'doc' });
  seen[DOC] = 1;

  (paras || []).forEach(function (p) {
    const conns = (connections && connections[p.id]) || [];
    if (!p.analysed && conns.length === 0) return;
    const pid = 'para:' + p.id;
    if (!seen[pid]) { nodes.push({ id: pid, label: p.id + '  ' + (p.title || ''), type: 'para' }); seen[pid] = 1; }
    links.push({ source: DOC, target: pid, kind: 'structure' });
    conns.forEach(function (c) {
      const cid = 'src:' + p.id + ':' + c.id;
      nodes.push({ id: cid, label: c.src, type: c.type || 'internal', verdict: c.verdict, blocked: !!c.blocked });
      links.push({ source: pid, target: cid, kind: c.verdict || 'link' });
    });
  });
  return { nodes: nodes, links: links };
};

/* Render into a container. Returns { resize, fit, refresh, draw }. */
RR.initGraph = function (container, data) {
  container.innerHTML = '';
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'width:100%;height:100%;display:block;cursor:grab';
  container.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  const byId = {};
  data.nodes.forEach(function (n) { byId[n.id] = n; });
  const doc = data.nodes.find(function (n) { return n.type === 'doc'; });
  const paras = data.nodes.filter(function (n) { return n.type === 'para'; });
  const childrenOf = {};
  data.links.forEach(function (l) {
    const s = l.source.id || l.source, t = l.target.id || l.target;
    (childrenOf[s] = childrenOf[s] || []).push(t);
  });

  // ---- deterministic radial layout (world coords) ----
  if (doc) { doc.x = 0; doc.y = 0; }
  const R1 = 240;
  paras.forEach(function (p, i) {
    const a = (-Math.PI / 2) + i * (2 * Math.PI / Math.max(1, paras.length));
    p._a = a; p.x = Math.cos(a) * R1; p.y = Math.sin(a) * R1;
  });
  paras.forEach(function (p) {
    const kids = (childrenOf[p.id] || []).map(function (id) { return byId[id]; }).filter(function (n) { return n && n.type !== 'doc'; });
    const k = kids.length, spread = Math.min(1.5, 0.55 * k);
    kids.forEach(function (c, j) {
      const off = (k <= 1) ? 0 : ((j - (k - 1) / 2) / (k - 1)) * spread;
      const ang = p._a + off;
      c.x = p.x + Math.cos(ang) * 155; c.y = p.y + Math.sin(ang) * 155;
    });
  });

  // ---- view transform: world point (panX,panY) sits at canvas center ----
  let zoom = 1, panX = 0, panY = 0, W = 0, H = 0, dpr = 1;

  function resize() {
    const cw = container.clientWidth, ch = container.clientHeight;
    if (cw < 10 || ch < 10) return false;
    dpr = window.devicePixelRatio || 1;
    W = cw; H = ch;
    canvas.width = Math.round(cw * dpr); canvas.height = Math.round(ch * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return true;
  }
  function radiusOf(n) { return (n.type === 'doc' ? 15 : n.type === 'para' ? 10 : 7) * Math.max(0.6, Math.min(zoom, 1.6)); }
  function toScreen(x, y) { return [W / 2 + (x - panX) * zoom, H / 2 + (y - panY) * zoom]; }

  function fit() {
    if (!W || !H) return;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    data.nodes.forEach(function (n) {
      if (n.x < minX) minX = n.x; if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y; if (n.y > maxY) maxY = n.y;
    });
    const spanX = (maxX - minX) || 1, spanY = (maxY - minY) || 1, pad = 110;
    zoom = Math.max(0.3, Math.min(Math.min((W - pad) / spanX, (H - pad) / spanY), 2));
    panX = (minX + maxX) / 2; panY = (minY + maxY) / 2;
    draw();
  }

  function draw() {
    if (!W || !H) return;
    ctx.clearRect(0, 0, W, H);
    // links
    data.links.forEach(function (l) {
      const s = byId[l.source.id || l.source], t = byId[l.target.id || l.target];
      if (!s || !t) return;
      const a = toScreen(s.x, s.y), b = toScreen(t.x, t.y);
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]);
      ctx.strokeStyle = l.kind === 'structure' ? 'rgba(168,130,255,0.30)' : (RR.verdictColors[l.kind] || 'rgba(168,130,255,0.18)');
      ctx.lineWidth = l.kind === 'structure' ? 1.6 : 1.1;
      ctx.stroke();
    });
    // nodes
    data.nodes.forEach(function (n) {
      const s = toScreen(n.x, n.y), x = s[0], y = s[1], r = radiusOf(n);
      const color = RR.typeColors[n.type] || '#94a3b8';
      const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3);
      g.addColorStop(0, color + '55'); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r * 3, 0, 6.2832); ctx.fill();
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fillStyle = color; ctx.fill();
      ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(255,255,255,0.30)'; ctx.stroke();
      if (n.blocked) {
        ctx.setLineDash([2, 2]); ctx.strokeStyle = 'rgba(253,186,116,0.9)';
        ctx.beginPath(); ctx.arc(x, y, r + 3, 0, 6.2832); ctx.stroke(); ctx.setLineDash([]);
      }
      if (n.type === 'doc' || n.type === 'para' || zoom > 0.85) {
        let label = n.label || ''; const max = n.type === 'doc' ? 30 : 26;
        if (label.length > max) label = label.slice(0, max - 1) + '…';
        ctx.font = (n.type === 'doc' ? '600 13px ' : '500 12px ') + 'Inter, system-ui, sans-serif';
        ctx.textAlign = 'center'; ctx.textBaseline = 'top';
        ctx.fillStyle = n.type === 'doc' ? 'rgba(230,224,255,0.95)' : 'rgba(214,214,214,0.85)';
        ctx.fillText(label, x, y + r + 4);
      }
    });
  }

  // ---- interactions ----
  let dragging = false, lx = 0, ly = 0;
  canvas.addEventListener('mousedown', function (e) { dragging = true; lx = e.clientX; ly = e.clientY; canvas.style.cursor = 'grabbing'; });
  window.addEventListener('mouseup', function () { dragging = false; canvas.style.cursor = 'grab'; });
  window.addEventListener('mousemove', function (e) {
    if (!dragging) return;
    panX -= (e.clientX - lx) / zoom; panY -= (e.clientY - ly) / zoom;
    lx = e.clientX; ly = e.clientY; draw();
  });
  canvas.addEventListener('mousemove', function (e) {
    if (dragging) return;
    const rect = canvas.getBoundingClientRect(), mx = e.clientX - rect.left, my = e.clientY - rect.top;
    let hit = false;
    for (let i = 0; i < data.nodes.length; i++) {
      const n = data.nodes[i], s = toScreen(n.x, n.y), r = radiusOf(n);
      if ((mx - s[0]) * (mx - s[0]) + (my - s[1]) * (my - s[1]) < (r + 4) * (r + 4)) { hit = true; break; }
    }
    canvas.style.cursor = hit ? 'pointer' : 'grab';
  });
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect(), mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const wx = panX + (mx - W / 2) / zoom, wy = panY + (my - H / 2) / zoom;
    zoom = Math.max(0.25, Math.min(zoom * (e.deltaY < 0 ? 1.12 : 0.89), 3));
    panX = wx - (mx - W / 2) / zoom; panY = wy - (my - H / 2) / zoom;
    draw();
  }, { passive: false });

  // ---- boot: retry until the container has a real size, then fit ----
  let tries = 0;
  (function ensure() { if (resize()) { fit(); return; } if (tries++ < 40) setTimeout(ensure, 80); })();
  if (window.ResizeObserver) { try { new ResizeObserver(function () { if (resize()) draw(); }).observe(container); } catch (e) {} }
  window.addEventListener('resize', function () { if (resize()) draw(); });

  return { resize: resize, fit: fit, refresh: function () { if (resize()) fit(); }, draw: draw };
};
