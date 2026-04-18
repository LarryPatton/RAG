import { useState, useRef, useEffect } from 'react'
import { Pencil, Send, Check } from 'lucide-react'

export default function QuickReplies({ options, onSelect, disabled }) {
  const [selected, setSelected] = useState(new Set())
  const [customMode, setCustomMode] = useState(false)
  const [customText, setCustomText] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    if (customMode) inputRef.current?.focus()
  }, [customMode])

  if (!options?.length) return null

  const toggleOption = (option) => {
    if (disabled) return
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(option)) next.delete(option)
      else next.add(option)
      return next
    })
  }

  const submitSelected = () => {
    if (disabled || selected.size === 0) return
    const items = [...selected]
    // Single selection: send directly; multiple: format clearly
    const text = items.length === 1
      ? items[0]
      : items.join(' + ')
    onSelect(text)
    setSelected(new Set())
  }

  const submitCustom = () => {
    if (disabled) return
    const text = customText.trim()
    if (text) { onSelect(text); setCustomText(''); setCustomMode(false) }
  }

  return (
    <div className="flex flex-wrap items-center gap-2 mt-2 ml-11">
      {options.map((option, i) => {
        const isSelected = selected.has(option)
        return (
          <button
            key={i}
            onClick={() => toggleOption(option)}
            disabled={disabled}
            className={`px-4 py-2 text-sm font-medium rounded-full border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              isSelected
                ? 'bg-sky-500 text-white border-sky-500'
                : 'text-sky-600 bg-white border-sky-200 hover:bg-sky-50 hover:border-sky-300 active:bg-sky-100'
            }`}
          >
            {isSelected && <Check size={12} className="inline mr-1 -mt-0.5" />}
            {option}
          </button>
        )
      })}

      {/* Send button — visible when selection exists */}
      {selected.size > 0 && (
        <button
          onClick={submitSelected}
          disabled={disabled}
          className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-white bg-sky-500 rounded-full hover:bg-sky-600 active:bg-sky-700 transition-colors disabled:opacity-50"
        >
          <Send size={13} />
          发送
        </button>
      )}

      {!customMode ? (
        <button
          onClick={() => setCustomMode(true)}
          disabled={disabled}
          className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-400 bg-white border border-slate-200 rounded-full hover:text-slate-600 hover:border-slate-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Pencil size={13} />
          其他
        </button>
      ) : (
        <div className="flex items-center gap-1 bg-white border border-sky-300 rounded-full px-3 py-1 shadow-sm">
          <input
            ref={inputRef}
            value={customText}
            onChange={e => setCustomText(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') submitCustom(); if (e.key === 'Escape') setCustomMode(false) }}
            placeholder="自定义输入..."
            disabled={disabled}
            className="text-sm outline-none w-36 text-slate-700 placeholder:text-slate-300 disabled:opacity-50"
          />
          <button
            onClick={submitCustom}
            disabled={disabled || !customText.trim()}
            className="text-sky-500 hover:text-sky-600 disabled:text-slate-300 transition-colors"
          >
            <Send size={14} />
          </button>
        </div>
      )}
    </div>
  )
}
