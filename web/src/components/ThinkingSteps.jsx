import { useState, useEffect } from 'react'
import { ChevronRight, ChevronDown, Wrench } from 'lucide-react'

export default function ThinkingSteps({ steps, streaming }) {
  // Default: expanded while streaming, collapsed when done
  const [manualToggle, setManualToggle] = useState(null)

  // Reset manual toggle when streaming starts (new message)
  useEffect(() => {
    if (streaming) setManualToggle(null)
  }, [streaming])

  if (!steps?.length) return null

  // If user manually toggled, respect that. Otherwise: open while streaming, closed when done.
  const isOpen = manualToggle !== null ? manualToggle : !!streaming

  return (
    <div className="mt-2 ml-11 mb-1">
      <button
        onClick={() => setManualToggle(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors"
      >
        {isOpen
          ? <ChevronDown size={12} />
          : <ChevronRight size={12} />
        }
        <span className="font-mono">调用了 {steps.length} 个工具</span>
      </button>
      {isOpen && (
        <div className="mt-1.5 bg-slate-50 border-l-2 border-slate-300 rounded-r-md pl-3 py-2 space-y-1.5">
          {steps.map((s, i) => (
            <div key={i} className="font-mono text-xs text-slate-400 flex items-start gap-1.5">
              <Wrench size={12} className="flex-shrink-0 mt-0.5 text-slate-300" />
              <div>
                <span className="font-medium text-sky-500">{s.label || s.tool}</span>
                {s.input && (
                  <span className="ml-1 text-slate-400">→ {s.input}</span>
                )}
                {s.result && (
                  <div className="text-emerald-500 truncate max-w-xs">{s.result}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
