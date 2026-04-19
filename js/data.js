/* ==================== RackMap mock data ==================== */
window.RACKMAP = (function () {
  const mac = (p) => Array.from({length:6},()=>Math.floor(Math.random()*256).toString(16).padStart(2,"0").toUpperCase()).join(":");
  const ip = (a,b,c,d) => `${a}.${b}.${c}.${d}`;

  // ======== Device factory ========
  let idc = 0;
  const dev = (o) => ({
    id: "d"+(++idc),
    status: "green",
    firmware: "—",
    serial: "SN-" + Math.random().toString(36).slice(2,10).toUpperCase(),
    mac: mac(),
    lastSeen: "2 сек. назад",
    notes: "",
    ports: [],
    cpu: 20 + Math.floor(Math.random()*40),
    ram: 30 + Math.floor(Math.random()*50),
    disk: 40 + Math.floor(Math.random()*40),
    diskUsed: "",
    ping: 1 + Math.floor(Math.random()*6),
    uptime: "34д 12ч",
    ...o,
  });

  const mkPorts = (count, kind, baseIp, peerName, cable="UTP Cat6", speed="1 Gb/s", vlan=10) => {
    const arr = [];
    for (let i=1;i<=count;i++){
      const on = Math.random() > 0.3;
      const err = on && Math.random() < 0.05;
      arr.push({
        label: kind === "sfp" ? `SFP${i}` : `${i}`,
        type: kind === "sfp" ? "SFP+" : "RJ45",
        ip: on ? (baseIp ? ip(baseIp[0], baseIp[1], baseIp[2], baseIp[3] + i) : "—") : "—",
        peer: on ? `${peerName}-${String(i).padStart(2,"0")}` : "—",
        cable,
        speed: kind === "sfp" ? "10 Gb/s" : speed,
        vlan: on ? (vlan + (i % 3) * 10) : "—",
        status: err ? "err" : (on ? "on" : "off"),
      });
    }
    return arr;
  };

  // ======== Rack 01 ========
  const rack01Devices = [
    dev({
      name: "mt-core-01", model: "Mikrotik RB4011iGS+RM",
      type: "router", u: 1, uStart: 42,
      ip: "10.0.0.1", firmware: "RouterOS 7.11.2",
      ports: mkPorts(10, "rj", [10,0,0,1], "port"),
    }),
    dev({
      name: "sw-core-01", model: "Cisco Catalyst 2960X-24",
      type: "switch", u: 1, uStart: 41,
      ip: "10.0.0.2", firmware: "IOS 15.2(7)",
      ports: (() => {
        const a = mkPorts(24, "rj", [10,0,0,10], "core");
        a.push(...mkPorts(2, "sfp", [10,0,0,40], "uplink", "Fiber LC", "10 Gb/s", 100));
        return a;
      })(),
    }),
    dev({
      name: "pp-24-a", model: "Patch Panel 24-port Cat6",
      type: "patch", u: 1, uStart: 40,
      ip: "—", firmware: "—",
      ports: mkPorts(24, "rj", null, "wall", "UTP Cat6", "—", 0),
    }),
    dev({
      name: "srv-app-01", model: "Dell PowerEdge R740",
      type: "server", u: 2, uStart: 36,
      ip: "10.0.1.11", firmware: "BIOS 2.17.1",
      cpu: 62, ram: 74, disk: 58, diskUsed: "2.9/5.0 TB",
      ports: mkPorts(4, "rj", [10,0,1,11], "sw-core", "UTP Cat6", "1 Gb/s", 20),
    }),
    dev({
      name: "srv-db-01", model: "Dell PowerEdge R750",
      type: "server", u: 2, uStart: 34,
      ip: "10.0.1.12", firmware: "BIOS 2.18.0",
      cpu: 88, ram: 91, disk: 72, diskUsed: "3.6/5.0 TB",
      status: "yellow",
      ports: mkPorts(4, "rj", [10,0,1,12], "sw-core", "UTP Cat6", "1 Gb/s", 30),
    }),
    dev({
      name: "srv-web-02", model: "Supermicro SYS-1029U",
      type: "server", u: 1, uStart: 33,
      ip: "10.0.1.14", firmware: "BIOS 1.4b",
      cpu: 33, ram: 41, disk: 22, diskUsed: "0.6/3.0 TB",
      ports: mkPorts(4, "rj", [10,0,1,14], "sw-core"),
    }),
    dev({
      name: "srv-gpu-01", model: "Supermicro GPU 4124GS",
      type: "server", u: 4, uStart: 29,
      ip: "10.0.1.15", firmware: "BIOS 2.1",
      cpu: 96, ram: 84, disk: 45,
      status: "red",
      ports: mkPorts(4, "rj", [10,0,1,15], "sw-core"),
    }),
    dev({
      name: "ups-apc-01", model: "APC Smart-UPS RT 5000",
      type: "ups", u: 3, uStart: 3,
      ip: "10.0.0.99", firmware: "5.4.9", battery: 92, load: 38,
      ports: [],
    }),
  ];

  const racks = [
    { id: "r01", name: "Rack 01", uCount: 42, x: 40, y: 40, status: "yellow", power: "5.2 кВт", load: "38%", temp: "24°C", devices: rack01Devices },
    { id: "r02", name: "Rack 02", uCount: 42, x: 260, y: 40, status: "green", power: "4.7 кВт", load: "31%", temp: "23°C", devices: [] },
    { id: "r03", name: "Rack 03", uCount: 42, x: 480, y: 40, status: "green", power: "5.1 кВт", load: "34%", temp: "24°C", devices: [] },
    { id: "r04", name: "Rack 04", uCount: 42, x: 700, y: 40, status: "red",   power: "6.4 кВт", load: "58%", temp: "29°C", devices: [] },
    { id: "r05", name: "Rack 05", uCount: 42, x: 920, y: 40, status: "green", power: "3.9 кВт", load: "24%", temp: "22°C", devices: [] },
  ];

  // Fill racks 2-5 procedurally
  [racks[1], racks[2], racks[3], racks[4]].forEach((r, idx) => {
    r.devices = [
      dev({ name:`sw-${r.id}`, model:"Cisco Catalyst 2960X", type:"switch", u:1, uStart:42,
        ip:`10.0.${idx+2}.2`, firmware:"IOS 15.2(7)",
        ports: mkPorts(24,"rj",[10,0,idx+2,10],"edge") }),
      dev({ name:`pp-${r.id}`, model:"Patch Panel 24", type:"patch", u:1, uStart:41, ip:"—",
        ports: mkPorts(24,"rj",null,"wall","UTP Cat6","—",0) }),
      dev({ name:`srv-${r.id}-01`, model:"Dell PowerEdge R740", type:"server", u:2, uStart:37,
        ip:`10.0.${idx+2}.11`, firmware:"BIOS 2.17.1",
        cpu: 40+idx*10, ram: 50+idx*8, disk: 30+idx*10,
        status: idx === 2 ? "red" : "green",
        ports: mkPorts(4,"rj",[10,0,idx+2,11],"edge") }),
      dev({ name:`srv-${r.id}-02`, model:"Supermicro SYS-1029U", type:"server", u:1, uStart:36,
        ip:`10.0.${idx+2}.12`, firmware:"BIOS 1.4b",
        cpu: 22, ram: 38, disk: 18,
        ports: mkPorts(4,"rj",[10,0,idx+2,12],"edge") }),
      dev({ name:`ups-${r.id}`, model:"APC Smart-UPS RT 3000", type:"ups", u:2, uStart:3,
        ip:`10.0.${idx+2}.99`, battery: 80+idx, load: 25+idx*5, ports: [] }),
    ];
  });

  // Events
  const events = [
    { ts:"2026-04-19 14:02:31", sev:"crit", device:"srv-gpu-01", rack:"Rack 01", desc:"Температура CPU 94°C — превышен критический порог", resolved:false, detail:"CPU0 temp spike at 14:02:29. Fan speed: 100%. Consider workload migration." },
    { ts:"2026-04-19 13:58:10", sev:"warn", device:"srv-db-01",  rack:"Rack 01", desc:"Использование памяти 91% — приближается к лимиту", resolved:false, detail:"RSS 91.4GB of 100GB. PG autovacuum running." },
    { ts:"2026-04-19 13:44:02", sev:"warn", device:"sw-core-01", rack:"Rack 01", desc:"Порт Gi0/12: рост ошибок CRC (22/мин)", resolved:false, detail:"CRC errors rising since 13:38. Possible faulty cable." },
    { ts:"2026-04-19 13:30:47", sev:"info", device:"mt-core-01", rack:"Rack 01", desc:"BGP peer 185.xx.xx.xx восстановлен", resolved:true, detail:"Session re-established after 12s downtime." },
    { ts:"2026-04-19 12:51:13", sev:"crit", device:"srv-r04-01", rack:"Rack 04", desc:"Диск sda: предсказание сбоя SMART", resolved:false, detail:"SMART attribute 5 (Reallocated_Sector_Ct) = 134, rising." },
    { ts:"2026-04-19 12:14:08", sev:"info", device:"ups-apc-01", rack:"Rack 01", desc:"Самотестирование пройдено", resolved:true, detail:"Last self-test OK. Battery runtime: 18m @ current load." },
    { ts:"2026-04-19 11:03:22", sev:"info", device:"sw-r02",     rack:"Rack 02", desc:"Новое устройство обнаружено: Gi0/4 → 10.0.2.14", resolved:true, detail:"LLDP discovered srv-r02-03." },
    { ts:"2026-04-19 10:44:02", sev:"warn", device:"srv-app-01", rack:"Rack 01", desc:"Задержка диска > 80мс на /dev/sdb", resolved:true, detail:"Await avg 92ms for 3 minutes. Recovered." },
    { ts:"2026-04-19 09:21:11", sev:"info", device:"mt-core-01", rack:"Rack 01", desc:"Конфигурация изменена: user admin", resolved:true, detail:"Change: /ip firewall filter add ..." },
    { ts:"2026-04-19 08:02:55", sev:"info", device:"sw-r03",     rack:"Rack 03", desc:"Обновление прошивки успешно", resolved:true, detail:"IOS 15.2(7)E3 → 15.2(7)E4" },
  ];

  const alerts = [
    { name: "CPU > 90%", cond: "load_avg > 90 за 2 мин", level: "warn", channel: "Telegram", on: true },
    { name: "RAM > 85%", cond: "used_mem > 85% за 5 мин", level: "warn", channel: "Email", on: true },
    { name: "Диск > 80%", cond: "fs_used > 80%", level: "warn", channel: "Telegram", on: true },
    { name: "Температура CPU > 85°C", cond: "temp > 85 сразу", level: "crit", channel: "SMS + Telegram", on: true },
    { name: "Пинг потерян", cond: "icmp loss > 50% за 1 мин", level: "crit", channel: "SMS", on: true },
    { name: "Порт down", cond: "ifOperStatus = down", level: "info", channel: "Email", on: false },
    { name: "Ошибки CRC", cond: "crc_errors > 10/мин", level: "warn", channel: "Telegram", on: true },
  ];

  return { racks, events, alerts };
})();
