import { useState } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 p-4 border-t border-slate-200 bg-white">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="帮你找什么？比如：帮我找一款500以内的降噪耳机"
        disabled={disabled}
        className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="px-6 py-2.5 bg-sky-500 text-white rounded-md hover:bg-sky-600 disabled:bg-slate-300 disabled:cursor-not-allowed transition text-sm font-medium"
      >
        发送
      </button>
    </form>
  )
}
