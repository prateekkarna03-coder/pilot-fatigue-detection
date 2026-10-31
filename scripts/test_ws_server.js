const http = require('http');
const { WebSocketServer } = require('ws');

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(`
    <!DOCTYPE html>
    <html>
      <body>
        <h1>Testing WebSocket</h1>
        <div id="log"></div>
        <script>
          const logDiv = document.getElementById('log');
          function log(msg) {
            console.log(msg);
            const p = document.createElement('p');
            p.textContent = msg;
            logDiv.appendChild(p);
          }
          log('Attempting WS to ws://localhost:3000/?role=subscriber...');
          const ws3000 = new WebSocket('ws://localhost:3000/?role=subscriber');
          ws3000.onopen = () => log('ws3000 OPENED!');
          ws3000.onclose = (e) => log('ws3000 CLOSED! code=' + e.code + ' reason=' + e.reason);
          ws3000.onerror = (e) => log('ws3000 ERROR!');

          log('Attempting WS to ws://localhost:3001/?role=subscriber...');
          const ws3001 = new WebSocket('ws://localhost:3001/?role=subscriber');
          ws3001.onopen = () => log('ws3001 OPENED!');
          ws3001.onclose = (e) => log('ws3001 CLOSED! code=' + e.code + ' reason=' + e.reason);
          ws3001.onerror = (e) => log('ws3001 ERROR!');
        </script>
      </body>
    </html>
  `);
});

const wss = new WebSocketServer({ server });
wss.on('connection', (ws, req) => {
  console.log('PORT 3001: WS CONNECTED! url:', req.url, 'headers:', req.headers);
  ws.on('close', (code, reason) => {
    console.log('PORT 3001: WS CLOSED code:', code, 'reason:', reason.toString());
  });
  ws.on('error', (err) => {
    console.log('PORT 3001: WS ERROR:', err);
  });
});

server.listen(3001, () => {
  console.log('Test WS server listening on http://localhost:3001');
});
