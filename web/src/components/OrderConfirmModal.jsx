export default function OrderConfirmModal({ data, onConfirm, onCancel }) {
  const priceComp = data.price_comparison || {}
  const minPlatform = Object.entries(priceComp).sort((a, b) => a[1] - b[1])[0]

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-lg p-5 max-w-sm">
      <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
        📦 订单确认
      </h3>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">商品</span>
          <span className="font-medium">{data.product}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">金额</span>
          <span className="text-lg font-bold text-red-500">¥{data.price}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">平台</span>
          <span>{data.platform}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">送达</span>
          <span>{data.delivery}</span>
        </div>
      </div>

      {/* Price comparison */}
      {Object.keys(priceComp).length > 0 && (
        <div className="mt-3 p-2 bg-blue-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-1">💰 比价</p>
          <div className="flex gap-3 text-xs">
            {Object.entries(priceComp).map(([platform, price]) => (
              <span key={platform} className={`${
                minPlatform && platform === minPlatform[0] ? 'font-bold text-green-600' : 'text-gray-500'
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
            <p key={i} className="text-xs text-amber-700">⚠️ {note}</p>
          ))}
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-3 mt-4">
        <button
          onClick={onCancel}
          className="flex-1 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50 transition"
        >
          取消
        </button>
        <button
          onClick={onConfirm}
          className="flex-1 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition"
        >
          确认下单
        </button>
      </div>
    </div>
  )
}
