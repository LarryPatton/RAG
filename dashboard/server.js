const http = require('http')
const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const PORT = 7788
const HTML = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf-8')

function pm2Json() {
  try {
    const raw = execSync('pm2 jlist', { encoding: 'utf-8', timeout: 5000 })
    const all = JSON.parse(raw)
    return all.filter(p => p.name.startsWith('rag-'))
  } catch { return [] }
}

function pm2Action(name, action) {
  try {
    execSync(`pm2 ${action} ${name}`, { encoding: 'utf-8', timeout: 10000 })
    return { ok: true }
  } catch (e) {
    return { ok: false, error: e.message }
  }
}

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST')

  if (req.method === 'GET' && req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
    res.end(HTML)
    return
  }

  if (req.method === 'GET' && req.url === '/api/status') {
    const procs = pm2Json()
    const data = procs.map(p => ({
      name: p.name,
      pid: p.pid,
      status: p.pm2_env?.status || 'unknown',
      cpu: p.monit?.cpu || 0,
      mem: p.monit?.memory || 0,
      uptime: p.pm2_env?.pm_uptime || 0,
      restarts: p.pm2_env?.restart_time || 0,
    }))
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify(data))
    return
  }

  if (req.method === 'POST' && req.url.startsWith('/api/')) {
    const parts = req.url.split('/')
    // /api/restart/rag-api  or  /api/stop/rag-api
    const action = parts[2]
    const name = parts[3]
    if (['restart', 'stop', 'start'].includes(action) && name?.startsWith('rag-')) {
      const result = pm2Action(name, action)
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify(result))
      return
    }
  }

  if (req.method === 'POST' && req.url === '/api/restart-all') {
    pm2Action('rag-api', 'restart')
    pm2Action('rag-web', 'restart')
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ ok: true }))
    return
  }

  if (req.method === 'GET' && req.url.startsWith('/api/logs/')) {
    const name = req.url.split('/')[3]
    if (name?.startsWith('rag-')) {
      try {
        const logs = execSync(`pm2 logs ${name} --lines 50 --nostream 2>&1`, { encoding: 'utf-8', timeout: 5000 })
        res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' })
        res.end(logs)
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'text/plain' })
        res.end(e.message)
      }
      return
    }
  }

  res.writeHead(404)
  res.end('Not found')
})

server.listen(PORT, () => {
  console.log(`Dashboard running at http://localhost:${PORT}`)
})
