module.exports = {
  apps: [
    {
      name: 'rag-api',
      cwd: 'G:/RAG',
      script: 'python.exe',
      args: '-m uvicorn api.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      max_restarts: 3,
      min_uptime: '5s',
      restart_delay: 2000,
      autorestart: true,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
      },
    },
    {
      name: 'rag-web',
      cwd: 'G:/RAG/web',
      script: 'node_modules/vite/bin/vite.js',
      args: '--host',
      max_restarts: 3,
      min_uptime: '5s',
    },
    {
      name: 'rag-dashboard',
      cwd: 'G:/RAG/dashboard',
      script: 'server.js',
      max_restarts: 3,
      min_uptime: '5s',
    },
  ],
}
