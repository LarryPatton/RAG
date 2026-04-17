export default function Header({ llmMode, onLlmChange, onClear }) {
  return (
    <header className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200">
      <div className="flex items-center gap-3">
        <span className="text-2xl">🛒</span>
        <h1 className="text-xl font-bold text-gray-800">RAG 智能购物助手</h1>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">Decision Agent Demo</span>
      </div>
      <div className="flex items-center gap-4">
        <select
          value={llmMode}
          onChange={(e) => onLlmChange(e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-3 py-1.5 bg-white"
        >
          <option value="ollama">Ollama (本地)</option>
          <option value="qwen-api">Qwen API (云端)</option>
        </select>
        <button
          onClick={onClear}
          className="text-sm text-gray-500 hover:text-red-500 px-3 py-1.5 rounded-md hover:bg-red-50 transition"
        >
          🔄 清空对话
        </button>
      </div>
    </header>
  )
}
