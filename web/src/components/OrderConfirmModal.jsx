import { useRef } from 'react'
import { Package, DollarSign, AlertTriangle } from 'lucide-react'

export default function OrderConfirmModal({ data, onConfirm, onCancel, disabled }) {
  const submittedRef = useRef(false)
  const priceComp = data.price_comparison || {}
  const validPriceEntries = Object.entries(priceComp).filter(
    ([, price]) => typeof price === 'number' && !isNaN(price)
  )
  const minPlatform = validPriceEntries.sort((a, b) => a[1] - b[1])[0]

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-lg p-5 max-w-sm">
      <h3 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
        <Package size={18} className="text-sky-500" />
        订单确认
      </h3>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-slate-500">商品</span>
          <span className="font-medium">{data.product}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">金额</span>
          <span className="text-lg font-bold font-mono text-red-600">¥{data.price}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">平台</span>
          <span>{data.platform}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">送达</span>
          <span>{data.delivery}</span>
        </div>
      </div>

      {/* Price comparison */}
      {validPriceEntries.length > 0 && (
        <div className="mt-3 p-2 bg-sky-50 rounded-lg">
          <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
            <DollarSign size={12} />
            比价
          </p>
          <div className="flex gap-3 text-xs">
            {validPriceEntries.map(([platform, price]) => (
              <span key={platform} className={`font-mono ${
                minPlatform && platform === minPlatform[0] ? 'font-bold text-emerald-600' : 'text-slate-500'
              }`}>
                {platform} ¥{price}
                {minPlatform && platform === minPlatform[0] && ' ← 最低'}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Risk notes */}
      {data.risk_notes?.length > 0 && (
        <div className="mt-3 p-2 bg-amber-50 rounded-lg">
          {data.risk_notes.map((note, i) => (
            <p key={i} className="text-xs text-amber-700 flex items-center gap-1">
              <AlertTriangle size={12} className="flex-shrink-0" />
              {note}
            </p>
          ))}
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-3 mt-4">
        {disabled ? (
          <div className="w-full py-2 text-center text-sm text-slate-400 bg-slate-100 rounded-md border border-slate-200">
            已下单 ✓
          </div>
        ) : (
          <>
            <button
              onClick={onCancel}
              className="flex-1 py-2 border border-slate-300 text-slate-600 text-sm rounded-md hover:bg-slate-50 transition"
            >
              取消
            </button>
            <button
              onClick={() => {
                if (submittedRef.current) return
                submittedRef.current = true
                onConfirm()
              }}
              className="flex-1 py-2 bg-emerald-500 text-white text-sm font-medium rounded-md hover:bg-emerald-600 transition"
            >
              确认下单
            </button>
          </>
        )}
      </div>
    </div>
  )
}
