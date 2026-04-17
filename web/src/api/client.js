const BASE = '/api'

export async function sendMessage(message, history, llmMode) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, llm_mode: llmMode }),
  })
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`)
  return res.json()
}

export async function getProducts(params = {}) {
  const query = new URLSearchParams(params).toString()
  const res = await fetch(`${BASE}/products?${query}`)
  if (!res.ok) throw new Error(`Products failed: ${res.status}`)
  return res.json()
}

export async function getProductStats() {
  const res = await fetch(`${BASE}/products/stats`)
  if (!res.ok) throw new Error(`Stats failed: ${res.status}`)
  return res.json()
}
