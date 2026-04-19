/* =============== RackMap app =============== */
(function () {
  const { racks, events, alerts } = window.RACKMAP;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const el = (tag, cls, html) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  };

  let currentRackId = racks[0].id;
  let currentDeviceId = racks[0].devices[0]?.id;

  // ================= TABS =================
  function showScreen(name) {
    $$(".screen").forEach((s) => s.classList.toggle("active", s.dataset.screen === name));
    $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.screen === name));
    if (name === "topology") requestAnimationFrame(drawTopology);
    if (name === "monitoring") renderMonitoring();
  }
  $("#tabs").addEventListener("click", (e) => {
    const t = e.target.closest(".tab");
    if (t) showScreen(t.dataset.screen);
  });
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-goto]");
    if (a) { e.preventDefault(); showScreen(a.dataset.goto); }
  });

  // ================= CLOCK =================
  function tickClock() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    $("#clock").textContent = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }
  tickClock(); setInterval(tickClock, 1000);

  // ================= SCREEN 1: FLOORPLAN =================
  function renderFloorplan() {
    const fp = $("#floorplan");
    fp.querySelectorAll(".rack-tile,.rack-placeholder").forEach((n) => n.remove());
    racks.forEach((r) => {
      const t = el("div", `rack-tile status-${r.status}`);
      t.style.left = r.x + "px";
      t.style.top = r.y + "px";
      t.dataset.rackId = r.id;
      const devBoxes = Array.from({ length: 28 }, (_, i) => {
        if (i < r.devices.length) {
          const s = r.devices[i].status;
          return `<div class="rt-dev ${s === "green" ? "on" : s === "yellow" ? "warn" : s === "red" ? "err" : ""}"></div>`;
        }
        return `<div class="rt-dev"></div>`;
      }).join("");
      t.innerHTML = `
        <div class="rt-name">
          <span>${r.name}</span>
          <span class="status-pill ${r.status}">${r.status === "green" ? "OK" : r.status === "yellow" ? "WARN" : "CRIT"}</span>
        </div>
        <div class="rt-devices">${devBoxes}</div>
        <div class="rt-foot">
          <span>${r.devices.length}/42U</span>
          <span>${r.power}</span>
        </div>
      `;
      fp.appendChild(t);
    });
    // placeholder
    const ph = el("div", "rack-placeholder", "+ Добавить стойку");
    ph.style.left = (racks[racks.length - 1].x + 220) + "px";
    ph.style.top = racks[0].y + "px";
    fp.appendChild(ph);

    // hover popup
    fp.querySelectorAll(".rack-tile").forEach((t) => {
      t.addEventListener("mouseenter", (ev) => showRackPop(ev, t.dataset.rackId));
      t.addEventListener("mousemove", (ev) => moveFloating($("#rack-pop"), ev.clientX + 18, ev.clientY + 18));
      t.addEventListener("mouseleave", () => $("#rack-pop").hidden = true);
      t.addEventListener("click", () => { openRack(t.dataset.rackId); });
    });
  }
  function showRackPop(ev, rackId) {
    const r = racks.find((x) => x.id === rackId);
    if (!r) return;
    $("#rp-name").textContent = r.name;
    const st = $("#rp-status");
    st.className = "status-pill " + r.status;
    st.textContent = r.status === "green" ? "OK" : r.status === "yellow" ? "WARN" : "CRIT";
    $("#rp-count").textContent = `${r.devices.length} / 42U`;
    $("#rp-power").textContent = r.power;
    $("#rp-load").textContent = r.load;
    $("#rp-temp").textContent = r.temp;
    const pop = $("#rack-pop"); pop.hidden = false;
    $("#rp-open").onclick = () => { openRack(rackId); $("#rack-pop").hidden = true; };
    moveFloating(pop, ev.clientX + 18, ev.clientY + 18);
  }
  function moveFloating(node, x, y) {
    const w = node.offsetWidth, h = node.offsetHeight;
    const mx = Math.min(x, window.innerWidth - w - 12);
    const my = Math.min(y, window.innerHeight - h - 12);
    node.style.left = mx + "px";
    node.style.top = my + "px";
  }

  function openRack(rackId) {
    currentRackId = rackId;
    const r = racks.find((x) => x.id === rackId);
    currentDeviceId = r.devices[0]?.id;
    $("#rack-select").value = rackId;
    renderRackDetail();
    showScreen("rack");
  }

  // ================= SCREEN 2: RACK DETAIL =================
  function fillRackSelect() {
    const sel = $("#rack-select");
    sel.innerHTML = racks.map((r) => `<option value="${r.id}">${r.name}</option>`).join("");
    sel.value = currentRackId;
    sel.onchange = () => {
      currentRackId = sel.value;
      const r = racks.find((x) => x.id === currentRackId);
      currentDeviceId = r.devices[0]?.id;
      renderRackDetail();
    };
  }

  function renderRackDetail() {
    const r = racks.find((x) => x.id === currentRackId);
    $("#rack-title").textContent = r.name;
    $("#rack-u-count").textContent = r.uCount + "U";
    $("#rack-power").textContent = r.power;
    $("#rack-load").textContent = r.load;
    $("#rack-temp").textContent = r.temp;

    // u-ruler
    const ruler = $("#u-ruler"); ruler.innerHTML = "";
    for (let i = 1; i <= r.uCount; i++) {
      ruler.appendChild(el("div", "u-num", String(i).padStart(2, "0")));
    }
    // u-slots: build 42 empty, then overlay devices
    const slots = $("#u-slots"); slots.innerHTML = "";
    const occupied = new Array(r.uCount + 1).fill(null);
    r.devices.forEach((d) => {
      for (let u = d.uStart; u < d.uStart + d.u; u++) occupied[u] = d;
    });
    for (let u = 1; u <= r.uCount; u++) {
      const d = occupied[u];
      if (!d) {
        slots.appendChild(el("div", "u-slot empty"));
      } else if (d.uStart === u) {
        slots.appendChild(renderDeviceBlock(d));
      }
      // devices spanning multiple U — their rendered element has the correct height
      else {
        // skipped; represented by the tall block
      }
    }
    // Device blocks click handling
    $$("#u-slots .device-block").forEach((b) => {
      b.addEventListener("click", () => {
        currentDeviceId = b.dataset.id;
        $$("#u-slots .device-block").forEach((x) => x.classList.toggle("selected", x.dataset.id === currentDeviceId));
        renderDeviceInfo();
      });
      if (b.dataset.id === currentDeviceId) b.classList.add("selected");
    });

    renderDeviceInfo();
  }

  function renderDeviceBlock(d) {
    const b = el("div", `device-block status-${d.status}`);
    b.style.setProperty("--u", d.u);
    b.dataset.id = d.id;
    const portsHtml = renderPortsInBlock(d);
    b.innerHTML = `
      <div class="db-head">
        <span class="db-name">${d.name}</span>
        <span class="db-u">U${String(d.uStart).padStart(2,"0")}${d.u>1?"–U"+String(d.uStart+d.u-1).padStart(2,"0"):""}</span>
      </div>
      <div class="db-body">${portsHtml}</div>
    `;
    // port hover
    b.querySelectorAll(".port,.pp").forEach((p) => {
      const idx = +p.dataset.idx;
      const port = d.ports[idx];
      if (!port) return;
      p.addEventListener("mouseenter", (ev) => showPortTip(ev, d, port));
      p.addEventListener("mousemove", (ev) => moveFloating($("#port-tip"), ev.clientX + 18, ev.clientY + 18));
      p.addEventListener("mouseleave", () => $("#port-tip").hidden = true);
    });
    return b;
  }
  function renderPortsInBlock(d) {
    if (d.type === "router") {
      return `<div class="ports-row">${d.ports.map((p,i) => `<span class="port ${p.status==='on'?'on':p.status==='err'?'err':''}" data-idx="${i}" title="${p.label}"></span>`).join("")}</div>`;
    }
    if (d.type === "switch") {
      return `<div class="switch-grid">${d.ports.map((p,i) => `<span class="port ${p.status==='on'?'on':p.status==='err'?'err':''}" data-idx="${i}" title="${p.label}"></span>`).join("")}</div>`;
    }
    if (d.type === "patch") {
      return `<div class="patch-ports">${d.ports.map((p,i) => `<span class="pp ${p.status==='on'?'on':''}" data-idx="${i}" title="${p.label}"></span>`).join("")}</div>`;
    }
    if (d.type === "server") {
      const cpuCls = d.cpu>90?"err":d.cpu>75?"warn":"";
      const ramCls = d.ram>90?"err":d.ram>80?"warn":"";
      return `
        <div class="server-view">
          <span class="led ${d.status==='red'?'red':d.status==='yellow'?'yellow':''}"></span>
          <div class="meter" title="CPU ${d.cpu}%"><div class="fill ${cpuCls}" style="width:${d.cpu}%"></div></div>
          <div class="meter" title="RAM ${d.ram}%"><div class="fill ${ramCls}" style="width:${d.ram}%"></div></div>
          <div class="disk-bays">${Array.from({length:8},(_,i)=>`<span class="disk-bay ${i<5?'on':''}"></span>`).join("")}</div>
          <div class="ports-row">${d.ports.map((p,i) => `<span class="port ${p.status==='on'?'on':p.status==='err'?'err':''}" data-idx="${i}"></span>`).join("")}</div>
        </div>
      `;
    }
    if (d.type === "ups") {
      return `
        <div class="ups-view">
          <span class="led"></span>
          <div class="ups-batt"><div class="bf" style="width:${d.battery}%"></div></div>
          <span>BAT ${d.battery}%</span>
          <span>·</span>
          <span>LOAD ${d.load}%</span>
        </div>
      `;
    }
    return "";
  }

  function showPortTip(ev, d, p) {
    $("#pt-label").textContent = `${d.name} · ${p.label}`;
    const s = $("#pt-status");
    s.className = "pt-status status-pill " + (p.status==='err'?'red':p.status==='on'?'green':'yellow');
    s.textContent = p.status==='err'?'ERR':p.status==='on'?'UP':'DOWN';
    $("#pt-type").textContent = p.type;
    $("#pt-ip").textContent = p.ip;
    $("#pt-peer").textContent = p.peer;
    $("#pt-cable").textContent = p.cable;
    $("#pt-speed").textContent = p.speed;
    $("#pt-vlan").textContent = p.vlan === "—" ? "—" : "VLAN " + p.vlan;
    const tip = $("#port-tip"); tip.hidden = false;
    moveFloating(tip, ev.clientX + 18, ev.clientY + 18);
  }

  // ---------- Device info (center) ----------
  function renderDeviceInfo() {
    const r = racks.find((x) => x.id === currentRackId);
    const d = r.devices.find((x) => x.id === currentDeviceId);
    if (!d) return;
    $("#d-name").textContent = d.name;
    $("#d-sub").textContent = `${d.model} · ${typeLabel(d.type)}`;
    const tags = $("#d-tags"); tags.innerHTML = "";
    tags.appendChild(el("span", "status-pill " + d.status, d.status === "green" ? "В СЕТИ" : d.status === "yellow" ? "ПРЕДУПР." : "КРИТ."));
    tags.appendChild(el("span", "status-pill", typeLabel(d.type).toUpperCase()));

    $("#i-name").textContent = d.name;
    $("#i-model").textContent = d.model;
    $("#i-ip").textContent = d.ip;
    $("#i-mac").textContent = d.mac;
    $("#i-pos").textContent = `U${String(d.uStart).padStart(2,"0")}${d.u>1?"–U"+String(d.uStart+d.u-1).padStart(2,"0"):""} · ${d.u}U`;
    $("#i-fw").textContent = d.firmware;
    $("#i-sn").textContent = d.serial;
    $("#i-seen").textContent = d.lastSeen;
    $("#i-notes").value = d.notes || "";

    // ports table
    const tb = $("#ports-tbody");
    tb.innerHTML = d.ports.length ? d.ports.map((p) => `
      <tr>
        <td class="mono">${p.label}</td>
        <td>${p.type}</td>
        <td class="mono">${p.ip}</td>
        <td class="mono">${p.peer}</td>
        <td>${p.cable}</td>
        <td class="mono">${p.vlan === "—" ? "—" : p.vlan}</td>
        <td><span class="st-dot ${p.status==='on'?'dot green':p.status==='err'?'dot red':'dot gray'}"></span>${p.status==='on'?'UP':p.status==='err'?'ERR':'DOWN'}</td>
        <td><button class="link">Ред.</button></td>
      </tr>
    `).join("") : `<tr><td colspan="8" class="muted" style="padding:14px">Нет портов у устройства этого типа.</td></tr>`;

    renderLiveStats(d);
  }
  function typeLabel(t) {
    return { server:"Сервер", switch:"Коммутатор", router:"Маршрутизатор", patch:"Патч-панель", ups:"ИБП" }[t] || t;
  }

  // ---------- Live stats (right) ----------
  let sparkPoints = [];
  let statsTimer = null;
  function renderLiveStats(d) {
    const rc = $("#ring-cpu"), rr = $("#ring-ram");
    const setRing = (ring, val) => {
      ring.style.setProperty("--v", val);
      ring.classList.remove("warn","err");
      if (val > 90) ring.classList.add("err");
      else if (val > 80) ring.classList.add("warn");
    };
    setRing(rc, d.cpu); $("#cpu-val").textContent = d.cpu;
    setRing(rr, d.ram); $("#ram-val").textContent = d.ram;
    $("#disk-fill").style.width = d.disk + "%";
    $("#disk-val").textContent = d.disk;
    $("#disk-used").textContent = d.diskUsed || "";
    $("#ping-val").textContent = d.ping + " мс";
    $("#up-val").textContent = d.uptime;

    // spark
    sparkPoints = Array.from({length:30}, () => d.cpu - 5 + Math.random()*10);
    drawSpark();
    clearInterval(statsTimer);
    statsTimer = setInterval(() => {
      const last = sparkPoints[sparkPoints.length-1] || d.cpu;
      const next = Math.max(5, Math.min(99, last + (Math.random()-0.5)*8));
      sparkPoints.push(next); sparkPoints.shift();
      drawSpark();
    }, 1200);
  }
  function drawSpark() {
    const svg = $("#spark");
    if (!svg) return;
    const w = 200, h = 50;
    const min = 0, max = 100;
    const pts = sparkPoints.map((v, i) => {
      const x = (i / (sparkPoints.length - 1)) * w;
      const y = h - ((v - min) / (max - min)) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    svg.innerHTML = `
      <polyline fill="none" stroke="#3B82F6" stroke-width="1.5" points="${pts}"/>
      <polyline fill="rgba(59,130,246,0.15)" stroke="none"
        points="0,${h} ${pts} ${w},${h}"/>
    `;
  }

  // Device tabs
  $$(".device-tab").forEach((t) => {
    t.addEventListener("click", () => {
      $$(".device-tab").forEach((x) => x.classList.toggle("active", x === t));
      $$(".device-tab-body").forEach((b) => b.classList.toggle("hidden", b.dataset.dtabBody !== t.dataset.dtab));
    });
  });

  // ================= SCREEN 3: TOPOLOGY =================
  function drawTopology() {
    const svg = $("#topo");
    const W = 1200, H = 700;
    // gather nodes across racks
    const allDevices = [];
    racks.forEach((r, ri) => {
      r.devices.forEach((d, di) => {
        allDevices.push({ ...d, rackIdx: ri, rackName: r.name });
      });
    });
    // positions: routers top, switches row 2, servers row 3+, ups/patch bottom
    const groups = { router: [], switch: [], server: [], patch: [], ups: [] };
    allDevices.forEach((d) => groups[d.type]?.push(d));
    const cols = Math.max(1, racks.length);
    const colW = W / cols;

    const positions = {};
    Object.entries(groups).forEach(([type, arr]) => {
      const rows = { router: 90, switch: 210, server: 370, patch: 530, ups: 640 };
      const y = rows[type] || 400;
      // group by rack
      racks.forEach((r, ri) => {
        const inRack = arr.filter((d) => d.rackIdx === ri);
        inRack.forEach((d, k) => {
          const x = ri * colW + colW / 2 + (k - (inRack.length - 1)/2) * 80;
          positions[d.id] = { x, y };
        });
      });
    });

    // edges: connect in each rack: router->switch, switch->server, switch->patch, ups to all in rack
    const edges = [];
    racks.forEach((r) => {
      const routers = r.devices.filter((d) => d.type === "router");
      const switches = r.devices.filter((d) => d.type === "switch");
      const servers = r.devices.filter((d) => d.type === "server");
      const patches = r.devices.filter((d) => d.type === "patch");
      routers.forEach((rt) => switches.forEach((sw) => edges.push({ a: rt.id, b: sw.id, kind: "fiber" })));
      switches.forEach((sw) => {
        servers.forEach((sv) => edges.push({ a: sw.id, b: sv.id, kind: Math.random() > 0.5 ? "utp" : "cat5e" }));
        patches.forEach((pp) => edges.push({ a: sw.id, b: pp.id, kind: "utp" }));
      });
    });
    // cross-rack: connect core routers of rack01 to edge switches of racks 2..5 (fiber uplinks)
    const coreRouter = racks[0].devices.find((d) => d.type === "router");
    if (coreRouter) {
      racks.slice(1).forEach((r) => {
        const sw = r.devices.find((d) => d.type === "switch");
        if (sw) edges.push({ a: coreRouter.id, b: sw.id, kind: "fiber" });
      });
    }

    const icons = {
      router: { bg: "#172342", accent: "#60a5fa", label: "RTR" },
      switch: { bg: "#1a2535", accent: "#3B82F6", label: "SW" },
      server: { bg: "#1c2330", accent: "#22C55E", label: "SRV" },
      patch:  { bg: "#22252B", accent: "#9CA3AF", label: "PP" },
      ups:    { bg: "#2b2618", accent: "#EAB308", label: "UPS" },
    };

    const edgesSvg = edges.map((e, i) => {
      const a = positions[e.a], b = positions[e.b];
      if (!a || !b) return "";
      return `<line class="topo-edge ${e.kind}" data-a="${e.a}" data-b="${e.b}"
        x1="${a.x}" y1="${a.y + 22}" x2="${b.x}" y2="${b.y - 22}">
        <title>${e.kind.toUpperCase()} · ${Math.random() > 0.5 ? '1 Gb/s' : '10 Gb/s'}</title>
      </line>`;
    }).join("");

    const nodesSvg = allDevices.map((d) => {
      const p = positions[d.id]; if (!p) return "";
      const ic = icons[d.type] || icons.switch;
      const stColor = d.status === "red" ? "#EF4444" : d.status === "yellow" ? "#EAB308" : "#22C55E";
      return `
        <g class="topo-node" data-id="${d.id}" transform="translate(${p.x - 50}, ${p.y - 22})">
          <rect width="100" height="44" rx="6" fill="${ic.bg}" stroke="${ic.accent}" stroke-width="1.2"/>
          <circle cx="92" cy="8" r="3" fill="${stColor}"/>
          <text x="10" y="18" font-weight="600">${d.name}</text>
          <text class="sub" x="10" y="33">${ic.label} · ${d.rackName}</text>
        </g>
      `;
    }).join("");

    // rack backgrounds
    const rackBgs = racks.map((r, ri) => {
      const x = ri * colW + 10;
      return `<g>
        <rect x="${x}" y="40" width="${colW - 20}" height="${H - 80}" fill="rgba(255,255,255,0.015)" stroke="${"#30363D"}" stroke-dasharray="3,3" rx="6"/>
        <text x="${x + 10}" y="32" fill="#8B949E" font-size="11" font-family="JetBrains Mono">${r.name}</text>
      </g>`;
    }).join("");

    svg.innerHTML = rackBgs + edgesSvg + nodesSvg;

    // filter behavior
    $$(".topo-filters input").forEach((cb) => {
      cb.onchange = () => {
        const kind = cb.dataset.filter;
        svg.querySelectorAll(`.topo-edge.${kind}`).forEach((e) => e.style.display = cb.checked ? "" : "none");
      };
    });

    // node click → isolate
    svg.querySelectorAll(".topo-node").forEach((n) => {
      n.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const id = n.dataset.id;
        const connected = new Set([id]);
        svg.querySelectorAll(".topo-edge").forEach((e) => {
          if (e.dataset.a === id || e.dataset.b === id) {
            connected.add(e.dataset.a); connected.add(e.dataset.b);
            e.classList.remove("dim");
          } else {
            e.classList.add("dim");
          }
        });
        svg.querySelectorAll(".topo-node").forEach((o) => {
          o.classList.toggle("dim", !connected.has(o.dataset.id));
        });
      });
    });
    svg.addEventListener("click", () => {
      svg.querySelectorAll(".topo-edge,.topo-node").forEach((e) => e.classList.remove("dim"));
    });

    // minimap
    const mini = $("#topo-mini");
    mini.innerHTML = svg.innerHTML;

    // zoom
    let scale = 1;
    const apply = () => svg.style.transform = `scale(${scale})`;
    $("#topo-zoom-in").onclick = () => { scale = Math.min(2, scale + 0.1); apply(); };
    $("#topo-zoom-out").onclick = () => { scale = Math.max(0.5, scale - 0.1); apply(); };
    $("#topo-reset").onclick = () => { scale = 1; apply(); };
  }

  // ================= SCREEN 4: MONITORING =================
  function renderMonitoring() {
    const grid = $("#mon-grid");
    const all = [];
    racks.forEach((r) => r.devices.forEach((d) => all.push({ ...d, rackName: r.name })));
    const monitorable = all.filter((d) => d.type !== "patch");
    grid.innerHTML = monitorable.map((d) => {
      const cpuCls = d.cpu > 90 ? "err" : d.cpu > 80 ? "warn" : "";
      const ramCls = d.ram > 90 ? "err" : d.ram > 80 ? "warn" : "";
      return `
        <div class="mon-card status-${d.status}">
          <div class="mc-head">
            <span class="mc-name">${d.name}</span>
            <span class="mc-type">${typeLabel(d.type)} · ${d.rackName}</span>
          </div>
          <div class="mc-rings">
            <div>
              <div class="ring ${cpuCls}" style="--v:${d.cpu}"></div>
              <div>ЦП ${d.cpu}%</div>
            </div>
            <div>
              <div class="ring ${ramCls}" style="--v:${d.ram}"></div>
              <div>ОЗУ ${d.ram}%</div>
            </div>
          </div>
          <div class="mc-metrics">
            <div class="row"><span class="muted">Диск</span><div class="mini-bar"><div class="fill" style="width:${d.disk}%"></div></div><strong>${d.disk}%</strong></div>
            <div class="row"><span class="muted">Пинг</span><strong style="color:${d.ping < 5 ? 'var(--green)' : d.ping < 20 ? 'var(--yellow)' : 'var(--red)'}">${d.ping} мс</strong></div>
            <div class="row"><span class="muted">Uptime</span><strong>${d.uptime}</strong></div>
            <div class="mc-spark">${sparkSvg()}</div>
          </div>
          <div class="mc-foot">
            <span>IP ${d.ip}</span>
            <span>последн. ${d.lastSeen}</span>
          </div>
        </div>
      `;
    }).join("");

    // alerts
    const at = $("#alerts-tbody");
    at.innerHTML = alerts.map((a, i) => `
      <tr>
        <td><strong>${a.name}</strong></td>
        <td class="mono muted">${a.cond}</td>
        <td><span class="sev ${a.level}">${a.level==='crit'?'КРИТ':a.level==='warn'?'ПРЕДУПР':'ИНФО'}</span></td>
        <td>${a.channel}</td>
        <td><span class="toggle ${a.on?'on':''}" data-idx="${i}"></span></td>
      </tr>
    `).join("");
    at.querySelectorAll(".toggle").forEach((t) => {
      t.addEventListener("click", () => t.classList.toggle("on"));
    });
  }
  function sparkSvg() {
    const pts = Array.from({length: 20}, () => 20 + Math.random()*40);
    const w = 200, h = 28;
    const path = pts.map((v,i) => `${(i/(pts.length-1))*w},${h - (v/100)*h}`).join(" ");
    return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <polyline fill="none" stroke="#3B82F6" stroke-width="1.5" points="${path}"/>
    </svg>`;
  }

  // ================= SCREEN 6: EVENTS =================
  function renderEvents() {
    const tb = $("#events-tbody");
    tb.innerHTML = events.map((e, i) => `
      <tr class="event-row" data-idx="${i}">
        <td class="mono">${e.ts}</td>
        <td><span class="sev ${e.sev}">${e.sev==='crit'?'КРИТ':e.sev==='warn'?'ПРЕДУПР':'ИНФО'}</span></td>
        <td class="mono">${e.device}</td>
        <td>${e.rack}</td>
        <td>${e.desc}</td>
        <td>${e.resolved ? '<span class="resolved-badge">Да</span>' : '<span class="muted">—</span>'}</td>
      </tr>
    `).join("");
    tb.querySelectorAll(".event-row").forEach((row) => {
      row.addEventListener("click", () => {
        const idx = +row.dataset.idx;
        const next = row.nextElementSibling;
        if (next && next.classList.contains("expand")) { next.remove(); return; }
        const e = events[idx];
        const ex = el("tr", "expand");
        ex.innerHTML = `<td colspan="6">› ${e.detail}</td>`;
        row.after(ex);
      });
    });
  }

  // ================= MODAL =================
  $("#btn-add-device").addEventListener("click", () => $("#modal").hidden = false);
  $("#modal-close").addEventListener("click", () => $("#modal").hidden = true);
  $("#modal-cancel").addEventListener("click", () => $("#modal").hidden = true);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") $("#modal").hidden = true; });

  // ================= INIT =================
  renderFloorplan();
  fillRackSelect();
  renderRackDetail();
  renderEvents();
})();
