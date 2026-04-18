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

/**
 * Stream a chat message via SSE.
 * Calls onEvent(event) for each parsed SSE event until "done".
 * Pass an AbortSignal to cancel the stream.
 */
export async function streamMessage(message, history, llmMode, onEvent, signal, userDecisions) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, llm_mode: llmMode, user_decisions: userDecisions || {} }),
    signal,
  })
  if (!res.ok) throw new Error(`Stream failed: ${res.status}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let receivedDone = false

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE lines are separated by \n\n
      const parts = buffer.split('\n\n')
      buffer = parts.pop() // keep incomplete trailing chunk

      for (const part of parts) {
        const line = part.trim()
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'done') receivedDone = true
            onEvent(event)
          } catch {
            // malformed JSON — skip
          }
        }
      }
    }
  } finally {
    // Guarantee cleanup: synthesize done if stream ended without one
    if (!receivedDone) {
      onEvent({ type: 'done', clean_text: '' })
    }
    try { reader.releaseLock() } catch { /* already released */ }
  }
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
