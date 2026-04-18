const STAGES = [
  { label: '了解需求', keys: ['意图澄清', '分析中'] },
  { label: '搜索商品', keys: ['搜索中'] },
  { label: '比较推荐', keys: ['推荐方案'] },
  { label: '确认下单', keys: ['订单确认', '下单完成'] },
]

function mapStageToIndex(stage) {
  for (let i = 0; i < STAGES.length; i++) {
    if (STAGES[i].keys.includes(stage)) return i
  }
  return -1
}

export default function StageProgress({ currentStage }) {
  const currentIdx = mapStageToIndex(currentStage)

  return (
    <div className="flex items-center gap-0">
      {STAGES.map((stage, i) => {
        const isDone = currentIdx >= 0 && i < currentIdx
        const isCurrent = i === currentIdx
        const isPending = currentIdx === -1 || i > currentIdx

        return (
          <div key={stage.label} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center gap-1">
              <div className={`w-3 h-3 rounded-full transition-all duration-300 ${
                isDone ? 'bg-emerald-500' :
                isCurrent ? 'bg-sky-500 shadow-[0_0_0_4px_rgba(14,165,233,0.2)]' :
                'bg-slate-200'
              }`} />
              <span className={`text-[11px] font-medium whitespace-nowrap ${
                isDone ? 'text-emerald-600' :
                isCurrent ? 'text-sky-600' :
                'text-slate-400'
              }`}>
                {stage.label}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <div className={`flex-1 h-px mx-2 -mt-3.5 transition-colors duration-300 ${
                isDone ? 'bg-emerald-300' : 'bg-slate-200'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
