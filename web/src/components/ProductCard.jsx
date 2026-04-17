export default function ProductCard({ product, onSelect }) {
  return <div onClick={onSelect}>{product?.name}</div>
}
