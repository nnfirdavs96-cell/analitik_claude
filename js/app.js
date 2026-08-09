// ============================================================
// RackMap · клиентское приложение
// ============================================================
(function () {
  'use strict';

  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  function switchScreen(name) {
    $$('#tabs .tab').forEach(t => t.classList.toggle('active', t.dataset.screen === name));
    $$('.screen').forEach(s => s.classList.toggle('active', s.dataset.screen === name));
    if (name === 'topology') renderTopology();
  }
  $$('#tabs .tab').forEach(t => t.addEventListener('click', () => switchScreen(t.dataset.screen)));
  $$('[data-goto]').forEach(a => a.addEventListener('click', e => {
    e.preventDefault(); switchScreen(a.dataset.goto);
  }));

  function tickClock() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    $('#clock').textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }
  tickClock(); setInterval(tickClock, 1000);

  // ============ Обзор ============
  function renderFloorplan() {
    const root = $('#floorplan');
    $$('.rack-tile', root).forEach(el => el.remove());

    DATA.racks.forEach(r => {
      const tile = document.createElement('div');
      tile.className = `rack-tile ${r.status}`;
      tile.innerHTML = `
        <div class="rack-tile-head">
          <b>${r.name}</b><span class="id">${r.id}</span>
        </div>
        <div class="rack-mini">${miniRackContent()}</div>
        <div class="rack-tile-foot">
          <span class="mono">${r.online}/${r.devices}</span>
          <span class="mono">${r.temp}</span>
        </div>
      `;
      tile.addEventListener('mouseenter', e => showRackPop(e, r));
      tile.addEventListener('mousemove', moveRackPop);
      tile.addEventListener('mouseleave', hideRackPop);
      tile.addEventListener('click', () => {
        selectRack(r.id);
        switchScreen('rack');
      });
      root.appendChild(tile);
    });

    const add = document.createElement('div');
    add.className = 'rack-tile add';
    add.textContent = '+ Добавить стойку';
    add.addEventListener('click', openModal);
    root.appendChild(add);
  }

  function miniRackContent() {
    const layout = [
      { kind:'router', label:'router' },
      { kind:'switch', label:'switch' },
      { kind:'server', label:'server' },
      { kind:'server', label:'server' },
      { kind:'empty',  label:'' },
      { kind:'patch',  label:'patch' },
      { kind:'empty',  label:'' },
      { kind:'ups',    label:'ups' },
    ];
    return layout.map(u => `<div class="rack-mini-u ${u.kind}">${u.label}</div>`).join('');
  }

  const pop = $('#rack-pop');
  function showRackPop(e, r) {
    $('#rp-name').textContent = `${r.name} · ${r.id}`;
    const sp = $('#rp-status');
    sp.className = `status-pill ${r.status}`;
    sp.textContent = r.status === 'ok' ? 'НОРМА' : r.status === 'warn' ? 'ПРЕДУПР.' : 'КРИТ.';
    $('#rp-count').textContent = `${r.online}/${r.devices} · онлайн`;
    $('#rp-power').textContent = r.power;
    $('#rp-load').textContent  = `${r.load}%`;
    $('#rp-temp').textContent  = r.temp;
    $('#rp-open').onclick = () => { hideRackPop(); selectRack(r.id); switchScreen('rack'); };
    pop.hidden = false;
    moveRackPop(e);
  }
  function moveRackPop(e) {
    if (pop.hidden) return;
    const pad = 14;
    let x = e.clientX + pad, y = e.clientY + pad;
    const w = 240, h = pop.offsetHeight || 180;
    if (x + w > window.innerWidth)  x = e.clientX - w - pad;
    if (y + h > window.innerHeight) y = e.clientY - h - pad;
    pop.style.left = x + 'px';
    pop.style.top  = y + 'px';
  }
  function hideRackPop() { pop.hidden = true; }

  // ============ Вид стойки ============
  let currentRackId = 'R-02';
  let selectedDeviceId = 'core-rtr-01';

  function fillRackSelect() {
    const sel = $('#rack-select');
    sel.innerHTML = DATA.racks
      .map(r => `<option value="${r.id}" ${r.id===currentRackId?'selected':''}>${r.name} · ${r.id}</option>`)
      .join('');
    sel.onchange = () => selectRack(sel.value);
  }

  function selectRack(id) {
    currentRackId = id;
    const rack = DATA.racks.find(r => r.id === id);
    const det  = DATA.rackDetails[id] || DATA.rackDetails['R-02'];
    $('#rack-title').textContent   = rack.name;
    $('#rack-u-count').textContent = `${det.uHeight}U`;
    $('#rack-power').textContent   = rack.power;
    $('#rack-load').textContent    = `${rack.load}%`;
    $('#rack-temp').textContent    = rack.temp;
    fillRackSelect();
    renderRackBody(det);
    selectedDeviceId = det.devices[0] ? det.devices[0].id : null;
    renderDevicePanel();
  }

  function renderRackBody(det) {
    const ruler = $('#u-ruler');
    const slots = $('#u-slots');
    ruler.innerHTML = '';
    slots.innerHTML = '';
    for (let u = det.uHeight; u >= 1; u--) {
      const m = document.createElement('div');
      m.className = 'u-mark';
      m.textContent = `U${u}`;
      ruler.appendChild(m);
      const s = document.createElement('div');
      s.className = 'u-slot';
      s.dataset.u = u;
      slots.appendChild(s);
    }
    det.devices.forEach(dev => {
      const topIdx = det.uHeight - (dev.u + dev.uSize - 1);
      const topPx  = topIdx * 23;
      const heightPx = dev.uSize * 22 + (dev.uSize - 1) * 1;
      const el = document.createElement('div');
      el.className = `device-block ${dev.kind}`;
      if (dev.id === selectedDeviceId) el.classList.add('selected');
      el.style.top = topPx + 'px';
      el.style.height = heightPx + 'px';
      el.dataset.id = dev.id;
      el.innerHTML = deviceInnerHTML(dev);
      el.addEventListener('click', () => {
        selectedDeviceId = dev.id;
        renderRackBody(det);
        renderDevicePanel();
      });
      $$('.dev-port', el).forEach((pEl, idx) => {
        const port = dev.ports[idx];
        if (!port) return;
        pEl.addEventListener('mouseenter', e => showPortTip(e, dev, port));
        pEl.addEventListener('mousemove',  movePortTip);
        pEl.addEventListener('mouseleave', hidePortTip);
      });
      slots.appendChild(el);
    });
  }

  function deviceInnerHTML(d) {
    let inner = `
      <span class="dev-led ${d.status}"></span>
      <span class="dev-name">${d.name}</span>
      <span class="dev-model">· ${d.model}</span>
    `;
    if (d.kind === 'switch') {
      const ports = d.ports.slice(0, 24).map(p =>
        `<span class="dev-port ${p.status}" title="Port ${p.n}"></span>`).join('');
      inner += `<span class="dev-ports grid">${ports}</span>`;
    } else if (d.kind === 'router') {
      const ports = d.ports.slice(0, 10).map(p =>
        `<span class="dev-port ${p.status}" title="Port ${p.n}"></span>`).join('');
      inner += `<span class="dev-ports">${ports}</span>`;
    } else if (d.kind === 'server') {
      const disks = Array.from({length: 8}, (_, i) =>
        `<span class="dev-disk ${d.status === 'err' && i === 2 ? 'err' : 'ok'}"></span>`).join('');
      inner += `<span class="dev-disks">${disks}</span>`;
    } else if (d.kind === 'patch') {
      const ports = d.ports.slice(0, 24).map(p =>
        `<span class="dev-port ${p.status}"></span>`).join('');
      inner += `<span class="dev-ports">${ports}</span>`;
    } else if (d.kind === 'ups') {
      inner += `<span class="dev-ups-meter">
        <b>${d.battery ?? 96}% батарея</b> · нагрузка ${d.loadPct ?? 42}%
      </span>`;
    }
    return inner;
  }

  function renderDevicePanel() {
    const det = DATA.rackDetails[currentRackId] || DATA.rackDetails['R-02'];
    const d = det.devices.find(x => x.id === selectedDeviceId) || det.devices[0];
    if (!d) return;

    $('#d-name').textContent = d.name;
    $('#d-sub').textContent  = `${d.model} · ${DATA.racks.find(r=>r.id===currentRackId).name} · U${d.u}${d.uSize>1?`-U${d.u+d.uSize-1}`:''}`;

    const tags = $('#d-tags');
    tags.innerHTML = '';
    tags.appendChild(pill(d.status === 'ok' ? 'ok' : d.status,
      d.status === 'ok' ? 'ONLINE' : d.status === 'warn' ? 'ПРЕДУПР.' : 'ОШИБКА'));
    tags.appendChild(pill('', d.kind.toUpperCase()));

    setText('i-name',  d.name);
    setText('i-model', d.model);
    setText('i-ip',    d.ip);
    setText('i-mac',   d.mac);
    setText('i-pos',   `${currentRackId} · U${d.u}${d.uSize>1?`-U${d.u+d.uSize-1}`:''}`);
    setText('i-fw',    d.firmware || '—');
    setText('i-sn',    d.sn || '—');
    setText('i-seen',  d.seen || '—');

    $('#i-notes').value = d.notes || '';

    const tbody = $('#ports-tbody');
    tbody.innerHTML = d.ports.map(p => `
      <tr>
        <td class="mono">${p.n}</td>
        <td>${p.type}</td>
        <td class="mono">${p.ip}</td>
        <td>${p.peer}</td>
        <td>${p.cable}</td>
        <td class="mono">${p.vlan}</td>
        <td>${portStatusPill(p.status)}</td>
        <td><button class="link">✎</button></td>
      </tr>
    `).join('');

    renderStatsPanel(d);
  }

  function portStatusPill(s) {
    if (s === 'ok')    return `<span class="status-pill ok">UP</span>`;
    if (s === 'warn')  return `<span class="status-pill warn">FLAP</span>`;
    if (s === 'err')   return `<span class="status-pill err">DOWN</span>`;
    if (s === 'empty') return `<span class="status-pill">—</span>`;
    return `<span class="status-pill">${s}</span>`;
  }

  function pill(kind, text) {
    const el = document.createElement('span');
    el.className = `status-pill ${kind}`;
    el.textContent = text;
    return el;
  }
  function setText(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }

  $$('.device-tab').forEach(t => t.addEventListener('click', () => {
    const tab = t.dataset.dtab;
    $$('.device-tab').forEach(x => x.classList.toggle('active', x === t));
    $$('.device-tab-body').forEach(b => b.classList.toggle('hidden', b.dataset.dtabBody !== tab));
  }));

  function renderStatsPanel(d) {
    setRing('#ring-cpu', '#cpu-val', d.cpu);
    setRing('#ring-ram', '#ram-val', d.ram);

    const disk = d.disk ?? 0;
    setText('disk-val', disk);
    setText('disk-used', disk ? `${Math.round(disk * 9.6)} ГБ из 960` : '—');
    const fill = $('#disk-fill');
    fill.style.width = (disk || 0) + '%';
    fill.className = 'disk-fill' + (disk >= 80 ? ' err' : disk >= 65 ? ' warn' : '');

    setText('ping-val', typeof d.ping === 'number' ? `${d.ping} мс` : d.ping || '—');
    setText('up-val',   d.uptime || '—');

    drawSpark('#spark', 60, (d.cpu ?? 40));
  }

  function setRing(container, valueEl, pct) {
    const el = $(container);
    if (pct == null) {
      el.innerHTML = `<svg viewBox="0 0 100 100"><circle class="ring-bg" cx="50" cy="50" r="42" stroke-width="8" fill="none"/></svg>
      <div class="ring-lbl">—</div>`;
      setText(valueEl.slice(1), '—');
      return;
    }
    const r = 42, c = 2 * Math.PI * r;
    const off = c * (1 - pct / 100);
    const cls = pct >= 85 ? 'err' : pct >= 70 ? 'warn' : '';
    el.innerHTML = `
      <svg viewBox="0 0 100 100">
        <circle class="ring-bg" cx="50" cy="50" r="${r}" stroke-width="8" fill="none"/>
        <circle class="ring-fg ${cls}" cx="50" cy="50" r="${r}" stroke-width="8" fill="none"
                stroke-dasharray="${c}" stroke-dashoffset="${off}" stroke-linecap="round"/>
      </svg>
      <div class="ring-lbl">${pct}%</div>
    `;
    setText(valueEl.slice(1), pct);
  }

  function drawSpark(selector, points, base) {
    const svg = $(selector);
    const W = 200, H = 50;
    let pts = [];
    let v = base;
    for (let i = 0; i < points; i++) {
      v += (Math.random() - .5) * 10;
      v = Math.max(5, Math.min(98, v));
      pts.push([i / (points - 1) * W, H - (v / 100) * (H - 6) - 3]);
    }
    const line = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
    const area = `M0 ${H} ` + pts.map(p => `L${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ') + ` L${W} ${H} Z`;
    svg.innerHTML = `<path class="area" d="${area}"/><path class="line" d="${line}"/>`;
  }

  // ============ Тултип порта ============
  const tip = $('#port-tip');
  function showPortTip(e, dev, port) {
    $('#pt-label').textContent = `${dev.name} · порт ${port.n}`;
    const st = $('#pt-status');
    st.className = `pt-status status-pill ${port.status === 'empty' ? '' : port.status}`;
    st.textContent = port.status === 'ok' ? 'UP' : port.status === 'warn' ? 'FLAP' : port.status === 'err' ? 'DOWN' : '—';
    setText('pt-type',  port.type);
    setText('pt-ip',    port.ip);
    setText('pt-peer',  port.peer);
    setText('pt-cable', port.cable);
    setText('pt-speed', port.speed);
    setText('pt-vlan',  port.vlan);
    tip.hidden = false;
    movePortTip(e);
  }
  function movePortTip(e) {
    if (tip.hidden) return;
    const pad = 14;
    let x = e.clientX + pad, y = e.clientY + pad;
    const w = tip.offsetWidth || 260, h = tip.offsetHeight || 180;
    if (x + w > window.innerWidth)  x = e.clientX - w - pad;
    if (y + h > window.innerHeight) y = e.clientY - h - pad;
    tip.style.left = x + 'px';
    tip.style.top  = y + 'px';
  }
  function hidePortTip() { tip.hidden = true; }

  // ============ Топология ============
  let selectedNodeId = null;
  const filters = { fiber: true, utp: true, cat5e: true };

  $$('.topo-filters input').forEach(cb => cb.addEventListener('change', () => {
    filters[cb.dataset.filter] = cb.checked;
    renderTopology();
  }));

  function renderTopology() {
    const svg = $('#topo');
    const mini = $('#topo-mini');
    const { nodes, edges } = DATA.topology;

    const edgeSVG = edges.map(e => {
      if (!filters[e.kind]) return '';
      const a = nodes.find(n => n.id === e.a), b = nodes.find(n => n.id === e.b);
      const dim = selectedNodeId && selectedNodeId !== e.a && selectedNodeId !== e.b ? ' dim' : '';
      const x1 = a.x + 80, y1 = a.y + 24, x2 = b.x + 80, y2 = b.y + 24;
      const midX = (x1 + x2) / 2, midY = (y1 + y2) / 2;
      return `
        <g>
          <path class="topo-edge ${e.kind}${dim}"
                d="M${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}"
                data-a="${e.a}" data-b="${e.b}" data-bw="${e.bw}" data-util="${e.util}"/>
          <text class="edge-label" x="${midX}" y="${midY - 4}" text-anchor="middle">${e.bw} · ${e.util}%</text>
        </g>
      `;
    }).join('');

    const nodeSVG = nodes.map(n => {
      const dim = selectedNodeId && !isConnected(n.id) ? ' dim' : '';
      const sel = selectedNodeId === n.id ? ' selected' : '';
      return `
        <g class="topo-node${dim}${sel}" transform="translate(${n.x}, ${n.y})" data-id="${n.id}">
          <rect class="node-bg" x="0" y="0" width="160" height="48"/>
          <text class="title" x="12" y="20">${escapeHTML(n.label)}</text>
          <text class="meta"  x="12" y="36">${escapeHTML(n.sub)}</text>
          <circle class="st ${n.status}" cx="146" cy="14" r="4"/>
        </g>
      `;
    }).join('');

    svg.innerHTML = edgeSVG + nodeSVG;

    $$('.topo-node', svg).forEach(g => g.addEventListener('click', () => {
      selectedNodeId = selectedNodeId === g.dataset.id ? null : g.dataset.id;
      renderTopology();
    }));
    $$('.topo-edge', svg).forEach(p => {
      p.addEventListener('mouseenter', () => {
        p.parentNode.querySelector('.edge-label').classList.add('show');
      });
      p.addEventListener('mouseleave', () => {
        p.parentNode.querySelector('.edge-label').classList.remove('show');
      });
    });

    mini.innerHTML = svg.innerHTML;

    function isConnected(id) {
      return id === selectedNodeId ||
        edges.some(e => (e.a === selectedNodeId && e.b === id) ||
                        (e.b === selectedNodeId && e.a === id));
    }
  }

  let zoom = 1;
  $('#topo-zoom-in').onclick  = () => { zoom = Math.min(1.6, zoom + .1); applyZoom(); };
  $('#topo-zoom-out').onclick = () => { zoom = Math.max(0.6, zoom - .1); applyZoom(); };
  $('#topo-reset').onclick    = () => { zoom = 1; selectedNodeId = null; applyZoom(); renderTopology(); };
  function applyZoom() {
    const svg = $('#topo');
    svg.style.transform = `scale(${zoom})`;
    svg.style.transformOrigin = 'center center';
  }

  // ============ Мониторинг ============
  function renderMonitoring() {
    const grid = $('#mon-grid');
    grid.innerHTML = DATA.monitoring.map((m, i) => `
      <div class="mon-card ${m.status}">
        <div class="mon-head">
          <b>${m.id}</b>
          <span class="mloc">${m.loc}</span>
        </div>
        <div class="mon-rings">
          <div class="ring" id="mr-cpu-${i}"></div>
          <div class="ring" id="mr-ram-${i}"></div>
        </div>
        <div class="mon-row">
          <div><span class="muted">Диск</span><br><b>${m.disk}%</b></div>
          <div><span class="muted">Пинг</span><br><b>${m.ping} мс</b></div>
          <div><span class="muted">Uptime</span><br><b>${m.uptime}</b></div>
          <div><span class="muted">Статус</span><br><b>${m.status === 'ok' ? 'OK' : m.status === 'warn' ? 'WARN' : 'CRIT'}</b></div>
        </div>
        <svg class="spark" viewBox="0 0 200 32" preserveAspectRatio="none" id="mr-spark-${i}"></svg>
      </div>
    `).join('');

    DATA.monitoring.forEach((m, i) => {
      renderMiniRing(`#mr-cpu-${i}`, m.cpu, 'CPU');
      renderMiniRing(`#mr-ram-${i}`, m.ram, 'RAM');
      drawMiniSpark(`#mr-spark-${i}`, m.cpu);
    });

    const at = $('#alerts-tbody');
    at.innerHTML = DATA.alertRules.map((r, i) => `
      <tr>
        <td>${r.name}</td>
        <td class="mono">${r.cond}</td>
        <td><span class="sev ${r.level === 'info' ? 'info' : r.level === 'warn' ? 'warn' : 'crit'}">${r.level.toUpperCase()}</span></td>
        <td class="muted">${r.channel}</td>
        <td><span class="toggle ${r.enabled ? 'on' : ''}" data-alert="${i}"></span></td>
      </tr>
    `).join('');
    $$('.toggle', at).forEach(t => t.addEventListener('click', () => t.classList.toggle('on')));
  }

  function renderMiniRing(container, pct, lbl) {
    const el = $(container);
    if (!el) return;
    const r = 22, c = 2 * Math.PI * r;
    const off = c * (1 - (pct || 0) / 100);
    const cls = pct >= 85 ? 'err' : pct >= 70 ? 'warn' : '';
    el.innerHTML = `
      <svg viewBox="0 0 54 54">
        <circle class="ring-bg" cx="27" cy="27" r="${r}" stroke-width="5" fill="none"/>
        <circle class="ring-fg ${cls}" cx="27" cy="27" r="${r}" stroke-width="5" fill="none"
                stroke-dasharray="${c}" stroke-dashoffset="${off}" stroke-linecap="round"/>
      </svg>
      <div class="ring-lbl">${pct}<span style="font-size:8px;color:var(--mute);margin-left:1px">${lbl}</span></div>
    `;
  }

  function drawMiniSpark(sel, base) {
    const svg = $(sel);
    if (!svg) return;
    const W = 200, H = 32, pts = [];
    let v = base;
    for (let i = 0; i < 30; i++) {
      v += (Math.random() - .5) * 12;
      v = Math.max(5, Math.min(96, v));
      pts.push([i / 29 * W, H - (v / 100) * (H - 4) - 2]);
    }
    const line = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
    svg.innerHTML = `<path fill="none" stroke="var(--accent)" stroke-width="1.3" d="${line}"/>`;
  }

  // ============ Журнал событий ============
  function renderEvents() {
    const tbody = $('#events-tbody');
    tbody.innerHTML = '';
    DATA.events.forEach((e, i) => {
      const row = document.createElement('tr');
      row.className = 'row';
      row.innerHTML = `
        <td class="ts">${e.ts}</td>
        <td><span class="sev ${e.sev}">${sevText(e.sev)}</span></td>
        <td>${e.device}</td>
        <td class="mono">${e.rack}</td>
        <td>${e.desc}</td>
        <td>${e.resolved ? '<span class="resolved-pill yes">✓ решено</span>' : '<span class="resolved-pill no">— открыто</span>'}</td>
      `;
      const detail = document.createElement('tr');
      detail.className = 'detail hidden';
      detail.innerHTML = `<td colspan="6">
        ${e.detail}
        <pre>event.id=EV-${String(1000+i)} · rack=${e.rack} · device=${e.device} · severity=${e.sev} · ts=${e.ts}</pre>
      </td>`;
      row.addEventListener('click', () => detail.classList.toggle('hidden'));
      tbody.appendChild(row);
      tbody.appendChild(detail);
    });
  }
  function sevText(s) {
    return s === 'info' ? 'ИНФО' : s === 'warn' ? 'ПРЕДУПР.' : 'КРИТИЧНО';
  }

  // ============ Модал ============
  const modal = $('#modal');
  function openModal()  { modal.hidden = false; }
  function closeModal() { modal.hidden = true; }
  $('#btn-add-device').addEventListener('click', openModal);
  $('#modal-close').addEventListener('click', closeModal);
  $('#modal-cancel').addEventListener('click', closeModal);
  modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

  function escapeHTML(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[c]));
  }

  renderFloorplan();
  fillRackSelect();
  selectRack(currentRackId);
  renderMonitoring();
  renderEvents();
  renderTopology();
})();
