/** Canonical stage ordering — single source of truth. */
export const STAGE_ORDER = ['等待输入', '意图澄清', '分析中', '搜索中', '推荐方案', '订单确认', '下单完成']

export const STAGE_LABELS = ['意图澄清', '分析中', '搜索中', '推荐方案', '订单确认', '下单完成']

export const STAGE_COLORS = {
  '意图澄清': 'bg-sky-100 text-sky-700',
  '分析中': 'bg-indigo-100 text-indigo-700',
  '搜索中': 'bg-amber-100 text-amber-700',
  '推荐方案': 'bg-emerald-100 text-emerald-700',
  '订单确认': 'bg-orange-100 text-orange-700',
  '下单完成': 'bg-emerald-100 text-emerald-700',
}
