export default function ComparisonBar({ comparisons }) {
  if (!comparisons) return null

  return (
    <div className="space-y-3">
      {Object.entries(comparisons).map(([dimension, values]) => {
        // Try to extract numeric values for proportional widths
        const numericValues = values.map(val => {
          if (typeof val === 'number') return val
          const match = String(val).match(/[\d.]+/)
          return match ? parseFloat(match[0]) : null
        })
        const allNumeric = numericValues.every(v => v !== null && !isNaN(v))
        const maxVal = allNumeric ? Math.max(...numericValues) : 0

        return (
          <div key={dimension}>
            <p className="text-xs font-medium text-slate-700 mb-1">{dimension}</p>
            <div className="space-y-1">
              {values.map((val, i) => {
                const width = allNumeric && maxVal > 0
                  ? `${(numericValues[i] / maxVal) * 100}%`
                  : `${100 / values.length}%`

                return (
                  <div key={i} className="flex items-center gap-2">
                    <div className={`h-3 rounded-full ${
                      i === 0 ? 'bg-sky-500' : i === 1 ? 'bg-sky-300' : 'bg-sky-200'
                    }`} style={{ width }} />
                    <span className="text-xs text-slate-600 whitespace-nowrap">{val}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
