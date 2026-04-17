const STAGES = ['意图澄清', '搜索中', '推荐方案', '订单确认', '下单完成']

export default function StageProgress({ currentStage }) {
  const currentIdx = STAGES.indexOf(currentStage)

  return (
    <div className="space-y-2">
      {STAGES.map((stage, i) => {
        let icon = '⬜'
        let style = 'text-gray-400'
        if (i < currentIdx) { icon = '✅'; style = 'text-green-600' }
        else if (i === currentIdx) { icon = '🔄'; style = 'text-blue-600 font-medium' }

        return (
          <div key={stage} className={`flex items-center gap-2 text-sm ${style}`}>
            <span>{icon}</span>
            <span>{stage}</span>
            {i === currentIdx && <span className="text-xs">← 当前</span>}
          </div>
        )
      })}
    </div>
  )
}
