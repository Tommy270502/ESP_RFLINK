#pragma once
#include <Arduino.h>

static const char WEB_UI_HTML[] PROGMEM = R"HTML(
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Wireless Dev Bridge</title>
  <style>
    :root { color-scheme: dark; --bg:#111315; --panel:#1b2024; --line:#39444d; --text:#eef2f3; --muted:#a9b5bc; --accent:#29b6a8; --warn:#f0a33a; --bad:#ef6b6b; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; background: var(--bg); color: var(--text); }
    header { padding: 18px 18px 8px; display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; border-bottom: 1px solid #252c31; }
    h1 { margin: 0; font-size: 24px; }
    h2 { margin: 0 0 12px; font-size: 16px; }
    .muted { color: var(--muted); }
    .wrap { padding: 16px 18px 22px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }
    .card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; min-width: 0; }
    .row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .stack { display: grid; gap: 8px; }
    .kv { display: grid; grid-template-columns: 110px 1fr; gap: 6px 10px; font-size: 14px; }
    .kv span:nth-child(odd) { color: var(--muted); }
    input, select, button { padding: 8px; border-radius: 6px; border: 1px solid #4b5962; background: #121619; color: var(--text); font: inherit; }
    input[type="number"] { width: 86px; }
    input[type="text"], input[type="password"] { min-width: 0; }
    button { cursor: pointer; background: #26323a; }
    button:hover { background: #31434b; }
    button.primary { border-color: #2fc5b6; background: #123a37; }
    button.warn { border-color: #c78527; background: #3a2812; }
    label { display: inline-flex; gap: 6px; align-items: center; }
    pre { background: #080a0c; padding: 10px; border-radius: 6px; overflow: auto; min-height: 150px; max-height: 320px; white-space: pre-wrap; }
    #log { min-height: 260px; }
    .pill { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 3px 8px; font-size: 12px; color: var(--muted); }
    .ok { color: var(--accent); }
    .bad { color: var(--bad); }
    @media (max-width: 700px) { header, .wrap { padding-left: 12px; padding-right: 12px; } .kv { grid-template-columns: 92px 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>Wireless Dev Bridge</h1>
    <span class="pill" id="identity">Connecting...</span>
    <span class="muted">ESP32-S3 + nRF24L01+ developer dashboard</span>
  </header>

  <main class="wrap">
    <div class="grid">
      <section class="card">
        <h2>Device</h2>
        <div class="kv" id="summary"></div>
        <div class="row" style="margin-top:12px">
          <button class="primary" onclick="sendCommand('identify')">Identify</button>
          <button onclick="sendCommand('self_test')">Self Test</button>
          <button onclick="sendCommand('diagnostics')">Diagnostics</button>
          <button onclick="exportReport()">Export Report</button>
        </div>
      </section>

      <section class="card">
        <h2>RF Config</h2>
        <div class="row">
          <label>Channel <input id="channel" type="number" min="0" max="125" value="76"></label>
          <label>Datarate
            <select id="datarate">
              <option>250kbps</option>
              <option selected>1mbps</option>
              <option>2mbps</option>
            </select>
          </label>
          <label>Power
            <select id="power">
              <option>min</option>
              <option selected>low</option>
              <option>high</option>
              <option>max</option>
            </select>
          </label>
          <label><input type="checkbox" id="autoAck" checked> Auto ACK</label>
          <button class="primary" onclick="setConfig()">Apply</button>
        </div>
      </section>

      <section class="card">
        <h2>Addresses</h2>
        <div class="stack">
          <label>Format
            <select id="addrFormat">
              <option selected>ascii</option>
              <option>hex</option>
            </select>
          </label>
          <label>RX <input id="rxaddr" value="NODE1" maxlength="10"></label>
          <label>TX <input id="txaddr" value="NODE2" maxlength="10"></label>
          <div class="row">
            <button onclick="preset('NODE1','NODE2')">Node 1</button>
            <button onclick="preset('NODE2','NODE1')">Node 2</button>
            <button class="primary" onclick="setAddress()">Apply</button>
          </div>
        </div>
      </section>

      <section class="card">
        <h2>RF Send</h2>
        <div class="stack">
          <label>Mode
            <select id="payloadMode" onchange="updatePayloadCount()">
              <option selected>Text</option>
              <option>Hex</option>
            </select>
          </label>
          <input id="payload" placeholder="hello or 68656C6C6F" value="hello" oninput="updatePayloadCount()">
          <span class="muted" id="payloadCount">5/32 bytes</span>
          <label><input type="checkbox" id="requireAck"> Require ACK</label>
          <button class="primary" onclick="sendRf()">Send RF</button>
        </div>
      </section>

      <section class="card">
        <h2>Bridge</h2>
        <div class="stack">
          <label><input type="checkbox" id="rf2wifi" checked> RF to Wi-Fi/WebSocket</label>
          <label><input type="checkbox" id="rf2ble" checked> RF to BLE notifications</label>
          <button class="primary" onclick="setBridge()">Apply Bridge State</button>
        </div>
      </section>

      <section class="card">
        <h2>Settings</h2>
        <div class="stack">
          <label>Auth token <input id="authToken" type="password" placeholder="optional"></label>
          <label><input type="checkbox" id="authRequired"> Require auth for Wi-Fi/BLE commands</label>
          <div class="row">
            <button onclick="getSettings()">Read</button>
            <button class="primary" onclick="setSecurity()">Apply Security</button>
            <button onclick="sendCommand('settings_save')">Save</button>
            <button class="warn" onclick="sendCommand('settings_reset')">Reset</button>
          </div>
        </div>
      </section>
    </div>

    <section class="card" style="margin-top:14px">
      <div class="row">
        <h2 style="margin-right:auto">Live Log</h2>
        <button onclick="clearLog()">Clear</button>
      </div>
      <pre id="log"></pre>
    </section>
  </main>

<script>
let ws;
let lastStatus = null;
let lastDiagnostics = null;
const logEl = document.getElementById('log');

function log(x, level) {
  const prefix = level === 'error' ? '! ' : '';
  logEl.textContent += prefix + x + '\n';
  logEl.scrollTop = logEl.scrollHeight;
}

function clearLog() { logEl.textContent = ''; }

function authHeaders() {
  const token = document.getElementById('authToken').value.trim();
  return token ? {'X-WDB-Token': token} : {};
}

function withAuth(body) {
  const token = document.getElementById('authToken').value.trim();
  if (token) body.auth = token;
  return body;
}

async function api(path, body) {
  const headers = body ? {'Content-Type': 'application/json', ...authHeaders()} : authHeaders();
  const r = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers,
    body: body ? JSON.stringify(body) : undefined
  });
  const data = await r.json();
  if (!data.ok && data.error) log(data.error.code + ': ' + data.error.message, 'error');
  return data;
}

async function command(body) {
  return api('/api/command', withAuth(body));
}

function dataOf(res) { return res && res.data ? res.data : res; }

function setSummary(data) {
  lastStatus = data;
  const radio = data.radio || {};
  const wifi = data.wifi || {};
  const ble = data.ble || {};
  const storage = data.storage || {};
  const security = data.security || {};
  const stats = data.stats || {};
  const rows = [
    ['Role', data.role || '-'],
    ['Firmware', data.fw || '-'],
    ['Protocol', data.protocol || '-'],
    ['Radio', radio.initialized && radio.chip_connected ? 'ok' : 'check'],
    ['RF', 'ch ' + (radio.channel ?? '-') + ' / ' + (radio.datarate || '-')],
    ['Addresses', (radio.rx_address_ascii || radio.rx_address_hex || '-') + ' -> ' + (radio.tx_address_ascii || radio.tx_address_hex || '-')],
    ['Wi-Fi', (wifi.ip || '-') + ' / ' + (wifi.clients || 0) + ' clients'],
    ['BLE', ble.enabled ? (ble.connected ? 'connected' : 'advertising') : 'disabled'],
    ['Counters', 'RX ' + (stats.rf_rx || 0) + ' / TX ' + (stats.rf_tx || 0) + ' / fail ' + (stats.rf_tx_fail || 0)],
    ['Storage', storage.dirty ? 'unsaved' : (storage.loaded_from_nvs ? 'persisted' : 'defaults')],
    ['Security', security.auth_required ? 'auth required' : 'trusted bench']
  ];
  document.getElementById('summary').innerHTML = rows.map(([k,v]) => '<span>'+k+'</span><span>'+v+'</span>').join('');
  document.getElementById('identity').textContent = (data.device && data.device.id ? data.device.id : data.role || 'device');

  if (radio.channel !== undefined) document.getElementById('channel').value = radio.channel;
  if (radio.datarate) document.getElementById('datarate').value = radio.datarate;
  if (radio.power) document.getElementById('power').value = radio.power;
  if (radio.auto_ack !== undefined) document.getElementById('autoAck').checked = !!radio.auto_ack;
  if (radio.rx_address_ascii || radio.rx_address_hex) document.getElementById('rxaddr').value = radio.rx_address_ascii || radio.rx_address_hex;
  if (radio.tx_address_ascii || radio.tx_address_hex) document.getElementById('txaddr').value = radio.tx_address_ascii || radio.tx_address_hex;
  if (data.bridge) {
    document.getElementById('rf2wifi').checked = !!data.bridge.rf_to_wifi;
    document.getElementById('rf2ble').checked = !!data.bridge.rf_to_ble;
  }
  if (security.auth_required !== undefined) document.getElementById('authRequired').checked = !!security.auth_required;
}

async function getStatus() {
  const res = await api('/api/status');
  const data = dataOf(res);
  if (res.ok) setSummary(data);
}

async function sendCommand(cmd) {
  const res = await command({cmd});
  log(cmd.toUpperCase() + ' ' + JSON.stringify(res));
  if (cmd === 'diagnostics' && res.ok) lastDiagnostics = res.data;
  await getStatus();
}

async function getSettings() {
  const res = await command({cmd:'settings_get'});
  log('SETTINGS ' + JSON.stringify(res));
  if (res.ok && res.data.effective && res.data.effective.security) {
    document.getElementById('authRequired').checked = !!res.data.effective.security.auth_required;
  }
}

async function setConfig() {
  const body = {
    channel: Number(document.getElementById('channel').value),
    datarate: document.getElementById('datarate').value,
    power: document.getElementById('power').value,
    auto_ack: document.getElementById('autoAck').checked
  };
  const res = await api('/api/rf/config', body);
  log('CONFIG ' + JSON.stringify(res));
  getStatus();
}

function payloadHex() {
  const mode = document.getElementById('payloadMode').value;
  const value = document.getElementById('payload').value;
  if (mode === 'Text') {
    return Array.from(new TextEncoder().encode(value)).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
  }
  return value.replace(/^0x/i, '').replace(/\s+/g, '').toUpperCase();
}

function updatePayloadCount() {
  let bytes = 0;
  try {
    bytes = document.getElementById('payloadMode').value === 'Text'
      ? new TextEncoder().encode(document.getElementById('payload').value).length
      : Math.ceil(payloadHex().length / 2);
  } catch (e) {}
  document.getElementById('payloadCount').textContent = bytes + '/32 bytes';
}

async function sendRf() {
  const hex = payloadHex();
  if (!hex || hex.length % 2 || hex.length > 64) {
    log('payload must be 1..32 bytes and valid hex after encoding', 'error');
    return;
  }
  const res = await api('/api/rf/send', {hex, require_ack: document.getElementById('requireAck').checked});
  log('TX ' + JSON.stringify(res));
  getStatus();
}

function preset(rx, tx) {
  document.getElementById('addrFormat').value = 'ascii';
  document.getElementById('rxaddr').value = rx;
  document.getElementById('txaddr').value = tx;
}

async function setAddress() {
  const res = await command({
    cmd:'rf_set_address',
    rx: document.getElementById('rxaddr').value.trim(),
    tx: document.getElementById('txaddr').value.trim(),
    format: document.getElementById('addrFormat').value
  });
  log('ADDRESS ' + JSON.stringify(res));
  getStatus();
}

async function setBridge() {
  const res = await api('/api/bridge', {
    rf_to_wifi: document.getElementById('rf2wifi').checked,
    rf_to_ble: document.getElementById('rf2ble').checked
  });
  log('BRIDGE ' + JSON.stringify(res));
  getStatus();
}

async function setSecurity() {
  const security = {auth_required: document.getElementById('authRequired').checked};
  const token = document.getElementById('authToken').value.trim();
  if (token) security.auth_token = token;
  const res = await command({cmd:'settings_set', security});
  log('SECURITY ' + JSON.stringify(res));
  getStatus();
}

async function exportReport() {
  const diag = lastDiagnostics || dataOf(await command({cmd:'diagnostics'}));
  const report = {
    generated_at: new Date().toISOString(),
    source: 'browser-dashboard',
    status: lastStatus,
    diagnostics: diag,
    log: logEl.textContent.split('\n').filter(Boolean).slice(-120)
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'wireless-dev-bridge-report.json';
  a.click();
  URL.revokeObjectURL(a.href);
}

function connectWs() {
  ws = new WebSocket('ws://' + location.hostname + ':81/');
  ws.onopen = () => log('WebSocket connected');
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'packet') log('RX ' + JSON.stringify(msg.data || msg));
      else if (msg.type === 'status') setSummary(msg.data || msg);
      else if (msg.ok !== undefined) log('CMD ' + JSON.stringify(msg));
    } catch (e) {
      log(ev.data);
    }
  };
  ws.onclose = () => setTimeout(connectWs, 1000);
}

updatePayloadCount();
getStatus();
connectWs();
setInterval(getStatus, 5000);
</script>
</body>
</html>
)HTML";
