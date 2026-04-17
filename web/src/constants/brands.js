const BRAND_COLORS = {
  "Sony":      { bg: "#1a1a2e", text: "#ffffff" },
  "Bose":      { bg: "#1c1c1c", text: "#ffffff" },
  "华为":      { bg: "#cf0a2c", text: "#ffffff" },
  "小米":      { bg: "#ff6900", text: "#ffffff" },
  "JBL":       { bg: "#ff3c00", text: "#ffffff" },
  "漫步者":    { bg: "#003366", text: "#ffffff" },
  "三星":      { bg: "#1428a0", text: "#ffffff" },
  "铁三角":    { bg: "#231f20", text: "#ffffff" },
  "1MORE":     { bg: "#e60012", text: "#ffffff" },
  "QCY":       { bg: "#00a0e9", text: "#ffffff" },
  "雷蛇":      { bg: "#44d62c", text: "#000000" },
  "罗技":      { bg: "#00b8fc", text: "#ffffff" },
  "森海塞尔":  { bg: "#0f1923", text: "#ffffff" },
  "B&O":       { bg: "#d4a574", text: "#1a1a1a" },
  "AKG":       { bg: "#c41230", text: "#ffffff" },
  "Beats":     { bg: "#e4002b", text: "#ffffff" },
  "Marshall":  { bg: "#1a1a1a", text: "#ffffff" },
  "韶音":      { bg: "#00c853", text: "#ffffff" },
  "南卡":      { bg: "#ff5722", text: "#ffffff" },
  "倍思":      { bg: "#333333", text: "#ffffff" },
  "联想":      { bg: "#e1002a", text: "#ffffff" },
  "OPPO":      { bg: "#1a6c37", text: "#ffffff" },
  "vivo":      { bg: "#415fff", text: "#ffffff" },
  "魅族":      { bg: "#00a0dc", text: "#ffffff" },
  "realme":    { bg: "#ffc800", text: "#1a1a1a" },
  "飞利浦":    { bg: "#0b5ed7", text: "#ffffff" },
  "松下":      { bg: "#0a2f6e", text: "#ffffff" },
  "HyperX":    { bg: "#e41230", text: "#ffffff" },
  "赛睿":      { bg: "#ff5200", text: "#ffffff" },
  "西伯利亚":  { bg: "#2196f3", text: "#ffffff" },
  "Nothing":   { bg: "#000000", text: "#ffffff" },
  "Jaybird":   { bg: "#76b900", text: "#ffffff" },
}

export function getBrandStyle(brand) {
  const entry = BRAND_COLORS[brand] || { bg: "#6b7280", text: "#ffffff" }
  return entry
}

export default BRAND_COLORS
