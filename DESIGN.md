# Design System — RAG 智能购物助手

## Product Context
- **What this is:** AI 购物助手 Demo，展示 RAG + Agent + Tools 的协作原理
- **Who it's for:** 老师/同学，技术背景的受众，用于学术/课堂演示
- **Space/industry:** AI Agent 教育演示，对标 ChatGPT/Perplexity 类对话界面 + 决策可视化 Dashboard
- **Project type:** 工具型 Web App — 左聊天 + 右决策面板（桌面端专用）

## Aesthetic Direction
- **Direction:** Industrial/Utilitarian — 功能优先的技术感
- **Decoration level:** Minimal — 排版和层级做所有工作，不依赖装饰性元素
- **Mood:** 严肃但不冷漠。技术内容是主角，界面为内容服务。用户感觉到"这是一个认真的技术工具"
- **Icon strategy:** 用 Lucide 图标库替代 emoji，统一图标语言

## Typography
- **Display/Hero:** DM Sans 700 — 几何感强、现代、可读性好，配合技术产品调性
- **Body/UI:** DM Sans 400/500 — 与标题同族，视觉统一。中文回落 system-ui
- **Data/Tables:** JetBrains Mono 400 (tabular-nums) — 用于工具调用日志、价格数字、节点标签
- **Code:** JetBrains Mono 400
- **Loading:** Google Fonts CDN
  ```html
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  ```
- **CSS variables:**
  ```css
  --font-sans: 'DM Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  ```
- **Scale:** 11px (caption) / 12px (label/tag) / 13px (small body) / 14px (body) / 16px (subtitle) / 20px (title) / 28px (hero)

## Color
- **Approach:** Restrained — 1 强调色 + 中性色体系，色彩使用克制但有意义

### Primary
| Token | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| `--primary` | `#0EA5E9` | sky-500 | 主按钮、用户气泡、活跃状态、链接 |
| `--primary-hover` | `#0284C7` | sky-600 | hover 状态 |
| `--primary-light` | `#E0F2FE` | sky-100 | 浅色背景、助手头像底色 |
| `--primary-muted` | `#BAE6FD` | sky-200 | 边框高亮 |

### Neutrals (Slate, 偶暖灰)
| Token | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| `--text-primary` | `#1E293B` | slate-800 | 标题、正文、正式回复文字 |
| `--text-secondary` | `#475569` | slate-600 | 次要文字 |
| `--text-muted` | `#94A3B8` | slate-400 | 推理过程文字、占位符 |
| `--text-faint` | `#CBD5E1` | slate-300 | 未激活状态 |
| `--surface` | `#FFFFFF` | white | 卡片、面板背景 |
| `--surface-raised` | `#F1F5F9` | slate-100 | 折叠推理摘要背景、输入区背景 |
| `--bg` | `#F8FAFC` | slate-50 | 页面背景 |
| `--border` | `#E2E8F0` | slate-200 | 主边框 |
| `--border-light` | `#F1F5F9` | slate-100 | 轻量分隔线 |

### Semantic
| Token | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| `--success` | `#10B981` | emerald-500 | 确认下单、已完成阶段、工具调用成功 |
| `--success-light` | `#D1FAE5` | emerald-100 | 成功提示背景 |
| `--warning` | `#F59E0B` | amber-500 | 风险提示、价格波动 |
| `--warning-light` | `#FEF3C7` | amber-100 | 警告提示背景 |
| `--error` | `#EF4444` | red-500 | 错误状态 |
| `--error-light` | `#FEE2E2` | red-100 | 错误提示背景 |
| `--info` | `#6366F1` | indigo-500 | 信息提示、场景标签 |
| `--info-light` | `#E0E7FF` | indigo-100 | 信息提示背景 |
| `--price-red` | `#DC2626` | red-600 | 价格显示（中文电商强语义色） |

### Dark mode strategy
- 反转中性色：slate-50 ↔ slate-900, white ↔ slate-800
- 主色保持不变，语义色降低饱和度 10-20%
- 通过 CSS custom properties 切换，一个 `.dark` class 控制全局

## Spacing
- **Base unit:** 4px
- **Density:** Comfortable (聊天区) / Compact (决策面板)
- **Scale:** 2xs(2px) xs(4px) sm(8px) md(16px) lg(24px) xl(32px) 2xl(48px) 3xl(64px)
- **Chat bubble padding:** 10px 16px
- **Card padding:** 14px-16px
- **Section gap:** 20px (面板内模块间距)

## Layout
- **Approach:** Hybrid — 聊天区标准布局，决策面板卡片式
- **Structure:** `h-screen flex flex-col` → header + `flex flex-1` (chat | drag-handle | panel)
- **Right panel default width:** 380-400px (比当前 320px 更宽)
- **Right panel min/max:** 300px / 600px
- **Chat bubble max-width:** `max-w-[640px]`（防止宽屏下气泡过宽）
- **Border radius scale:**
  - sm: 4px (小元素、标签)
  - md: 8px (按钮、输入框、卡片内元素)
  - lg: 12px (卡片、面板)
  - xl: 16px (chat bubble、主容器)
  - full: 9999px (头像、标签药丸)

## Motion
- **Approach:** Intentional — 有意义的状态过渡，不做纯装饰动画
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(50-100ms) short(150-250ms) medium(250-400ms) long(400-700ms)
- **Key animations:**
  - Streaming 光标：闪烁的 `▊` 字符，`animate-blink` 0.8s
  - 推理过程折叠/展开：`transition-all duration-200 ease-out`
  - 决策卡片入场：`fade-in + slide-up`，duration 300ms，交错 100ms
  - 阶段指示器进度：当前阶段 dot 有 `box-shadow pulse`

## Chat Area — 推理过程 vs 正式回复

这是产品的核心交互设计，必须严格遵守视觉分层：

### Streaming 阶段（推理进行中）
- 推理过程（工具调用）实时显示为 **灰色小字**：
  - 字体：`font-mono text-xs text-muted`（JetBrains Mono, 12px, slate-400）
  - 背景：`surface-raised`（slate-100）+ 左侧 2px 边框（slate-300）
  - 工具名称用 primary 色高亮，结果用 success 色
- 正式回复文本同时 streaming，用正常样式：
  - 字体：`font-sans text-sm text-primary`（DM Sans, 14px, slate-800）

### Streaming 结束后
- 推理过程 **自动折叠** 为一行摘要：
  - 格式："▶ 调用了 N 个工具 · X.Xs"
  - 样式：`font-mono text-xs text-muted`，可点击展开
- 正式回复保持显示，是用户需要读的核心内容

### 视觉比喻
- 推理过程 = "AI 的自言自语"（轻、灰、monospace、可忽略）
- 正式回复 = "AI 对你说的话"（重、黑、sans-serif、核心）

## Decision Panel — 决策仪表板

右侧面板组织为两个核心模块：

### Module A: 阶段指示器（顶部常驻）
- 精简的购买阶段：了解需求 → 搜索商品 → 比较推荐 → 确认下单
- 横向排列，用 dot + 箭头连接
- 已完成阶段：success 色 dot
- 当前阶段：primary 色 dot + pulse shadow
- 未来阶段：faint 色 dot

### Module B: 决策信息卡片（动态更新）
随对话推进，卡片逐步出现。每张卡片标注来源阶段。

1. **需求摘要** — 用户的预算、类型、场景、品牌偏好（tag 形式）
2. **候选商品** — 检索漏斗：总数 → 语义匹配 → 价格筛选 → 类型过滤 → 最终候选
3. **比价信息** — 各平台价格对比，最低价高亮
4. **推荐理由** — AI 推荐该商品的核心原因（primary-light 背景突出）

### 卡片样式
- 背景 white, 边框 slate-200, 圆角 8px
- Header: 标题（12px semibold）+ 来源阶段标签（mono, 10px, muted bg）
- 推荐理由卡片特殊样式：primary-light 背景 + primary-muted 边框

## Preview
- **Preview file:** `/tmp/design-consultation-preview.html`
- 包含字体对比、配色色板、组件样式、完整界面 mockup
- 支持亮色/暗色模式切换

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-18 | Initial design system created | 基于产品定位（教学演示 AI Agent Demo）和同类产品分析，选择 Industrial/Utilitarian 美学 |
| 2026-04-18 | Sky-500 替代 Blue-600 作为主色 | 更亮、更现代，与"智能"联想更强，避免 Tailwind 默认蓝的同质化 |
| 2026-04-18 | 推理过程/正式回复视觉分层 | 用灰色 mono 小字 vs 黑色 sans 正常字体区分 AI 的"思考"和"回答" |
| 2026-04-18 | 右侧面板从阶段进度升级为决策仪表板 | 卡片式信息组织，展示每个阶段产生的决策依据，而非仅显示阶段状态 |
| 2026-04-18 | 不考虑移动端 | 产品为桌面端课堂演示场景 |
| 2026-04-18 | 右侧面板默认宽度从 320px 提到 380-400px | 给决策卡片和比价信息足够的展示空间 |
