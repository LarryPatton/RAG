import StageProgress from './StageProgress'
import UserProfile from './UserProfile'
import SearchFunnel from './SearchFunnel'
import ComparisonBar from './ComparisonBar'

export default function DecisionPanel({ data, stage }) {
  const hasRecommendation = data?.type === 'recommendation'
  const process = hasRecommendation ? data.decision_process : null
  const profile = hasRecommendation ? data.user_profile : null
  const comparisons = hasRecommendation ? data.comparisons : null

  return (
    <div className="p-4 space-y-5">
      <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
        🧠 决策过程
      </h2>

      {/* Stage progress */}
      <div>
        <h3 className="text-xs font-medium text-gray-500 uppercase mb-2">阶段进度</h3>
        <StageProgress currentStage={stage} />
      </div>

      {/* User profile */}
      {profile && (
        <div>
          <h3 className="text-xs font-medium text-gray-500 uppercase mb-2">需求画像</h3>
          <UserProfile profile={profile} />
        </div>
      )}

      {/* Search funnel */}
      {process && (
        <div>
          <h3 className="text-xs font-medium text-gray-500 uppercase mb-2">检索漏斗</h3>
          <SearchFunnel process={process} />
        </div>
      )}

      {/* Comparison */}
      {comparisons && (
        <div>
          <h3 className="text-xs font-medium text-gray-500 uppercase mb-2">多维对比</h3>
          <ComparisonBar comparisons={comparisons} />
        </div>
      )}

      {/* Empty state */}
      {!hasRecommendation && stage === '等待输入' && (
        <div className="text-center text-gray-400 py-8">
          <p className="text-3xl mb-2">🧠</p>
          <p className="text-sm">开始对话后</p>
          <p className="text-sm">这里会展示 AI 的决策过程</p>
        </div>
      )}
    </div>
  )
}
