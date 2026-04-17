import { useRef, useEffect } from 'react'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'

export default function ChatPanel({ messages, loading, onSend, onSelectProduct, onConfirmOrder, onCancelOrder }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <span className="text-5xl mb-4">🛒</span>
            <p className="text-lg font-medium">RAG 智能购物助手</p>
            <p className="text-sm mt-1">告诉我你想买什么，我来帮你做决策</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage
            key={i}
            role={msg.role}
            text={msg.text}
            structuredData={msg.structuredData}
            onSelectProduct={onSelectProduct}
            onConfirmOrder={onConfirmOrder}
            onCancelOrder={onCancelOrder}
          />
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-gray-400 mb-4">
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-sm">🤖</div>
            <div className="bg-gray-100 rounded-2xl px-4 py-3 text-sm">
              <span className="animate-pulse">思考中...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={loading} />
    </div>
  )
}
