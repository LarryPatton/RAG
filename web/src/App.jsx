import { useState, useCallback } from 'react'
import Header from './components/Header'
import ChatPanel from './components/ChatPanel'
import DecisionPanel from './components/DecisionPanel'
import { sendMessage } from './api/client'

export default function App() {
  const [messages, setMessages] = useState([])
  const [llmMode, setLlmMode] = useState('ollama')
  const [loading, setLoading] = useState(false)
  const [decisionData, setDecisionData] = useState(null)
  const [stage, setStage] = useState('等待输入')

  const handleSend = useCallback(async (text) => {
    const userMsg = { role: 'user', text, structuredData: null }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.text }))
      const res = await sendMessage(text, history, llmMode)

      const assistantMsg = {
        role: 'assistant',
        text: res.text,
        structuredData: res.structured_data,
      }
      setMessages((prev) => [...prev, assistantMsg])
      if (res.stage && res.stage !== '未知') {
        setStage(res.stage)
      }

      if (res.structured_data) {
        setDecisionData(res.structured_data)
      }
    } catch (err) {
      const errorMsg = { role: 'assistant', text: `错误: ${err.message}`, structuredData: null }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }, [messages, llmMode])

  const handleSelectProduct = useCallback((product) => {
    handleSend(`我选择 ${product.name}，帮我下单${product.platform}的`)
  }, [handleSend])

  const handleConfirmOrder = useCallback(() => {
    handleSend('确认下单')
  }, [handleSend])

  const handleCancelOrder = useCallback(() => {
    handleSend('取消，我再看看')
  }, [handleSend])

  const handleClear = useCallback(() => {
    setMessages([])
    setDecisionData(null)
    setStage('等待输入')
  }, [])

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header llmMode={llmMode} onLlmChange={setLlmMode} onClear={handleClear} />
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Chat */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-gray-200">
          <ChatPanel
            messages={messages}
            loading={loading}
            onSend={handleSend}
            onSelectProduct={handleSelectProduct}
            onConfirmOrder={handleConfirmOrder}
            onCancelOrder={handleCancelOrder}
          />
        </div>
        {/* Right: Decision panel */}
        <div className="w-80 flex-shrink-0 bg-white overflow-y-auto">
          <DecisionPanel data={decisionData} stage={stage} />
        </div>
      </div>
    </div>
  )
}
