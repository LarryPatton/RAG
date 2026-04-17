import ProductCard from './ProductCard'
import OrderConfirmModal from './OrderConfirmModal'

export default function ChatMessage({ role, text, structuredData, onSelectProduct, onConfirmOrder, onCancelOrder }) {
  const isUser = role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : ''}`}>
        {/* Avatar */}
        <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
            isUser ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'
          }`}>
            {isUser ? '👤' : '🤖'}
          </div>
          <div className={`rounded-2xl px-4 py-3 ${
            isUser ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'
          }`}>
            {/* Text content */}
            {text && (
              <div className="text-sm whitespace-pre-wrap leading-relaxed">{text}</div>
            )}
          </div>
        </div>

        {/* Product cards (below the message bubble) */}
        {structuredData?.type === 'recommendation' && (
          <div className="mt-3 ml-11">
            <div className="flex gap-3 overflow-x-auto pb-2">
              {structuredData.products.map((product) => (
                <ProductCard
                  key={product.rank}
                  product={product}
                  onSelect={() => onSelectProduct(product)}
                />
              ))}
            </div>
            {structuredData.verdict && (
              <div className="mt-2 text-sm text-gray-600 bg-blue-50 rounded-lg px-4 py-2">
                💡 {structuredData.verdict}
              </div>
            )}
          </div>
        )}

        {/* Order confirmation */}
        {structuredData?.type === 'order_confirm' && (
          <div className="mt-3 ml-11">
            <OrderConfirmModal
              data={structuredData}
              onConfirm={onConfirmOrder}
              onCancel={onCancelOrder}
            />
          </div>
        )}
      </div>
    </div>
  )
}
