import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { User, Bot, ChevronDown, ChevronRight } from 'lucide-react'
import ProductCard from './ProductCard'
import OrderConfirmModal from './OrderConfirmModal'
import ThinkingSteps from './ThinkingSteps'
import QuickReplies from './QuickReplies'
import { STAGE_LABELS, STAGE_COLORS } from '../constants/stages'

const STAGE_REGEX = new RegExp(`^\\[(${STAGE_LABELS.join('|')})\\]\\s*`)
// Also match inline stage tags like [搜索中] that appear mid-text
const INLINE_STAGE_REGEX = new RegExp(`\\[(${STAGE_LABELS.join('|')})\\]\\s*`, 'g')

// Intermediate stages = AI thinking, not user-facing answers
const THINKING_STAGES = new Set(['分析中', '搜索中'])

function parseStageTag(text) {
  if (!text) return { stage: null, cleanText: text }
  const match = text.match(STAGE_REGEX)
  if (match) {
    return { stage: match[1], cleanText: text.slice(match[0].length) }
  }
  return { stage: null, cleanText: text }
}

function cleanAssistantText(text) {
  if (!text) return text
  let cleaned = text
  // Strip ```json ... ``` blocks
  cleaned = cleaned.replace(/```json\s*\n[\s\S]*?\n```/g, '')
  // Strip bare json blocks without backticks (LLM sometimes outputs raw JSON)
  cleaned = cleaned.replace(/```\s*\n[\s\S]*?\n```/g, '')
  // Strip inline tool call JSON like: json { "name": "compare_prices", "arguments": ... }
  cleaned = cleaned.replace(/\bjson\s*\{[^}]*"name"\s*:\s*"[^"]*"[^}]*"arguments"\s*:\s*\{[^}]*\}\s*\}/g, '')
  // Strip inline [阶段] tags
  cleaned = cleaned.replace(INLINE_STAGE_REGEX, '')
  // Collapse multiple blank lines
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n')
  return cleaned.trim()
}

export default function ChatMessage({ role, text, structuredData, taskPlan, thinkingSteps, streaming, quickReplies, onSend, onSelectProduct, onConfirmOrder, onCancelOrder, orderPlaced, loading }) {
  const isUser = role === 'user'
  const [thinkingExpanded, setThinkingExpanded] = useState(false)

  // For assistant messages: extract stage tag and clean text
  let stageTag = null
  let displayText = text
  if (!isUser && text) {
    const parsed = parseStageTag(text)
    stageTag = parsed.stage
    displayText = cleanAssistantText(parsed.cleanText)
  }

  // Determine if this is a "thinking" message (intermediate stage with no structured output)
  const isThinkingMessage = !isUser && !streaming && THINKING_STAGES.has(stageTag) && !structuredData

  // If this is a thinking-only message, collapse it after streaming ends
  if (isThinkingMessage && displayText) {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[640px]">
          {/* Thinking steps */}
          <ThinkingSteps steps={thinkingSteps} streaming={streaming} />

          {/* Collapsed thinking message */}
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-slate-100 text-slate-500">
              <Bot size={16} />
            </div>
            <div>
              <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full mb-1.5 ${STAGE_COLORS[stageTag] || 'bg-slate-100 text-slate-600'}`}>
                {stageTag}
              </span>
              <div className="rounded-xl px-4 py-2.5 bg-slate-50 border border-slate-200 text-slate-500">
                <button
                  onClick={() => setThinkingExpanded(!thinkingExpanded)}
                  className="flex items-center gap-1.5 text-xs hover:text-slate-700 transition-colors w-full"
                >
                  {thinkingExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  <span>AI 正在分析和收集数据...</span>
                </button>
                {thinkingExpanded && (
                  <div className="mt-2 text-xs text-slate-400 prose prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                    <ReactMarkdown>{displayText}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[640px] ${isUser ? 'order-2' : ''}`}>
        {/* Thinking steps (above bubble, assistant only) */}
        {!isUser && <ThinkingSteps steps={thinkingSteps} streaming={streaming} />}

        {/* Avatar + bubble */}
        <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? 'bg-sky-100 text-sky-600' : 'bg-slate-100 text-slate-500'
          }`}>
            {isUser ? <User size={16} /> : <Bot size={16} />}
          </div>
          <div>
            {/* Stage badge */}
            {!isUser && stageTag && (
              <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full mb-1.5 ${STAGE_COLORS[stageTag] || 'bg-slate-100 text-slate-600'}`}>
                {stageTag}
              </span>
            )}
            {/* Text bubble */}
            {displayText && (
              <div className={`rounded-xl px-4 py-2.5 ${
                isUser ? 'bg-sky-500 text-white' : 'bg-slate-100 text-slate-800'
              }`}>
                {isUser
                  ? <div className="text-sm whitespace-pre-wrap leading-relaxed">{displayText}</div>
                  : <div className={`text-sm prose prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 ${streaming ? 'streaming-cursor' : ''}`}>
                      <ReactMarkdown>{displayText}</ReactMarkdown>
                    </div>
                }
              </div>
            )}
          </div>
        </div>

        {/* Product cards — this is the real user-facing output */}
        {structuredData?.type === 'recommendation' && (
          <div className="mt-3 ml-11">
            <div className="flex gap-3 overflow-x-auto pb-2">
              {structuredData.products.map((product) => (
                <ProductCard
                  key={product.rank}
                  product={product}
                  onSelect={() => onSelectProduct(product)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Order confirmation */}
        {structuredData?.type === 'order_confirm' && (
          <div className="mt-3 ml-11">
            <OrderConfirmModal
              data={structuredData}
              onConfirm={onConfirmOrder}
              onCancel={onCancelOrder}
              disabled={orderPlaced}
            />
          </div>
        )}

        {/* Quick reply buttons */}
        {!isUser && !streaming && quickReplies && (
          <QuickReplies options={quickReplies} onSelect={onSend} disabled={loading} />
        )}
      </div>
    </div>
  )
}
