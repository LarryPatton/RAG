import { Check, AlertTriangle, User } from 'lucide-react'
import { getBrandStyle } from '../constants/brands'

export default function ProductCard({ product, onSelect }) {
  const brandStyle = getBrandStyle(product.brand)
  const stars = '★'.repeat(Math.floor(product.rating)) + '☆'.repeat(5 - Math.floor(product.rating))

  return (
    <div className="w-72 flex-shrink-0 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition overflow-hidden">
      {/* Rank badge */}
      <div className="flex items-center gap-2 px-4 pt-3">
        <span className={`text-xs font-bold px-2 py-0.5 rounded ${
          product.rank === 1 ? 'bg-yellow-100 text-yellow-700' :
          product.rank === 2 ? 'bg-slate-100 text-slate-600' :
          'bg-orange-50 text-orange-600'
        }`}>
          #{product.rank}
        </span>
      </div>

      {/* Brand block + name + price */}
      <div className="flex items-center gap-3 px-4 py-3">
        <div
          className="w-14 h-14 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
          style={{ backgroundColor: brandStyle.bg, color: brandStyle.text }}
        >
          {product.brand}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-800 truncate">{product.name}</p>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-lg font-bold font-mono text-red-600">¥{product.price}</span>
            <span className="text-xs text-amber-500">{stars} {product.rating}</span>
          </div>
        </div>
      </div>

      {/* Pros & Cons */}
      <div className="px-4 pb-2 space-y-1">
        {product.pros?.map((pro, i) => (
          <div key={i} className="flex items-center gap-1.5 text-xs text-emerald-700">
            <Check size={12} className="flex-shrink-0" />
            <span>{pro}</span>
          </div>
        ))}
        {product.cons?.map((con, i) => (
          <div key={i} className="flex items-center gap-1.5 text-xs text-amber-600">
            <AlertTriangle size={12} className="flex-shrink-0" />
            <span>{con}</span>
          </div>
        ))}
      </div>

      {/* Best for */}
      {product.best_for && (
        <div className="mx-4 mb-2 text-xs text-slate-500 bg-slate-50 rounded px-2 py-1 flex items-center gap-1.5">
          <User size={12} className="flex-shrink-0" />
          适合：{product.best_for}
        </div>
      )}

      {/* Select button */}
      <div className="px-4 pb-4">
        <button
          onClick={onSelect}
          className="w-full py-2 bg-sky-500 text-white text-sm font-medium rounded-md hover:bg-sky-600 transition"
        >
          选择这款
        </button>
      </div>
    </div>
  )
}
