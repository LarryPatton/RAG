import { BookOpen, UserCheck, Search, BarChart2, Lightbulb, MessageSquare, Compass } from 'lucide-react'
import StageProgress from './StageProgress'
import UserProfile from './UserProfile'
import SearchFunnel from './SearchFunnel'
import ComparisonBar from './ComparisonBar'

const DECISION_DIMENSIONS = [
  { key: 'type', label: '耳机类型', color: 'bg-sky-100 text-sky-700 border-sky-200' },
  { key: 'budget', label: '预算', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  { key: 'scenario', label: '使用场景', color: 'bg-indigo-100 text-indigo-700 border-indigo-200' },
  { key: 'brand_preference', label: '品牌偏好', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  { key: 'noise_cancellation', label: '降噪需求', color: 'bg-red-100 text-red-700 border-red-200' },
]

function DecisionCard({ title, icon, children, delay = 0, highlight = false }) {
  return (
    <div
      className={`rounded-lg p-4 animate-fade-slide-up ${
        highlight
          ? 'bg-sky-50 border border-sky-200'
          : 'bg-white border border-slate-200 shadow-sm'
      }`}
      style={{ animationDelay: `${delay * 100}ms` }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sky-500">{icon}</span>
          <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{title}</h3>
        </div>
      </div>
      {children}
    </div>
  )
}

function DecisionDirection({ decisions, onSend }) {
  const hasAny = DECISION_DIMENSIONS.some(d => decisions[d.key])
  if (!hasAny) return null

  return (
    <DecisionCard title="决策方向" icon={<Compass size={14} />} delay={0}>
      <div className="flex flex-wrap gap-2">
        {DECISION_DIMENSIONS.map(({ key, label, color }) => {
          const value = decisions[key]
          if (value) {
            return (
              <button
                key={key}
                onClick={() => onSend(`我想修改${label}，不再是${value}`)}
                className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full border transition-colors hover:opacity-80 ${color}`}
                title={`点击修改${label}`}
              >
                {label}: {value}
              </button>
            )
          }
          return (
            <span
              key={key}
              className="inline-flex items-center px-2.5 py-1 text-xs text-slate-400 rounded-full border border-dashed border-slate-300"
            >
              {label}: 待确认
            </span>
          )
        })}
      </div>
    </DecisionCard>
  )
}

export default function DecisionPanel({ data, stage, thinkingSteps, userDecisions = {}, onSend }) {
  const hasRecommendation = data?.type === 'recommendation'
  const process = data?.decision_process ?? null
  const profile = data?.user_profile ?? null
  const comparisons = data?.comparisons ?? null

  return (
    <div className="flex flex-col h-full">
      {/* Module A: Stage indicator — always visible */}
      <div className="px-4 pt-4 pb-3 border-b border-slate-100 sticky top-0 bg-white z-10">
        <div className="flex items-center gap-2 mb-3">
          <BookOpen size={16} className="text-sky-500" />
          <h2 className="text-sm font-bold text-slate-800">决策面板</h2>
        </div>
        <StageProgress currentStage={stage} />
      </div>

      {/* Module B: Decision cards */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* Card 0: 决策方向 — shows confirmed user decisions */}
        <DecisionDirection decisions={userDecisions} onSend={onSend} />

        {/* Card 1: 需求摘要 */}
        {profile && (
          <DecisionCard title="需求摘要" icon={<UserCheck size={14} />} delay={1}>
            <UserProfile profile={profile} />
          </DecisionCard>
        )}

        {/* Card 2: 候选商品 */}
        {process && (
          <DecisionCard title="候选商品" icon={<Search size={14} />} delay={2}>
            <SearchFunnel process={process} />
          </DecisionCard>
        )}

        {/* Card 3: 比价信息 */}
        {comparisons && (
          <DecisionCard title="比价信息" icon={<BarChart2 size={14} />} delay={3}>
            <ComparisonBar comparisons={comparisons} />
          </DecisionCard>
        )}

        {/* Card 4: 推荐理由 */}
        {hasRecommendation && data.verdict && (
          <DecisionCard title="推荐理由" icon={<Lightbulb size={14} />} delay={4} highlight>
            <p className="text-sm text-slate-700 leading-relaxed">{data.verdict}</p>
          </DecisionCard>
        )}

        {/* Empty state */}
        {!hasRecommendation && stage === '等待输入' && Object.keys(userDecisions).length === 0 && (
          <div className="text-center text-slate-400 py-12">
            <MessageSquare size={32} className="mx-auto mb-3" strokeWidth={1.5} />
            <p className="text-sm">开始对话后</p>
            <p className="text-sm">这里会展示 AI 的决策过程</p>
          </div>
        )}
      </div>
    </div>
  )
}
