export default function ComparisonBar({ comparisons }) {
  if (!comparisons) return null

  return (
    <div className="space-y-3">
      {Object.entries(comparisons).map(([dimension, values]) => (
        <div key={dimension}>
          <p className="text-xs font-medium text-gray-700 mb-1">{dimension}</p>
          <div className="space-y-1">
            {values.map((val, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className={`h-3 rounded-full ${
                  i === 0 ? 'bg-blue-500' : i === 1 ? 'bg-blue-300' : 'bg-blue-200'
                }`} style={{ width: `${100 - i * 20}%` }} />
                <span className="text-xs text-gray-600 whitespace-nowrap">{val}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
