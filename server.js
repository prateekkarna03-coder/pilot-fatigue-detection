const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');
const { WebSocketServer } = require('ws');

const dev = process.env.NODE_ENV !== 'production';
const hostname = 'localhost';
const port = 3000;
const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = createServer(async (req, res) => {
    try {
      const parsedUrl = parse(req.url, true);
      if (req.url.startsWith('/api')) {
        await handle(req, res);
      } else {
        await handle(req, res, parsedUrl);
      }
    } catch (err) {
      console.error('Error occurred handling', req.url, err);
      res.statusCode = 500;
      res.end('internal server error');
    }
  });

  const wss = new WebSocketServer({ noServer: true });
  
  server.on('upgrade', (req, socket, head) => {
    const { pathname, query } = parse(req.url, true);
    if (pathname === '/ws' && (query.role === 'subscriber' || query.role === 'publisher' ||
        query.role === 'frame-subscriber' || query.role === 'frame-publisher')) {
      wss.handleUpgrade(req, socket, head, (ws) => {
        wss.emit('connection', ws, req);
      });
    } else if (pathname.startsWith('/_next')) {
      // Let Next.js internal upgradeHandler handle HMR and Next.js internal upgrades
      return;
    } else {
      console.warn(`[WS] Rejecting unknown upgrade path: ${pathname || req.url}`);
      socket.destroy();
    }
  });

  const subscribers = new Set();
  const frameSubscribers = new Set();
  let publisherSocket = null;
  let publisherGeneration = 0;

  wss.on('connection', (ws, req) => {
    const url = parse(req.url, true);
    const role = url.query.role; 
    
    if (role === 'subscriber') {
      console.log(`[WS] Subscriber connected. total=${subscribers.size + 1}`);
      subscribers.add(ws);
      ws.on('error', (err) => {
        console.error('[WS] Subscriber error:', err.message);
      });
      ws.on('close', (code, reason) => {
        subscribers.delete(ws);
        console.log(`[WS] Subscriber disconnected. code=${code} reason=${reason.toString() || 'none'} remaining=${subscribers.size}`);
      });
    } else if (role === 'frame-subscriber') {
      console.log(`[WS] Camera frame subscriber connected. total=${frameSubscribers.size + 1}`);
      frameSubscribers.add(ws);
      ws.on('error', (err) => {
        console.error('[WS] Camera frame subscriber error:', err.message);
      });
      ws.on('close', (code, reason) => {
        frameSubscribers.delete(ws);
        console.log(`[WS] Camera frame subscriber disconnected. code=${code} reason=${reason.toString() || 'none'}`);
      });
    } else if (role === 'frame-publisher') {
      console.log('[WS] Camera frame publisher connected.');
      ws.on('error', (err) => {
        console.error('[WS] Camera frame publisher error:', err.message);
      });
      ws.on('close', (code, reason) => {
        console.log(`[WS] Camera frame publisher disconnected. code=${code} reason=${reason.toString() || 'none'}`);
      });
      ws.on('message', (data, isBinary) => {
        if (!isBinary) return;
        for (const subscriber of frameSubscribers) {
          if (subscriber.readyState === 1) {
            subscriber.send(data, { binary: true });
          }
        }
      });
    } else if (role === 'publisher') {
      publisherGeneration++;
      ws.generation = publisherGeneration;
      if (publisherSocket && publisherSocket.readyState === 1) {
        console.warn(`[WS] Replacing existing publisher connection. oldGeneration=${publisherSocket.generation} newGeneration=${ws.generation}`);
        publisherSocket.close(1000, 'Replaced by newer publisher');
      }
      publisherSocket = ws;
      console.log(`[WS] Publisher connected. generation=${ws.generation}`);
      ws.on('error', (err) => {
        console.error(`[WS] Publisher error. generation=${ws.generation}:`, err.message);
      });
      ws.on('close', (code, reason) => {
        console.log(`[WS] Publisher disconnected. generation=${ws.generation} code=${code} reason=${reason.toString() || 'none'}`);
        if (publisherSocket === ws) publisherSocket = null;
      });
      ws.on('message', async (data) => {
        try {
          const messageStr = data.toString();
          const pData = JSON.parse(messageStr);
          pData.generation = ws.generation;
          const enrichedStr = JSON.stringify(pData);

          console.log(`[WS] Telemetry received. sessionId=${pData.sessionId} sequence=${pData.sequence} generation=${ws.generation} timestamp=${pData.timestamp} subscribers=${subscribers.size}`);
          if (subscribers.size === 0) {
            console.warn(`[WS] Diagnostic: Telemetry received for session ${pData.sessionId} but subscriber count is 0. No browser dashboard is currently subscribed.`);
          }

          // Broadcast to connected web clients instantly
          for (const sub of subscribers) {
            if (sub.readyState === 1) { // 1 is WebSocket.OPEN
              sub.send(enrichedStr);
            }
          }

          // Offload persistence & Risk Engine logic to the Next.js API route 
          // via internal fetch. This keeps TypeScript business logic out of this raw JS server.
          fetch(`http://${hostname}:${port}/api/telemetry`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-telemetry-token': process.env.NEXTAUTH_SECRET || ''
            },
            body: enrichedStr
          }).then((response) => {
            if (!response.ok) {
              console.error(`[WS] Telemetry API rejected sample: HTTP ${response.status}`);
            }
          }).catch(err => {
            console.error("[WS] Failed to POST telemetry to API:", err.message);
          });

        } catch (e) {
          console.error("[WS] Error parsing publisher message:", e);
        }
      });
    } else {
      ws.close();
    }
  });

  server.once('error', (err) => {
    console.error(err);
    process.exit(1);
  });

  server.listen(port, () => {
    console.log(`> WebSocket+Next.js server ready on http://${hostname}:${port}`);
  });
});
