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
    :root { color-scheme: dark; }
    body { font-family: system-ui, sans-serif; margin: 20px; background: #101214; color: #eef1f3; }
    h1 { margin: 0 0 4px; font-size: 28px; }
    h2 { margin: 0 0 12px; font-size: 18px; }
    .muted { color: #a6b0b8; margin-top: 0; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }
    .card { background: #1a1f24; border: 1px solid #313941; border-radius: 8px; padding: 14px; }
    .row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    input, select, button { padding: 8px; border-radius: 6px; border: 1px solid #4a5662; background: #12161a; color: #eef1f3; }
    button { cursor: pointer; background: #26323c; }
    button:hover { background: #314251; }
    label { display: inline-flex; gap: 6px; align-items: center; }
    pre { background: #080a0c; padding: 10px; border-radius: 6px; overflow: auto; min-height: 140px; max-height: 320px; }
    #log { min-height: 260px; }
  </style>
</head>
<body>
  <h1>Wireless Dev Bridge</h1>
  <p class="muted">ESP32-S3 + nRF24L01+ V1 dashboard</p>

  <div class="grid">
    <section class="card">
      <h2>Status</h2>
      <pre id="status">Connecting...</pre>
      <button onclick="getStatus()">Refresh</button>
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
        <button onclick="setConfig()">Apply</button>
      </div>
    </section>

    <section class="card">
      <h2>RF Send</h2>
      <div class="row">
        <input id="txhex" placeholder="Hex payload, e.g. 68656C6C6F" size="34">
        <label><input type="checkbox" id="requireAck"> Require ACK</label>
        <button onclick="sendRf()">Send RF</button>
      </div>
    </section>

    <section class="card">
      <h2>Bridge</h2>
      <label><input type="checkbox" id="rf2wifi" checked onchange="setBridge()"> RF -> Wi-Fi/WebSocket</label>
    </section>
  </div>

  <section class="card" style="margin-top:14px">
    <div class="row">
      <h2 style="margin-right:auto">Live Packet Log</h2>
      <button onclick="clearLog()">Clear</button>
    </div>
    <pre id="log"></pre>
  </section>

<script>
let ws;
const logEl = document.getElementById('log');
const statusEl = document.getElementById('status');

function log(x) {
  logEl.textContent += x + '\n';
  logEl.scrollTop = logEl.scrollHeight;
}

function clearLog() {
  logEl.textContent = '';
}

function unwrap(res) {
  return res && res.data ? res.data : res;
}

async function api(path, body) {
  const r = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? {'Content-Type': 'application/json'} : {},
    body: body ? JSON.stringify(body) : undefined
  });
  return await r.json();
}

async function getStatus() {
  const res = await api('/api/status');
  const data = unwrap(res);
  statusEl.textContent = JSON.stringify(data, null, 2);
  if (data.radio) {
    document.getElementById('channel').value = data.radio.channel;
    document.getElementById('datarate').value = data.radio.datarate;
    document.getElementById('power').value = data.radio.power;
    document.getElementById('autoAck').checked = !!data.radio.auto_ack;
  }
  if (data.bridge) document.getElementById('rf2wifi').checked = !!data.bridge.rf_to_wifi;
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

async function sendRf() {
  const hex = document.getElementById('txhex').value.trim();
  const require_ack = document.getElementById('requireAck').checked;
  const res = await api('/api/rf/send', {hex, require_ack});
  log('TX ' + JSON.stringify(res));
  getStatus();
}

async function setBridge() {
  const rf_to_wifi = document.getElementById('rf2wifi').checked;
  const res = await api('/api/bridge', {rf_to_wifi});
  log('BRIDGE ' + JSON.stringify(res));
}

function connectWs() {
  ws = new WebSocket('ws://' + location.hostname + ':81/');
  ws.onopen = () => log('WebSocket connected');
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'packet') log('RX ' + JSON.stringify(msg.data || msg));
      if (msg.type === 'status') statusEl.textContent = JSON.stringify(msg.data || msg, null, 2);
      if (msg.ok !== undefined) log('CMD ' + JSON.stringify(msg));
    } catch (e) {
      log(ev.data);
    }
  };
  ws.onclose = () => setTimeout(connectWs, 1000);
}

getStatus();
connectWs();
setInterval(getStatus, 5000);
</script>
</body>
</html>
)HTML";
