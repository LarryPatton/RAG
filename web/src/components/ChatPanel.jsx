import { useRef, useEffect, useCallback } from 'react'
import { ShoppingCart, Bot, Loader2 } from 'lucide-react'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'

export default function ChatPanel({ messages, loading, onSend, onSelectProduct, onConfirmOrder, onCancelOrder, orderPlaced }) {
  const bottomRef = useRef(null)
  const isAtBottom = useRef(true)

  // Track whether user is near the bottom
  useEffect(() => {
    const el = bottomRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => { isAtBottom.current = entry.isIntersecting },
      { threshold: 0.1 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  // Auto-scroll only when user is at bottom
  useEffect(() => {
    if (isAtBottom.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <ShoppingCart size={48} className="mb-4" strokeWidth={1.5} />
            <p className="text-lg font-medium">RAG 智能购物助手</p>
            <p className="text-sm mt-1">告诉我你想买什么，我来帮你做决策</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            role={msg.role}
            text={msg.text}
            structuredData={msg.structuredData}
            taskPlan={msg.taskPlan}
            thinkingSteps={msg.thinkingSteps}
            streaming={msg.streaming}
            quickReplies={msg.quickReplies}
            onSend={onSend}
            onSelectProduct={onSelectProduct}
            onConfirmOrder={onConfirmOrder}
            onCancelOrder={onCancelOrder}
            orderPlaced={orderPlaced}
            loading={loading}
          />
        ))}
        {/* Only show spinner when loading but no streaming message exists yet */}
        {loading && !messages.some(m => m.streaming) && (
          <div className="flex items-center gap-2 text-slate-400 mb-4">
            <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
              <Bot size={16} className="text-slate-500" />
            </div>
            <div className="bg-slate-100 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-sky-500" />
              <span>思考中...</span>
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
