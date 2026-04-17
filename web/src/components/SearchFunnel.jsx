export default function SearchFunnel({ process }) {
  if (!process) return null

  const steps = [
    { label: '商品总数', value: process.total_products },
    { label: '语义检索', value: process.retrieved },
    { label: '价格过滤', value: process.after_price_filter },
    { label: '类型过滤', value: process.after_type_filter },
    { label: '最终推荐', value: process.final_candidates },
  ].filter(s => s.value != null)

  const max = steps[0]?.value || 1

  return (
    <div className="space-y-1.5">
      {steps.map((step, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-16 text-right flex-shrink-0">{step.label}</span>
          <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500 flex items-center justify-end pr-1"
              style={{ width: `${Math.max((step.value / max) * 100, 8)}%` }}
            >
              <span className="text-[10px] text-white font-medium">{step.value}</span>
            </div>
          </div>
        </div>
      ))}
      {process.primary_criterion && (
        <p className="text-xs text-gray-500 mt-1">
          决策依据：<span className="font-medium text-gray-700">{process.primary_criterion}</span>
        </p>
      )}
    </div>
  )
}
