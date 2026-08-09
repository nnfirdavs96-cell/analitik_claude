// ============================================================
// RackMap · моковые данные
// ============================================================
const DATA = {
  // ------------------ Комната: 5 стоек ------------------
  racks: [
    { id: 'R-01', name: 'Rack 01', status: 'ok',   devices: 9,  online: 9,  power: '3.4/6.0 кВт', load: 57, temp: '22°C' },
    { id: 'R-02', name: 'Rack 02', status: 'ok',   devices: 11, online: 11, power: '4.1/6.0 кВт', load: 68, temp: '23°C' },
    { id: 'R-03', name: 'Rack 03', status: 'warn', devices: 8,  online: 7,  power: '5.2/6.0 кВт', load: 87, temp: '27°C' },
    { id: 'R-04', name: 'Rack 04', status: 'err',  devices: 10, online: 8,  power: '2.9/6.0 кВт', load: 48, temp: '29°C' },
    { id: 'R-05', name: 'Rack 05', status: 'ok',   devices: 9,  online: 9,  power: '3.8/6.0 кВт', load: 63, temp: '22°C' },
  ],

  rackDetails: {
    'R-01': {
      uHeight: 42,
      devices: [
        stubDevice('rtr-branch-01', 'router', 'Mikrotik RB4011', '10.0.1.1', 1, 1, 'ok'),
        stubDevice('sw-branch-01',  'switch', 'Cisco C9200-24T', '10.0.1.2', 3, 1, 'ok'),
        stubDevice('srv-file-01',   'server', 'Dell R650',       '10.0.1.10', 5, 2, 'ok'),
        stubDevice('srv-mail-01',   'server', 'Dell R650',       '10.0.1.11', 8, 2, 'ok'),
        stubDevice('patch-01',      'patch',  'Legrand LCS3 24', '—',        11, 1, 'ok'),
        stubDevice('ups-01',        'ups',    'APC SRT 3000',    '10.0.99.201', 40, 3, 'ok'),
      ],
    },

    'R-02': {
      uHeight: 42,
      devices: [
        richDevice({
          id:'core-rtr-01', kind:'router', name:'core-rtr-01', model:'Mikrotik RB4011iGS+',
          ip:'10.0.0.1', mac:'74:4D:28:A1:10:02', sn:'MTK-4011-192734',
          u:1, uSize:1, firmware:'RouterOS 7.14.3', status:'ok',
          cpu:38, ram:62, disk:14, ping:0.2, uptime:'64d 11h',
          notes:'Основной граничный маршрутизатор. Uplink к Ростелекому на SFP+ 1, резерв на SFP+ 2.',
          seen:'2026-04-19 16:42:03',
          ports: [
            { n:1, type:'SFP+', ip:'203.0.113.2/30',  peer:'ISP-Rostelecom',           cable:'LC-LC OS2', speed:'10G', vlan:'trunk', status:'ok' },
            { n:2, type:'SFP+', ip:'198.51.100.2/30', peer:'ISP-ER-Telecom',           cable:'LC-LC OS2', speed:'10G', vlan:'trunk', status:'ok' },
            { n:3, type:'RJ45', ip:'10.0.10.1/24',    peer:'dist-sw-01 / Gi1/0/1',     cable:'Cat6a',     speed:'1G',  vlan:'10',    status:'ok' },
            { n:4, type:'RJ45', ip:'10.0.20.1/24',    peer:'dist-sw-02 / Gi1/0/1',     cable:'Cat6a',     speed:'1G',  vlan:'20',    status:'ok' },
            { n:5, type:'RJ45', ip:'10.0.30.1/24',    peer:'srv-db-01',                cable:'Cat5e',     speed:'1G',  vlan:'30',    status:'warn' },
            { n:6, type:'RJ45', ip:'—',               peer:'—',                        cable:'—',         speed:'—',   vlan:'—',     status:'empty' },
            { n:7, type:'RJ45', ip:'—',               peer:'—',                        cable:'—',         speed:'—',   vlan:'—',     status:'empty' },
            { n:8, type:'RJ45', ip:'10.0.99.1/24',    peer:'mgmt-sw / 24',             cable:'Cat6',      speed:'1G',  vlan:'99',    status:'ok' },
            { n:9, type:'RJ45', ip:'—',               peer:'неизв.',                    cable:'—',         speed:'—',   vlan:'—',     status:'err' },
            { n:10,type:'RJ45', ip:'—',               peer:'—',                        cable:'—',         speed:'—',   vlan:'—',     status:'empty' },
          ],
        }),
        richDevice({
          id:'dist-sw-01', kind:'switch', name:'dist-sw-01', model:'Cisco Catalyst 9300-24T',
          ip:'10.0.10.2', mac:'00:1E:BE:44:AA:01', sn:'FCW2412L0M9',
          u:3, uSize:1, firmware:'IOS-XE 17.9.4a', status:'ok',
          cpu:24, ram:51, disk:22, ping:0.4, uptime:'128d 03h',
          notes:'Распределительный коммутатор блока A. Стекирован с dist-sw-02 через 40G DAC.',
          seen:'2026-04-19 16:42:01',
          ports: Array.from({length:24}, (_,i) => ({
            n:i+1, type:'RJ45',
            ip: i < 20 ? `10.0.10.${i+10}` : '—',
            peer: i < 20 ? `srv-app-${String(i+1).padStart(2,'0')}` : '—',
            cable: i < 20 ? 'Cat6' : '—',
            speed: i < 20 ? '1G' : '—',
            vlan: i < 12 ? '10' : (i < 20 ? '40' : '—'),
            status: i === 17 ? 'err' : (i < 20 ? 'ok' : 'empty'),
          })),
        }),
        richDevice({
          id:'srv-web-01', kind:'server', name:'srv-web-01', model:'Dell PowerEdge R650',
          ip:'10.0.10.21', mac:'18:66:DA:C2:11:01', sn:'6HXQ8P3',
          u:5, uSize:2, firmware:'BIOS 2.9.3 / iDRAC 5.10', status:'ok',
          cpu:62, ram:74, disk:58, ping:0.3, uptime:'31d 07h',
          notes:'Web-frontend nginx + keepalived. В паре с srv-web-02 (R-03/U-07).',
          seen:'2026-04-19 16:42:07',
          ports: [
            { n:1, type:'RJ45',  ip:'10.0.10.21/24', peer:'dist-sw-01 / Gi1/0/11', cable:'Cat6',  speed:'1G',   vlan:'10', status:'ok' },
            { n:2, type:'RJ45',  ip:'10.0.99.21/24', peer:'mgmt-sw / 8',           cable:'Cat6',  speed:'1G',   vlan:'99', status:'ok' },
            { n:3, type:'IDRAC', ip:'10.0.99.121',   peer:'mgmt-sw / 18',          cable:'Cat5e', speed:'100M', vlan:'99', status:'ok' },
          ],
        }),
        richDevice({
          id:'srv-db-01', kind:'server', name:'srv-db-01', model:'Dell PowerEdge R740',
          ip:'10.0.30.10', mac:'18:66:DA:C2:22:02', sn:'2K9L1M7',
          u:8, uSize:2, firmware:'BIOS 2.14.1', status:'warn',
          cpu:81, ram:88, disk:76, ping:0.5, uptime:'212d 02h',
          notes:'PostgreSQL primary. Высокая нагрузка I/O. Проверить рейд BBU.',
          seen:'2026-04-19 16:41:59',
          ports: [
            { n:1, type:'RJ45', ip:'10.0.30.10/24', peer:'core-rtr-01 / 5', cable:'Cat5e', speed:'1G', vlan:'30', status:'warn' },
            { n:2, type:'RJ45', ip:'10.0.30.11/24', peer:'dist-sw-02 / 5',  cable:'Cat6',  speed:'1G', vlan:'30', status:'ok' },
          ],
        }),
        richDevice({
          id:'patch-panel-02', kind:'patch', name:'patch-panel-02', model:'Legrand LCS3 24-port',
          ip:'—', mac:'—', sn:'PP-24-000232',
          u:11, uSize:1, firmware:'—', status:'ok',
          cpu:null, ram:null, disk:null, ping:'—', uptime:'—',
          notes:'Патч-панель к офисным розеткам 1–24.',
          seen:'—',
          ports: Array.from({length:24}, (_,i) => ({
            n:i+1, type:'Cat6', ip:'—', peer:`OFFICE-${String(i+1).padStart(2,'0')}`,
            cable:'Cat6', speed:'—', vlan:'—',
            status: i < 18 ? 'ok' : 'empty',
          })),
        }),
        richDevice({
          id:'ups-apc-01', kind:'ups', name:'ups-apc-01', model:'APC Smart-UPS SRT 5000',
          ip:'10.0.99.200', mac:'00:C0:B7:99:01:02', sn:'AS1637121103',
          u:40, uSize:3, firmware:'UPS 15.3', status:'ok',
          cpu:null, ram:null, disk:null, ping:1.1, uptime:'340d',
          battery:96, loadPct:42,
          notes:'Заряд 96%. Автотест батарей — ежемесячно. Следующий: 28.04.2026.',
          seen:'2026-04-19 16:42:00',
          ports: [
            { n:1, type:'RJ45', ip:'10.0.99.200', peer:'mgmt-sw / 24', cable:'Cat5e', speed:'100M', vlan:'99', status:'ok' },
          ],
        }),
      ],
    },
  },

  topology: {
    nodes: [
      { id:'isp',  label:'ISP',            sub:'Rostelecom · 10G',    kind:'router', x: 90,  y: 90,  status:'ok' },
      { id:'core', label:'core-rtr-01',    sub:'MTK · 10.0.0.1',      kind:'router', x: 320, y: 120, status:'ok' },
      { id:'fw',   label:'fw-edge-01',     sub:'FortiGate 60F',       kind:'router', x: 320, y: 300, status:'ok' },
      { id:'sw1',  label:'dist-sw-01',     sub:'Cisco · 10.0.10.2',   kind:'switch', x: 600, y: 90,  status:'ok' },
      { id:'sw2',  label:'dist-sw-02',     sub:'Cisco · 10.0.20.2',   kind:'switch', x: 600, y: 260, status:'ok' },
      { id:'web',  label:'srv-web-01',     sub:'Dell · 10.0.10.21',   kind:'server', x: 900, y: 50,  status:'ok' },
      { id:'web2', label:'srv-web-02',     sub:'Dell · 10.0.10.22',   kind:'server', x: 900, y: 160, status:'ok' },
      { id:'db',   label:'srv-db-01',      sub:'Dell · 10.0.30.10',   kind:'server', x: 900, y: 300, status:'warn' },
      { id:'sto',  label:'storage-01',     sub:'Synology RS3621',     kind:'server', x: 900, y: 440, status:'ok' },
      { id:'pp',   label:'patch-panel-02', sub:'LCS3 · 24p',          kind:'panel',  x: 600, y: 450, status:'ok' },
      { id:'mgmt', label:'mgmt-sw',        sub:'MTK · CRS328',        kind:'switch', x: 320, y: 480, status:'ok' },
      { id:'ups',  label:'ups-apc-01',     sub:'APC SRT · 5kVA',      kind:'ups',    x: 320, y: 620, status:'ok' },
    ],
    edges: [
      { a:'isp',  b:'core', kind:'fiber', bw:'10 Гбит/с', util:42 },
      { a:'core', b:'fw',   kind:'fiber', bw:'10 Гбит/с', util:10 },
      { a:'core', b:'sw1',  kind:'utp',   bw:'1 Гбит/с',  util:66 },
      { a:'core', b:'sw2',  kind:'utp',   bw:'1 Гбит/с',  util:38 },
      { a:'sw1',  b:'web',  kind:'utp',   bw:'1 Гбит/с',  util:54 },
      { a:'sw1',  b:'web2', kind:'utp',   bw:'1 Гбит/с',  util:48 },
      { a:'sw2',  b:'db',   kind:'cat5e', bw:'1 Гбит/с',  util:71 },
      { a:'sw2',  b:'sto',  kind:'fiber', bw:'10 Гбит/с', util:22 },
      { a:'sw1',  b:'pp',   kind:'utp',   bw:'1 Гбит/с',  util:12 },
      { a:'mgmt', b:'ups',  kind:'utp',   bw:'100 Мбит/с',util: 4 },
      { a:'mgmt', b:'core', kind:'utp',   bw:'1 Гбит/с',  util: 8 },
    ],
  },

  monitoring: [
    { id:'core-rtr-01', loc:'R-02 · U1',  cpu:38, ram:62, disk:14, ping:0.2, uptime:'64d',  status:'ok'   },
    { id:'dist-sw-01',  loc:'R-02 · U3',  cpu:24, ram:51, disk:22, ping:0.4, uptime:'128d', status:'ok'   },
    { id:'dist-sw-02',  loc:'R-03 · U3',  cpu:27, ram:49, disk:22, ping:0.5, uptime:'128d', status:'ok'   },
    { id:'srv-web-01',  loc:'R-02 · U5',  cpu:62, ram:74, disk:58, ping:0.3, uptime:'31d',  status:'ok'   },
    { id:'srv-web-02',  loc:'R-03 · U7',  cpu:58, ram:72, disk:60, ping:0.3, uptime:'30d',  status:'ok'   },
    { id:'srv-db-01',   loc:'R-02 · U8',  cpu:81, ram:88, disk:76, ping:0.5, uptime:'212d', status:'warn' },
    { id:'srv-app-12',  loc:'R-04 · U14', cpu:94, ram:91, disk:89, ping:18,  uptime:'4d',   status:'err'  },
    { id:'storage-01',  loc:'R-05 · U20', cpu:12, ram:42, disk:63, ping:0.6, uptime:'540d', status:'ok'   },
    { id:'ups-apc-01',  loc:'R-02 · U40', cpu: 0, ram: 0, disk: 0, ping:1.1, uptime:'340d', status:'ok'   },
  ],

  alertRules: [
    { name:'Высокая нагрузка CPU', cond:'CPU > 85% на 5 мин', level:'warn', channel:'email, telegram', enabled:true  },
    { name:'Дефицит памяти',       cond:'RAM > 90%',           level:'warn', channel:'telegram',        enabled:true  },
    { name:'Диск близок к полному',cond:'Disk > 80%',          level:'warn', channel:'email',           enabled:true  },
    { name:'Задержки сети',        cond:'Ping > 50 мс',        level:'info', channel:'telegram',        enabled:false },
    { name:'Порт погас',           cond:'Link down',           level:'crit', channel:'email, slack',    enabled:true  },
    { name:'ИБП на батарее',       cond:'onBattery = true',    level:'crit', channel:'email, sms',      enabled:true  },
    { name:'Перегрев стойки',      cond:'T > 28°C',            level:'warn', channel:'email',           enabled:true  },
  ],

  events: [
    { ts:'2026-04-19 16:41:22', sev:'crit', device:'srv-app-12',  rack:'R-04', desc:'Потеря связи — 3 таймаута пинга подряд', resolved:false, detail:'ping 10.0.40.12 timeout ×3. Последний ответ 16:40:58. MAC 18:66:DA:C2:44:0C. Инцидент INC-2026-0418.' },
    { ts:'2026-04-19 16:38:05', sev:'warn', device:'srv-db-01',   rack:'R-02', desc:'CPU 81% > порог 80% в течение 5 минут',  resolved:false, detail:'Длительный autovacuum на events_partition_202604. Рекомендуется пересчёт статистики.' },
    { ts:'2026-04-19 16:12:10', sev:'warn', device:'Rack 03',     rack:'R-03', desc:'Темп. 27.4°C приближается к порогу 28°C',resolved:false, detail:'Датчик T-03. Проверить перфорацию двери и заглушки.' },
    { ts:'2026-04-19 15:47:00', sev:'info', device:'dist-sw-01',  rack:'R-02', desc:'Порт Gi1/0/18: admin shutdown',           resolved:true,  detail:'Исполнитель: a.ivanov. TKT-4412 — замена патч-корда.' },
    { ts:'2026-04-19 14:55:31', sev:'info', device:'core-rtr-01', rack:'R-02', desc:'Конфиг: добавлен BGP neighbor 203.0.113.5', resolved:true, detail:'Резервный пир к ISP #2. RIB проверен.' },
    { ts:'2026-04-19 10:02:17', sev:'warn', device:'ups-apc-01',  rack:'R-02', desc:'Самотест батареи — успех, ёмкость 94%',   resolved:true,  detail:'Плановый тест. Следующий 28.04.2026.' },
    { ts:'2026-04-18 23:18:44', sev:'crit', device:'srv-web-02',  rack:'R-03', desc:'RAID degraded — диск 3 failed',           resolved:true,  detail:'Заменён ночной сменой. Rebuild 14h 22m, завершён 05:40.' },
    { ts:'2026-04-18 12:03:00', sev:'info', device:'—',           rack:'—',   desc:'Плановый бэкап конфигураций — OK',        resolved:true,  detail:'12 конфигов, 4.2 МБ → s3://rackmap-backup/2026-04-18/' },
  ],
};

function stubDevice(id, kind, model, ip, u, uSize, status) {
  return richDevice({
    id, name:id, kind, model, ip,
    mac:'—', sn:'—', u, uSize, firmware:'—', status,
    cpu: kind==='server' ? 40 : (kind==='router' || kind==='switch' ? 25 : null),
    ram: kind==='server' ? 55 : (kind==='router' || kind==='switch' ? 40 : null),
    disk:kind==='server' ? 45 : (kind==='router' || kind==='switch' ? 20 : null),
    ping: 0.5, uptime:'—', notes:'',
    seen:'2026-04-19 16:41:00',
    ports: [],
  });
}
function richDevice(o) { return o; }
