const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT || 3001);
const PUBLIC_MODE = String(process.env.PUBLIC_MODE || '').toLowerCase() === 'true';

const PUBLIC_DIR = path.join(__dirname, 'public');

function send(res, statusCode, body, contentType = 'text/plain; charset=utf-8') {
  res.writeHead(statusCode, { 'Content-Type': contentType });
  res.end(body);
}

function sendJson(res, statusCode, payload) {
  send(res, statusCode, JSON.stringify(payload), 'application/json; charset=utf-8');
}

function serveHtml(res, fileName) {
  const filePath = path.join(PUBLIC_DIR, fileName);
  fs.readFile(filePath, (err, data) => {
    if (err) {
      sendJson(res, 500, { detail: `Failed to read ${fileName}` });
      return;
    }
    send(res, 200, data, 'text/html; charset=utf-8');
  });
}

function isPublicModeBlockedPath(pathname) {
  if (pathname === '/sop' || pathname === '/query') return true;
  if (pathname === '/api/sop/forecast') return true;
  if (pathname === '/notes' || pathname === '/api/sop/query') return true;
  return false;
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  if (PUBLIC_MODE && isPublicModeBlockedPath(pathname)) {
    sendJson(res, 404, { detail: 'Not found in PUBLIC_MODE' });
    return;
  }

  if (req.method === 'GET' && (pathname === '/' || pathname === '/index')) {
    serveHtml(res, 'index.html');
    return;
  }

  if (req.method === 'GET' && pathname === '/edgar') {
    serveHtml(res, 'edgar.html');
    return;
  }

  if (req.method === 'GET' && pathname === '/query') {
    serveHtml(res, 'query.html');
    return;
  }

  if (req.method === 'GET' && pathname === '/sop') {
    serveHtml(res, 'sop.html');
    return;
  }

  sendJson(res, 404, { detail: 'Not found' });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`notes-api listening on http://127.0.0.1:${PORT} (PUBLIC_MODE=${PUBLIC_MODE})`);
});
