import { useState, useCallback, useRef } from 'react'
import Header from './components/Header'
import ChatPanel from './components/ChatPanel'
import DecisionPanel from './components/DecisionPanel'
import { streamMessage } from './api/client'
import { STAGE_ORDER } from './constants/stages'

/** Extract decisions from user message text in real-time. */
function parseUserDecisions(text) {
  const decisions = {}
  // Split by "+" for multi-select, then parse each part
  const parts = text.split('+').map(p => p.trim()).filter(Boolean)
  const t = text.trim()

  // Type: 入耳式 / 头戴式 / 颈挂式
  if (/入耳/.test(t)) decisions.type = '入耳式'
  else if (/头戴/.test(t)) decisions.type = '头戴式'
  else if (/颈挂/.test(t)) decisions.type = '颈挂式'

  // Budget: collect all numbers, take the widest range
  const allNumbers = []
  for (const part of parts) {
    // Range: "500-1000"
    const rangeMatch = part.match(/(\d{2,5})\s*[-–~到]\s*(\d{2,5})/)
    if (rangeMatch) {
      allNumbers.push(parseInt(rangeMatch[1], 10), parseInt(rangeMatch[2], 10))
      continue
    }
    // "XXX以上"
    const aboveMatch = part.match(/(\d{2,5})\s*(以上|起)/)
    if (aboveMatch) {
      allNumbers.push(parseInt(aboveMatch[1], 10), 99999)
      continue
    }
    // "XXX以内" or plain number
    const numMatch = part.match(/(\d{2,5})\s*(元|以内|块|预算|左右)?/)
    if (numMatch) {
      allNumbers.push(parseInt(numMatch[1], 10))
    }
  }
  if (allNumbers.length > 0) {
    const min = Math.min(...allNumbers.filter(n => n < 99999))
    const max = Math.max(...allNumbers.filter(n => n < 99999))
    if (allNumbers.includes(99999)) {
      decisions.budget = `¥${min}以上`
    } else if (min === max) {
      decisions.budget = `≤¥${max}`
    } else {
      decisions.budget = `¥${min}-${max}`
    }
  }

  // Scenario: collect all matching scenarios
  const scenarios = { '通勤': '通勤', '运动': '运动', '跑步': '运动', '办公': '办公', '游戏': '游戏', '音乐': '音乐欣赏', '睡眠': '睡眠', '学习': '学习' }
  const matched = []
  for (const [kw, val] of Object.entries(scenarios)) {
    if (t.includes(kw) && !matched.includes(val)) matched.push(val)
  }
  if (matched.length > 0) decisions.scenario = matched.join('、')

  // Noise cancellation
  if (/降噪|主动降噪|ANC/.test(t)) decisions.noise_cancellation = '需要降噪'

  // Brand
  const brands = ['Sony', 'Bose', 'AKG', 'JBL', '华为', '小米', 'OPPO', 'vivo', '三星', '森海塞尔', '铁三角', 'Beats', '漫步者', 'FIIL', '万魔', '魅族', 'Jabra', 'Nothing']
  for (const b of brands) {
    if (t.toLowerCase().includes(b.toLowerCase())) { decisions.brand_preference = b; break }
  }

  return Object.keys(decisions).length > 0 ? decisions : null
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [llmMode, setLlmMode] = useState('ollama')
  const [loading, setLoading] = useState(false)
  const [decisionData, setDecisionData] = useState(null)
  const [stage, setStage] = useState('等待输入')
  const [orderPlaced, setOrderPlaced] = useState(false)
  const [lastThinkingSteps, setLastThinkingSteps] = useState([])
  const [sidebarWidth, setSidebarWidth] = useState(400)
  const [userDecisions, setUserDecisions] = useState({})

  // Keep a ref to current messages for use inside streaming callbacks
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  // AbortController for cancelling in-flight streams
  const abortRef = useRef(null)
  // Use ref for userDecisions to avoid recreating handleSend on every decision change
  const userDecisionsRef = useRef(userDecisions)
  userDecisionsRef.current = userDecisions

  const handleSend = useCallback(async (text) => {
    // Cancel any prior in-flight stream
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    const history = messagesRef.current.map((m) => ({ role: m.role, content: m.text }))
    const userMsg = { id: crypto.randomUUID(), role: 'user', text, structuredData: null, taskPlan: null, thinkingSteps: [], quickReplies: null }
    // Seed the assistant message as empty — we'll stream into it
    const assistantSeed = { id: crypto.randomUUID(), role: 'assistant', text: '', structuredData: null, taskPlan: null, thinkingSteps: [], streaming: true, quickReplies: null }

    setMessages((prev) => [...prev, userMsg, assistantSeed])
    setLoading(true)

    // Immediately extract decisions from user's message
    const extracted = parseUserDecisions(text)
    if (extracted) {
      setUserDecisions((prev) => ({ ...prev, ...extracted }))
    }

    // Merge current + extracted decisions for this request (state update is async)
    const mergedDecisions = { ...userDecisionsRef.current, ...extracted }

    try {
      await streamMessage(text, history, llmMode, (event) => {
        // Ignore events if this stream was aborted
        if (controller.signal.aborted) return

        switch (event.type) {
          case 'token':
            setMessages((prev) => {
              const msgs = [...prev]
              const last = msgs[msgs.length - 1]
              msgs[msgs.length - 1] = { ...last, text: last.text + event.content }
              return msgs
            })
            // Advance stage to at least 意图澄清 once LLM starts responding
            setStage((prev) => prev === '等待输入' ? '意图澄清' : prev)
            break

          case 'tool_start':
            setMessages((prev) => {
              const msgs = [...prev]
              const last = msgs[msgs.length - 1]
              const step = { tool: event.tool, icon: event.icon, label: event.label, input: event.input }
              msgs[msgs.length - 1] = { ...last, thinkingSteps: [...(last.thinkingSteps || []), step] }
              return msgs
            })
            // Advance stage based on tool usage
            if (event.tool === 'product_search') {
              setStage((prev) => {
                return STAGE_ORDER.indexOf(prev) < STAGE_ORDER.indexOf('搜索中') ? '搜索中' : prev
              })
            }
            break

          case 'tool_end':
            setMessages((prev) => {
              const msgs = [...prev]
              const last = msgs[msgs.length - 1]
              const steps = [...(last.thinkingSteps || [])]
              // Attach result to the last step for this tool that has no result yet
              const idx = steps.findLastIndex(s => s.tool === event.tool && !s.result)
              if (idx >= 0) steps[idx] = { ...steps[idx], result: event.result }
              msgs[msgs.length - 1] = { ...last, thinkingSteps: steps }
              return msgs
            })
            break

          case 'task_plan':
            setMessages((prev) => {
              const msgs = [...prev]
              msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], taskPlan: event.data }
              return msgs
            })
            break

          case 'structured_data':
            setMessages((prev) => {
              const msgs = [...prev]
              msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], structuredData: event.data }
              return msgs
            })
            if (event.data?.type === 'recommendation') {
              setDecisionData(event.data)
              // Advance stage to at least 推荐方案
              setStage((prev) => {
                return STAGE_ORDER.indexOf(prev) < STAGE_ORDER.indexOf('推荐方案') ? '推荐方案' : prev
              })
            }
            if (event.data?.type === 'order_confirm') {
              setStage((prev) => {
                return STAGE_ORDER.indexOf(prev) < STAGE_ORDER.indexOf('订单确认') ? '订单确认' : prev
              })
            }
            break

          case 'stage': {
            if (event.stage && event.stage !== '未知') {
              setStage((prev) => {
                const prevIdx = STAGE_ORDER.indexOf(prev)
                const newIdx = STAGE_ORDER.indexOf(event.stage)
                // Only advance, never regress
                return newIdx > prevIdx ? event.stage : prev
              })
            }
            break
          }

          case 'thinking_steps':
            if (event.steps?.length > 0) setLastThinkingSteps(event.steps)
            break

          case 'decision_update':
            if (event.decisions) {
              setUserDecisions((prev) => ({ ...prev, ...event.decisions }))
            }
            break

          case 'quick_replies':
            setMessages((prev) => {
              const msgs = [...prev]
              msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], quickReplies: event.options }
              return msgs
            })
            break

          case 'done':
            setMessages((prev) => {
              const msgs = [...prev]
              const last = msgs[msgs.length - 1]
              // Replace raw accumulated text with backend-cleaned text (strips JSON blocks)
              const cleanText = event.clean_text ?? last.text
              msgs[msgs.length - 1] = { ...last, text: cleanText, streaming: false }
              return msgs
            })
            setLoading(false)
            break

          case 'error':
            setMessages((prev) => {
              const msgs = [...prev]
              msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], text: `错误: ${event.message}`, streaming: false }
              return msgs
            })
            setLoading(false)
            break
        }
      }, controller.signal, mergedDecisions)
    } catch (err) {
      // Silently ignore abort errors
      if (err.name === 'AbortError') return
      setMessages((prev) => {
        const msgs = [...prev]
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], text: `错误: ${err.message}`, streaming: false }
        return msgs
      })
      setLoading(false)
    }
  }, [llmMode])

  const handleSelectProduct = useCallback((product) => {
    handleSend(`我选择 ${product.name}，帮我下单${product.platform}的`)
  }, [handleSend])

  const handleConfirmOrder = useCallback(() => {
    setOrderPlaced(true)
    handleSend('确认下单')
  }, [handleSend])

  const handleCancelOrder = useCallback(() => {
    handleSend('取消，我再看看')
  }, [handleSend])

  const handleClear = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setDecisionData(null)
    setStage('等待输入')
    setOrderPlaced(false)
    setLastThinkingSteps([])
    setUserDecisions({})
    setLoading(false)
  }, [])

  // Resizable sidebar drag handler
  const handleDragStart = useCallback((e) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = sidebarWidth

    const onMove = (e) => {
      const delta = startX - e.clientX
      setSidebarWidth(Math.max(300, Math.min(600, startWidth + delta)))
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [sidebarWidth])

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Header llmMode={llmMode} onLlmChange={setLlmMode} onClear={handleClear} />
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Chat */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatPanel
            messages={messages}
            loading={loading}
            onSend={handleSend}
            onSelectProduct={handleSelectProduct}
            onConfirmOrder={handleConfirmOrder}
            onCancelOrder={handleCancelOrder}
            orderPlaced={orderPlaced}
          />
        </div>

        {/* Drag handle */}
        <div
          onMouseDown={handleDragStart}
          className="w-1.5 flex-shrink-0 bg-slate-200 hover:bg-sky-400 active:bg-sky-500 cursor-col-resize transition-colors"
          title="拖拽调整宽度"
        />

        {/* Right: Decision panel */}
        <div style={{ width: sidebarWidth }} className="flex-shrink-0 bg-white overflow-y-auto border-l border-slate-100">
          <DecisionPanel data={decisionData} stage={stage} thinkingSteps={lastThinkingSteps} userDecisions={userDecisions} onSend={handleSend} />
        </div>
      </div>
    </div>
  )
}
