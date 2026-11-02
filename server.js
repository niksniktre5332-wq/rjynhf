// Контра — сайт и онлайн-сервер в одном файле.
// Запуск: npm install && npm start   →   http://localhost:3000
const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');

const PORT = process.env.PORT || 3000;
const PUB = path.join(__dirname, 'public');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.json': 'application/json', '.zip': 'application/zip' };

const server = http.createServer((req, res) => {
  let url;
  try { url = decodeURIComponent(req.url.split('?')[0]); } catch (e) { res.writeHead(400); return res.end(); }
  if (url === '/') url = '/index.html';
  if (url === '/play') url = '/play.html';
  const file = path.join(PUB, path.normalize(url));
  if (!file.startsWith(PUB)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' }); return res.end('Страница не найдена'); }
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-cache' });
    res.end(buf);
  });
});

// ===== онлайн-комнаты =====
const wss = new WebSocketServer({ server, path: '/ws', maxPayload: 64 * 1024 });
const rooms = new Map();
let seq = 0;
const send = (ws, o) => { if (ws.readyState === 1) ws.send(JSON.stringify(o)); };
const list = r => [...r].map(c => ({ peer: c.id, presence: c.pres || null }));
const bcast = (r, o, except) => { const s = JSON.stringify(o); for (const c of r) if (c !== except && c.readyState === 1) c.send(s); };

wss.on('connection', ws => {
  ws.id = 'p' + (++seq).toString(36) + Math.random().toString(36).slice(2, 6);
  ws.room = null; ws.alive = true; ws.tokens = 60; ws.last = Date.now();
  ws.on('pong', () => { ws.alive = true; });
  ws.on('message', raw => {
    // простая защита от флуда: не больше ~40 сообщений в секунду
    const now = Date.now(); ws.tokens = Math.min(60, ws.tokens + (now - ws.last) * 0.04); ws.last = now;
    if (ws.tokens < 1) return; ws.tokens--;
    let m; try { m = JSON.parse(raw); } catch (e) { return; }
    if (!m || typeof m !== 'object') return;
    if (m.t === 'join' && !ws.room) {
      const name = String(m.room || 'pub').slice(0, 40);
      let r = rooms.get(name); if (!r) rooms.set(name, r = new Set());
      if (r.size >= 32) { send(ws, { t: 'full' }); return ws.close(); }
      ws.room = name; r.add(ws);
      send(ws, { t: 'hello', id: ws.id });
      bcast(r, { t: 'peers', list: list(r) });
      return;
    }
    const r = ws.room && rooms.get(ws.room); if (!r) return;
    if (m.t === 'pres') { ws.pres = m.d; bcast(r, { t: 'pres', peer: ws.id, d: m.d }, ws); }
    else if (m.t === 'emit' && typeof m.topic === 'string') bcast(r, { t: 'msg', peer: ws.id, topic: m.topic.slice(0, 16), d: m.d }, ws);
  });
  ws.on('close', () => {
    const r = ws.room && rooms.get(ws.room); if (!r) return;
    r.delete(ws);
    if (!r.size) rooms.delete(ws.room); else bcast(r, { t: 'peers', list: list(r) });
  });
});
setInterval(() => { for (const ws of wss.clients) { if (!ws.alive) { ws.terminate(); continue; } ws.alive = false; ws.ping(); } }, 30000);

server.listen(PORT, () => console.log('Контра запущена: http://localhost:' + PORT));
