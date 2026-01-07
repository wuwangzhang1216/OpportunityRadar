# OpportunityRadar Demo 录制计划

> 使用网站: https://doxmind.com/

---

## 概述

- **预计时长**: 约15分钟 (包含注册、完整Onboarding 3步流程、所有核心功能展示)
- **目标受众**: 潜在用户、投资人、合作伙伴
- **核心卖点**: AI驱动的机会匹配 + 智能材料生成 + 智能Onboarding + 紧急度管理 + Profile自动填充

## 最新GUI亮点 (2024版)

| 功能 | 描述 | 页面 |
|------|------|------|
| **Profile Completion Card** | 7维度进度追踪 + "Complete Next Step"快速完善按钮 | Dashboard |
| **Today's Focus Card** | AI每日智能推荐，渐变背景卡片 | Dashboard |
| **AI Value Card** | 展示AI为用户创造的价值统计 | Dashboard |
| **Deadline Calendar** | 14天可视化日历，颜色编码紧急度 | Dashboard |
| **防抖搜索** | 300ms防抖 + 搜索图标脉冲动画 | Opportunities |
| **Quick Prep按钮** | 渐变色一键开始准备，自动跳转Generator | Opportunities |
| **Score Tooltip** | 悬停分数显示四维度分解 | Opportunities |
| **Profile Auto-fill** | Generator自动从Profile填充项目信息 | Generator |
| **Result Feedback Modal** | Pipeline标记Won/Lost时收集反馈 | Pipeline |
| **Version History** | Materials支持版本管理和比较 | Materials |

---

## 录制前准备

### 环境检查
- [ ] 后端服务运行正常 (`docker-compose up`)
- [ ] 前端服务运行正常 (`npm run dev`)
- [ ] 数据库中有足够的机会数据（包含不同紧急度的deadline）
- [ ] 清除浏览器缓存，使用无痕模式
- [ ] 重置Tour状态（Settings → Reset All Tours）

### 录制工具
- [ ] 屏幕录制软件 (OBS / Loom / 系统自带)
- [ ] 分辨率设置: 1920x1080
- [ ] 麦克风测试 (如需配音)

---

## Demo 账号信息

### 录制时使用的注册信息

| 字段 | 值 |
|------|-----|
| **Full Name** | `DoxMind Team` |
| **Email** | `demo@doxmind.com` |
| **Password** | `DemoRadar2024!` |

### Onboarding时使用的URL

| 字段 | 值 |
|------|-----|
| **网站URL** | `https://doxmind.com` |

> AI会自动从URL提取以下信息，可在Step 2中确认/编辑

---

## Demo 脚本

### 第一幕：开场与注册 (1分钟)

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 0:00 | `/` | 展示首页 | "欢迎使用OpportunityRadar，一个AI驱动的机会发现平台" | Hero区域动画效果 |
| 0:15 | `/` | 滚动查看功能介绍 | "帮助开发者和创业团队发现最匹配的Hackathon、Grant、Bounty等机会" | 功能卡片hover效果 |
| 0:25 | `/` | 点击"Get Started"按钮 | "让我们注册一个新账号体验完整流程" | 按钮渐变色效果 |
| 0:35 | `/signup` | 填写Full Name | 输入: `DoxMind Team` | 输入框focus ring |
| 0:40 | `/signup` | 填写Email | 输入: `demo@doxmind.com` | - |
| 0:45 | `/signup` | 填写Password和Confirm | 输入密码 | 密码强度指示(如有) |
| 0:55 | `/signup` | 点击"Create account" | "注册成功后，系统会引导我们完成初始设置" | 按钮loading状态 |

> **无需邮箱验证，注册后自动跳转到Onboarding**

---

### 第二幕：Onboarding引导 (2分30秒) ⭐新用户体验

**Onboarding 3步流程**: Enter URL → Confirm Profile → Get Matches

#### Step 1: URL智能提取

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 1:00 | `/onboarding` | 展示Step 1界面 | "系统会引导新用户完成个人资料设置，只需3步" | 进度条显示 1/3 |
| 1:10 | `/onboarding` | 指向进度条 | "第一步：输入你的网站或GitHub地址" | 步骤指示器高亮 |
| 1:20 | `/onboarding` | 输入URL | 输入: `https://doxmind.com` | 输入框自动focus |
| 1:30 | `/onboarding` | 点击Continue | "AI会自动提取项目信息" | 按钮变为loading状态 |
| 1:35 | `/onboarding` | 展示提取动画 | "正在分析网站内容..." | 旋转动画 + 脉冲效果 |

#### Step 2: 确认Profile信息

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 1:50 | `/onboarding` | 展示Step 2界面 | "AI自动识别了项目信息" | 表单预填充数据 |
| 2:00 | `/onboarding` | 指向各字段 | "团队名称、产品描述、技术栈都自动填充了" | 字段有渐入动画 |
| 2:10 | `/onboarding` | 指向Confidence标签 | "绿色表示高置信度，可以点击编辑调整" | 绿色/黄色/红色confidence badge |
| 2:20 | `/onboarding` | **演示编辑Goals** | "可以添加你的目标：funding, prizes等" | 多选按钮选中状态变化 |
| 2:35 | `/onboarding` | 点击Continue | "确认信息后继续" | 表单验证通过 |

#### Step 3: 查看匹配结果

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 2:45 | `/onboarding` | 展示加载动画 | "AI正在为你匹配机会..." | 机器人图标 + 脉冲动画 |
| 2:55 | `/onboarding` | 展示Step 3界面 | "Profile创建成功！" | 成功勾选图标 |
| 3:05 | `/onboarding` | 展示Top 3匹配 | "这是匹配度最高的3个机会" | 卡片渐入动画 |
| 3:15 | `/onboarding` | 指向匹配分数和原因 | "每个机会显示匹配度和匹配原因" | 分数badge颜色(green/blue/yellow) |
| 3:25 | `/onboarding` | 点击"Go to Dashboard" | "进入Dashboard开始探索" | 按钮hover效果 |

---

### 第三幕：Dashboard概览 (2分30秒) ⭐核心功能展示

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 3:30 | `/dashboard` | 展示整体界面 | "这是你的个人仪表板，所有重要信息一目了然" | 页面进入动画(opacity + y偏移)，`motion.div`渐入 |
| 3:35 | `/dashboard` | **指向Header区域** | "Dashboard标题旁边有个问号按钮" | Sparkles图标 + 12x12 rounded-2xl图标容器 |
| 3:40 | `/dashboard` | **点击HelpButton(右上角)** | "点击可以随时重新查看产品导览" | `<HelpButton>` 组件，tooltip显示"Replay tutorial" |
| 3:50 | `/dashboard` | **展示Profile Completion卡片** | "这是Profile完成度追踪卡片" | `<ProfileCompletionCard>` 组件 |
| 3:55 | `/dashboard` | 指向进度条 | "进度条显示你已完成的百分比" | 动画填充效果 |
| 4:00 | `/dashboard` | 指向7个检查项 | "7个维度：Basic Info, Bio, Skills, Interests, Experience, Goals, Availability" | 绿色勾✓表示完成，灰色圆○表示未完成 |
| 4:10 | `/dashboard` | **点击"Complete Next Step"按钮** | "点击可以快速跳转完善下一项" | 按钮链接到 `/profile` |
| 4:20 | `/dashboard` | **展示Today's Focus卡片** | "AI每天为你分析并推荐最重要的事项" | `<TodaysFocusCard>` 渐变背景 |
| 4:30 | `/dashboard` | 指向主推荐内容 | "显示最紧急的deadline或最高优先级事项" | 优先级badge样式 |
| 4:40 | `/dashboard` | **展示4个统计卡片(Stats Grid)** | "这里是关键统计数据" | `data-tour="stats"` 属性 |
| 4:45 | `/dashboard` | 指向Total Matches卡片 | "Total Matches - 为你匹配的机会总数" | primary颜色，Target图标 |
| 4:50 | `/dashboard` | **指向In Pipeline卡片的紧急警告** | "注意红色警告徽章，显示本周到期数量" | `urgency`属性，红色三角图标 + "X due this week" |
| 5:00 | `/dashboard` | 指向Preparing卡片 | "Preparing - 正在准备中的数量" | yellow颜色，Clock图标 |
| 5:05 | `/dashboard` | 指向Won卡片 | "Won - 你的胜利数" | purple颜色，Trophy图标 |
| 5:10 | `/dashboard` | **展示Top Matches卡片** | "这里显示匹配度最高的5个机会" | `data-tour="top-matches"`，Zap图标 |
| 5:15 | `/dashboard` | 指向一个Match条目 | "每个机会显示分数、类型和deadline" | 分数badge颜色(≥80%绿色，≥60%蓝色，≥40%黄色) |
| 5:20 | `/dashboard` | **展示Pipeline Overview卡片** | "Pipeline概览显示各阶段进度" | 5个阶段进度条(Discovered/Preparing/Submitted/Pending/Won) |
| 5:30 | `/dashboard` | **展示Deadline Calendar** | "日历视图显示未来14天的所有deadline" | `<DeadlineCalendar>` 组件，14列布局 |
| 5:35 | `/dashboard` | 指向日历颜色编码 | "红色=紧急(≤3天)，橙色=即将(≤7天)，黄色=注意(≤14天)" | urgency颜色系统 |
| 5:40 | `/dashboard` | 悬停一个日期 | "悬停查看当天的机会详情" | Tooltip显示机会名称和类型 |
| 5:45 | `/dashboard` | **展示Quick Actions卡片** | "快速操作区域" | 3列grid，feature variant卡片 |
| 5:50 | `/dashboard` | 指向3个快速操作 | "Browse Opportunities、Generate Materials、Improve Profile" | 每个有独特颜色和图标 |
| 5:55 | `/dashboard` | **展示AI Value Card** | "AI价值统计卡片显示AI为你创造的价值" | `<AIValueCard>` 组件 |
| 6:00 | `/dashboard` | 点击导航进入Opportunities | "让我们看看所有匹配的机会" | 侧边栏nav item hover效果 |

---

### 第四幕：发现与筛选机会 (3分30秒) ⭐搜索+紧急度+快速操作

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 6:05 | `/opportunities` | 展示机会列表 | "Opportunities页面显示所有为你匹配的机会" | 3列网格布局(lg:grid-cols-3) |
| 6:10 | `/opportunities` | 指向页面标题 | "标题下方显示匹配到的机会数量" | "Showing X opportunities" 文字 |
| 6:15 | `/opportunities` | **展示搜索框** | "可以通过关键词搜索感兴趣的机会" | `<Input>` pl-10 pr-10，Search图标在左侧 |
| 6:25 | `/opportunities` | 输入搜索词"AI" | "比如搜索AI相关的机会" | **输入时搜索图标变为primary色并有`animate-pulse`脉冲动画** |
| 6:30 | `/opportunities` | 等待搜索结果 | "搜索使用300ms防抖技术，输入停止后自动过滤" | `useDebouncedSearch` hook，`isSearching`状态控制动画 |
| 6:35 | `/opportunities` | **点击X清除按钮** | "点击X清除搜索" | 清除按钮在输入框右侧，hover变foreground色 |
| 6:40 | `/opportunities` | **展示状态过滤器** | "可以按状态筛选" | 3个按钮: All Matches / Bookmarked / Dismissed |
| 6:45 | `/opportunities` | 点击Bookmarked | "查看已收藏的机会" | Bookmark图标在按钮内，选中时variant="default" |
| 6:50 | `/opportunities` | 点击All Matches返回 | "返回所有机会" | - |
| 6:55 | `/opportunities` | **展示类型过滤器** | "还可以按类型筛选" | 6个类别: All/Hackathons/Grants/Bounties/Accelerators/Competitions |
| 7:00 | `/opportunities` | 选择Hackathons | "比如只看Hackathon类型的机会" | 按钮选中时variant="secondary" |
| 7:05 | `/opportunities` | **指向机会卡片结构** | "每个卡片显示关键信息" | 卡片结构: 类型badge + 分数 + 标题 + 描述 |
| 7:10 | `/opportunities` | **指向分数badge** | "分数badge可以悬停查看详细分解" | `<ScoreTooltip>` 组件包裹分数 |
| 7:15 | `/opportunities` | 悬停在分数上 | "显示四维度分数和匹配原因" | Tooltip显示score_breakdown和reasons |
| 7:20 | `/opportunities` | **指向Match reasons** | "匹配原因以标签形式显示" | Badge variant="secondary"，最多显示2个+剩余数量 |
| 7:25 | `/opportunities` | **指向Eligibility indicator** | "资格状态用颜色和图标表示" | ✓绿色=eligible，⚠黄色=partial，✗红色=需检查 |
| 7:30 | `/opportunities` | 悬停在卡片上 | "悬停可以看到快速操作按钮" | **右上角3个按钮滑入(opacity transition)** |
| 7:35 | `/opportunities` | **指向3个悬停按钮** | "收藏、忽略、添加到Pipeline" | Bookmark/X/Plus图标，h-8 w-8 |
| 7:40 | `/opportunities` | **点击收藏按钮** | "点击星标收藏感兴趣的机会" | BookmarkCheck替换Bookmark，text-yellow-600 |
| 7:45 | `/opportunities` | 展示Toast提示 | "收藏成功会显示Toast提示" | success toast: "Bookmarked" + "Opportunity saved to your bookmarks" |
| 7:50 | `/opportunities` | **指向Quick Prep按钮** | "Quick Prep一键开始准备" | **渐变背景 `bg-gradient-to-r from-primary to-purple-600`** |
| 7:55 | `/opportunities` | 指向Zap图标 | "闪电图标会有脉冲动画" | `group-hover/btn:animate-pulse` |
| 8:00 | `/opportunities` | 点击Quick Prep | "它会自动添加到Pipeline的preparing阶段" | 按钮显示loading spinner + "Preparing..." |
| 8:05 | - | (跳过跳转，先返回) | "稍后我们会详细演示，先看看机会详情" | 点击浏览器返回或Details按钮 |
| 8:10 | `/opportunities` | **指向卡片底部deadline提示** | "如果deadline紧急，底部会显示提醒" | Clock图标 + "X days left" + urgency颜色 |
| 8:15 | `/opportunities` | 点击Details按钮或卡片 | "点击查看完整详情" | 跳转到 `/opportunities/[id]` |
| 8:20 | `/opportunities/[id]` | 展示详情页顶部 | "详情页显示完整的机会信息" | ArrowLeft返回按钮 + 标题 + host_name |
| 8:30 | 详情页 | **指向顶部操作按钮区域** | "右上角有多个操作按钮" | 5个按钮: Bookmark / Dismiss / Add to Pipeline / Generate Materials / Add to Calendar |
| 8:35 | 详情页 | **展示Calendar下拉菜单** | "点击日历图标可以添加到你的日历" | `showCalendarMenu`状态控制下拉 |
| 8:40 | 详情页 | 指向3个日历选项 | "支持Google Calendar、Outlook和iCal下载" | 每个选项有对应的SVG图标 |
| 8:50 | 详情页 | **重点展示Match Score卡片** | "这是AI的匹配分析核心" | border-2 border-primary/20 + 渐变背景 |
| 8:55 | 详情页 | 指向大分数显示 | "右上角显示总体匹配度" | 3xl字体 + 颜色编码(≥80绿，≥60蓝，≥40黄) |
| 9:00 | 详情页 | **指向四维度分数grid** | "四个维度详细评估" | grid-cols-2 md:grid-cols-4 |
| 9:05 | 详情页 | 解释Relevance | "Relevance - 语义相关性，项目与机会的匹配程度" | semantic_score |
| 9:10 | 详情页 | 解释Eligibility | "Eligibility - 资格审查结果" | rule_score |
| 9:15 | 详情页 | 解释Timeline | "Timeline - 时间表是否匹配" | time_score |
| 9:20 | 详情页 | 解释Team Fit | "Team Fit - 团队规模是否适合" | team_score |
| 9:25 | 详情页 | **展示Eligibility Status** | "资格状态会显示不同图标" | CheckCircle2(绿)/AlertCircle(黄)/XCircle(红) |
| 9:30 | 详情页 | **展示Eligibility Issues(如有)** | "如果有资格问题，会列出具体原因" | ul列表 + XCircle图标(红色) |
| 9:35 | 详情页 | **展示Fix Suggestions** | "AI还会给出改进建议" | bg-blue-50卡片 + Lightbulb图标 + TrendingUp图标 |
| 9:40 | 详情页 | 展示Match Reasons | "匹配原因以Badge形式列出" | Badge variant="secondary" |
| 9:45 | 详情页 | 展示Key Info cards | "关键信息卡片显示deadline、奖金、团队规模、地区" | 4列grid |
| 9:50 | 详情页 | 点击"Add to Pipeline" | "把这个机会加入我们的追踪Pipeline" | Plus图标 + "Add to Pipeline"

---

### 第五幕：Pipeline管理 (2分钟) ⭐拖拽+紧急度+结果反馈

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 9:55 | `/pipeline` | 展示Kanban看板 | "Pipeline是一个Kanban风格的看板" | 5列布局(grid-cols-5)，桌面版 |
| 10:00 | `/pipeline` | **介绍6个阶段** | "从发现、准备、提交、待审、赢得，到归档" | stages数组: discovered/preparing/submitted/pending/won/lost |
| 10:05 | `/pipeline` | 指向列标题 | "每列显示阶段名称和项目数量" | 列标题 + Badge显示count |
| 10:10 | `/pipeline` | **悬停列标题的HelpCircle图标** | "悬停问号图标查看阶段说明和提示" | `<Tooltip>` 显示description和tips列表 |
| 10:15 | `/pipeline` | **指向卡片左边框颜色** | "4px左边框颜色表示紧急度" | urgency系统: critical(红)/urgent(橙)/warning(黄)/safe(灰) |
| 10:20 | `/pipeline` | **指向紧急卡片的动画** | "紧急的机会有脉冲动画" | `animate-urgency-pulse`(critical) / `animate-urgency-glow`(urgent) / `animate-urgency-subtle`(warning) |
| 10:25 | `/pipeline` | 指向URGENT徽章 | "最紧急的还会显示红色URGENT徽章" | bg-urgency-critical/10 + 红色文字 |
| 10:30 | `/pipeline` | **拖拽卡片演示(桌面版)** | "拖拽卡片就可以更新状态" | cursor-grab，拖拽时opacity-50 scale-95 + ring-2 ring-primary |
| 10:35 | `/pipeline` | 将卡片拖到目标列 | "目标列会高亮显示" | `dragOverStage`状态，bg-primary/10 ring-2 ring-primary |
| 10:40 | `/pipeline` | 放下卡片 | "松开完成移动，自动保存到后端" | `moveMutation`调用API |
| 10:45 | `/pipeline` | **点击卡片右上角三点菜单** | "也可以通过菜单操作" | MoreVertical图标，h-6 w-6 |
| 10:50 | `/pipeline` | 展示菜单选项 | "可以快速移动到任意阶段" | 5个阶段选项(除lost) + 分隔线 |
| 10:55 | `/pipeline` | 指向"Generate Materials"选项 | "直接生成材料" | Sparkles图标，链接到`/generator?batch_id=` |
| 11:00 | `/pipeline` | **指向"Mark as Won"选项** | "标记为赢得" | Trophy图标，text-green-600 |
| 11:05 | `/pipeline` | **点击"Mark as Won"** | "会弹出反馈收集弹窗" | `<ResultFeedbackModal>` 弹出 |
| 11:10 | `/pipeline` | **展示ResultFeedbackModal** | "系统会收集你的反馈" | 可选择won/lost/withdrew + 添加notes |
| 11:15 | `/pipeline` | 提交反馈 | "反馈帮助我们改进推荐" | 提交后卡片移动到Won列 |
| 11:20 | `/pipeline` | 指向"Archive / Didn't Win"选项 | "或者归档没赢的机会" | Archive图标，text-orange-600 |
| 11:25 | `/pipeline` | **展示底部Archived区域** | "归档的机会显示在底部" | `<Card>` + Archive图标 + 3列grid |
| 11:30 | `/pipeline` | 指向恢复按钮 | "可以恢复归档的机会" | RotateCcw图标，移回discovered |
| 11:35 | `/pipeline` | 指向删除按钮 | "或者永久删除" | Trash2图标，text-red-500 |
| 11:40 | `/pipeline` | **指向卡片的"Move to X"按钮** | "每个卡片底部有快速移动按钮" | 显示下一个阶段，ChevronRight图标 |
| 11:45 | `/pipeline` | 点击卡片标题 | "点击标题跳转到机会详情" | 链接到 `/opportunities/[id]` |

> **移动端展示（可选）**：
> - 顶部显示Stage Selector，左右滑动切换阶段
> - 进度点显示所有阶段，点击快速跳转
> - 卡片列表使用AnimatePresence动画切换
> - 不支持拖拽，通过菜单操作移动

---

### 第六幕：AI材料生成 (2分30秒) ⭐核心功能+Profile自动填充

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 11:50 | `/generator` | 进入AI Generator | "现在来看最强大的功能：AI材料生成器" | motion.div opacity+y动画 |
| 11:55 | `/generator` | **展示Header区域** | "标题旁边的14x14图标和文字" | Sparkles图标 + rounded-2xl容器 |
| 12:00 | `/generator` | **指向For: badge(如从机会页来)** | "如果从机会页进入，会显示关联的机会" | Zap图标 + sky-100背景 |
| 12:05 | `/generator` | **指向Profile自动填充badge** | "注意这个badge：表单已从Profile自动填充" | `<Badge variant="ai">` + User图标 + "Pre-filled from profile" |
| 12:10 | `/generator` | **展示材料类型选项** | "支持生成4种材料" | 4列网格(md:grid-cols-4) |
| 12:15 | `/generator` | 指向每种类型 | "README、3分钟演讲稿、Demo脚本、Q&A准备" | 图标：FileText/Mic/PlayCircle/HelpCircle，每种有独特颜色 |
| 12:20 | `/generator` | **点击选择"3分钟演讲稿"** | "让我们生成一个3分钟的演讲稿" | 选中卡片：彩色border + Check图标在右上角(圆形背景) |
| 12:25 | `/generator` | 再选择"Q&A Prep" | "可以同时选择多种类型" | 多个卡片选中状态，whileHover y:-4 |
| 12:30 | `/generator` | **展示表单区域** | "填写项目信息，已从Profile自动填充" | Bot图标 + "Tell us about your project" |
| 12:35 | `/generator` | **指向已填充的字段** | "项目名和技术栈已自动填充" | 从profile.product_name和profile.tech_stack读取 |
| 12:40 | `/generator` | 检查/修改Project Name | "可以修改或确认" | Input h-12 rounded-xl |
| 12:45 | `/generator` | 输入Problem Statement | "开发者花费大量时间阅读和理解文档" | textarea min-h-100px，rounded-xl |
| 12:55 | `/generator` | 输入Your Solution | "AI驱动的文档问答和摘要工具" | - |
| 13:05 | `/generator` | 检查Tech Stack | "技术栈已自动填充，可以补充" | 逗号分隔的字符串 |
| 13:10 | `/generator` | **点击生成按钮** | "点击生成，AI开始工作" | 按钮 size="lg" w-full，显示Sparkles图标 |
| 13:15 | `/generator` | **展示loading状态** | "按钮显示加载状态" | Loader2 animate-spin + "AI is generating your materials..." |
| 13:20 | `/generator` | **展示生成动画卡片** | "这个动画真的很酷" | Card variant="feature"，Bot图标rotate-360动画(3s infinite) |
| 13:25 | `/generator` | 指向进度说明 | "显示正在生成的材料类型" | Badge列表显示选中的types |
| 13:35 | `/generator` | **展示生成结果** | "专业的材料已经生成好了" | Check图标(绿色) + "Generated Materials"标题 |
| 13:40 | `/generator` | 展示3分钟演讲稿卡片 | "每种材料有独立的卡片" | Card variant="elevated"，图标用type对应的颜色 |
| 13:45 | `/generator` | 滚动查看内容 | "包含完整的演讲结构" | pre whitespace-pre-wrap，max-h-400px滚动 |
| 13:50 | `/generator` | **点击复制按钮** | "一键复制到剪贴板" | AnimatePresence切换Copy→Copied!，绿色Check图标 |
| 13:55 | `/generator` | 展示Toast提示 | "复制成功会有Toast提示" | success toast: "Copied to clipboard" |
| 14:00 | `/generator` | 展示Q&A Prep卡片 | "Q&A准备材料也生成好了" | 多个材料卡片垂直排列 |

---

### 第七幕：材料管理 (1分30秒) ⭐版本历史+比较功能

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 14:05 | `/materials` | 展示材料库 | "所有生成的材料都保存在材料库中" | motion.div渐入动画 |
| 14:10 | `/materials` | **展示页面Header** | "右上角可以快速生成新材料" | Plus图标 + "Generate New"按钮 |
| 14:15 | `/materials` | 展示材料卡片列表 | "每个材料有独立的卡片" | grid gap-4布局 |
| 14:20 | `/materials` | **指向卡片Header区域** | "显示材料类型图标、标题、类型badge" | 10x10圆角图标容器 + Badge |
| 14:25 | `/materials` | 指向时间戳 | "显示创建时间" | Clock图标 + `formatRelativeTime` |
| 14:30 | `/materials` | 指向关联机会 | "显示关联的机会名称" | "For: {opportunity_title}" |
| 14:35 | `/materials` | **指向版本号badge(v2+)** | "如果有多个版本，显示版本号" | History图标 + Badge "v{version}" |
| 14:40 | `/materials` | **点击History按钮** | "点击查看版本历史" | History图标按钮，选中时bg-secondary |
| 14:45 | `/materials` | **展示VersionHistory面板** | "版本历史面板展开" | AnimatePresence动画，bg-secondary/10 |
| 14:50 | `/materials` | 展示版本列表 | "可以查看所有历史版本" | `<VersionHistory>` 组件 |
| 14:55 | `/materials` | 指向Restore按钮 | "可以恢复到任意历史版本" | "Restore按钮 |
| 15:00 | `/materials` | **点击Compare按钮(如有)** | "可以比较两个版本的差异" | 弹出VersionCompare modal |
| 15:05 | `/materials` | **展示VersionCompare弹窗** | "差异比较帮助你了解变化" | `<VersionCompare>` 组件 |
| 15:10 | `/materials` | 关闭弹窗 | - | 点击关闭或外部区域 |
| 15:15 | `/materials` | **点击ChevronDown/Up展开卡片** | "点击展开查看完整内容" | AnimatePresence展开动画 |
| 15:20 | `/materials` | 展示完整内容 | "可以滚动查看完整材料" | pre max-h-500px滚动，scrollbar-modern |
| 15:25 | `/materials` | 点击Copy按钮 | "一键复制使用" | Check图标 + "Copied!"文字变化 |
| 15:30 | `/materials` | 指向Delete按钮 | "不需要的材料可以删除" | Trash2图标，红色hover效果 |

---

### 第八幕：Profile与Settings (1分30秒)

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 15:35 | `/profile` | 快速展示Profile页面 | "在Profile页面可以完善个人资料" | User图标 + "Your Profile"标题 |
| 15:40 | `/profile` | **指向Profile Active badge** | "如果已创建Profile会显示Active状态" | Badge variant="success" |
| 15:45 | `/profile` | **展示Profile Type选择** | "选择你的身份类型" | 5个按钮: developer/student/startup/designer/researcher |
| 15:50 | `/profile` | **展示Tech Stack卡片** | "选择你的技术栈" | Code图标，27个技术标签可选 |
| 15:55 | `/profile` | 演示点击选择多个技术 | "点击选中，再点击取消" | Badge variant切换default/outline |
| 16:00 | `/profile` | **展示Industries卡片** | "选择感兴趣的行业领域" | Target图标，10个选项 |
| 16:05 | `/profile` | **展示Goals卡片** | "设置你的目标" | 2列grid，6个选项按钮 |
| 16:10 | `/profile` | 演示选择Goals | "可以多选" | border-primary bg-sky-50选中效果 |
| 16:15 | `/profile` | **展示Availability卡片** | "设置可用时间和团队规模偏好" | Clock图标 |
| 16:20 | `/profile` | 指向Hours per week | "每周可投入的小时数" | Input type="number" |
| 16:25 | `/profile` | 指向Team size preference | "偏好的团队规模范围" | Min/Max两个输入框 |
| 16:30 | `/profile` | 点击Save按钮 | "保存后会自动重新计算匹配" | Save图标 + "Update Profile" |
| 16:35 | `/settings` | 进入Settings页面 | "Settings页面有更多设置选项" | max-w-3xl布局 |
| 16:40 | `/settings` | **展示Connected Accounts卡片** | "可以连接GitHub和Google账号" | SVG图标 + 连接状态 |
| 16:45 | `/settings` | 指向Connect/Disconnect按钮 | "连接或断开OAuth账号" | Button variant="outline" size="sm" |
| 16:50 | `/settings` | **展示Data Export卡片** | "可以导出你的所有数据" | JSON和CSV两种格式 |
| 16:55 | `/settings` | **展示Calendar Subscription卡片** | "订阅日历获取所有deadline" | - |
| 17:00 | `/settings` | 点击"Get Subscription URL" | "获取订阅链接" | 加载后显示URL输入框 |
| 17:05 | `/settings` | 指向使用说明 | "支持Google Calendar、Outlook、Apple Calendar" | ul列表说明 |
| 17:10 | `/settings` | **展示Guided Tours卡片** | "管理产品导览" | 3个tour列表 |
| 17:15 | `/settings` | 指向Dashboard Tour状态 | "显示完成状态" | Check图标 + "Completed"(如已完成) |
| 17:20 | `/settings` | 指向Replay按钮 | "可以重新播放任意导览" | RotateCcw图标 + "Replay" |
| 17:25 | `/settings` | 指向Reset All Tours按钮 | "或者重置所有导览状态" | ghost变体按钮在底部 |
| 17:30 | `/settings` | **展示Danger Zone** | "危险操作区域" | border-red-200边框 |

---

### 第九幕：收尾 (30秒)

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 17:35 | `/dashboard` | 回到Dashboard | "这就是OpportunityRadar的完整体验" | 页面过渡动画 |
| 17:40 | `/dashboard` | 展示整体界面 | "AI帮你发现机会、管理进度、准备材料" | 展示所有组件 |
| 17:45 | `/dashboard` | 再次指向Today's Focus | "每天登录，AI会为你推荐最重要的事" | TodaysFocusCard高亮 |
| 17:50 | `/dashboard` | 指向Quick Actions | "一键开始任何操作" | 3个快速操作卡片 |
| 17:55 | - | 展示Logo/结束画面 | "OpportunityRadar - 让AI帮你发现机会，赢得比赛" | 品牌结束画面 |
| 18:00 | - | 结束 | "感谢观看，立即注册开始你的机会发现之旅" | CTA文字 |

---

## UI交互细节参考

### 紧急度系统 (Urgency System)

| 级别 | 天数 | CSS类名 | 动画效果 | 位置 |
|------|------|---------|----------|------|
| Critical | ≤3天 | `border-l-urgency-critical` | `animate-urgency-pulse` | Pipeline卡片左边框、Deadline Calendar |
| Urgent | ≤7天 | `border-l-urgency-urgent` | `animate-urgency-glow` | Pipeline卡片左边框、Deadline Calendar |
| Warning | ≤14天 | `border-l-urgency-warning` | `animate-urgency-subtle` | Pipeline卡片左边框、Deadline Calendar |
| Safe | >14天 | `border-l-urgency-safe` | 无 | Pipeline卡片左边框 |
| Expired | 已过期 | `border-l-urgency-expired` | 无 | 灰色显示 |

**紧急度Badge样式**：
- Critical: `bg-urgency-critical/10 text-urgency-critical` + "URGENT"文字
- Dashboard统计卡片: `urgencyLabel` + `AlertTriangle`图标

### 匹配分数颜色

| 分数范围 | CSS类名 | Tailwind类 |
|----------|---------|------------|
| 80-100% | `bg-green-500` | 绿色badge |
| 60-79% | `bg-primary` | 蓝色badge |
| 40-59% | `bg-yellow-500` | 黄色badge |
| 0-39% | `bg-gray-400` | 灰色badge |

**Score Tooltip组件**：`<ScoreTooltip>` 悬停显示:
- 总分百分比
- 四维度分解 (semantic/rule/time/team)
- 匹配原因列表 (reasons)

### 四维度匹配分析

| 维度 | 说明 | 数据字段 | 详情页显示 |
|------|------|----------|------------|
| Relevance | 语义相关性分数 | `semantic_score` | `bg-secondary/50 rounded-lg` |
| Eligibility | 资格审查结果 | `rule_score` | CheckCircle2/AlertCircle/XCircle图标 |
| Timeline | 时间表匹配度 | `time_score` | 百分比显示 |
| Team Fit | 团队规模适配 | `team_score` | 百分比显示 |

**Eligibility Status显示**：
- `eligible`: CheckCircle2(绿) + "You meet all eligibility requirements"
- `partial`: AlertCircle(黄) + "You meet some requirements"
- `ineligible`: XCircle(红) + "Some eligibility issues found"

**Fix Suggestions**: `bg-blue-50 rounded-lg` + Lightbulb图标 + TrendingUp列表

### Profile Completion检查项

| 检查项 | Profile字段 | 检查逻辑 |
|--------|-------------|----------|
| Basic Info | `full_name`, `email` | 非空 |
| Bio | `description` | 非空 |
| Skills | `tech_stack` | 数组长度 > 0 |
| Interests | `industries` | 数组长度 > 0 |
| Experience | `experience_level` | 已设置 |
| Goals | `intents` | 数组长度 > 0 |
| Availability | `available_hours_per_week` | > 0 |

### Dashboard组件布局

| 组件 | 位置 | data-tour属性 |
|------|------|---------------|
| Header + HelpButton | 顶部 | `data-tour="welcome"` |
| ProfileCompletionCard | Header下方 | - |
| TodaysFocusCard | ProfileCompletion下方 | `data-tour="ai-assistant"` |
| Stats Grid (4卡片) | TodaysFocus下方 | `data-tour="stats"` |
| Top Matches + Pipeline Overview | 2列grid | `data-tour="top-matches"` |
| DeadlineCalendar | 底部 | - |
| Quick Actions | Calendar下方 | - |
| AIValueCard | 最底部 | - |

### 动画效果参考

| 效果 | 使用位置 | 实现方式 |
|------|----------|----------|
| 页面进入 | 所有页面 | `motion.div` opacity + y偏移 |
| 卡片hover | 各种卡片 | `whileHover={{ y: -4 }}` |
| 按钮点击 | Button | `whileTap={{ scale: 0.98 }}` |
| 搜索脉冲 | Opportunities搜索 | `isSearching && "animate-pulse"` |
| 拖拽反馈 | Pipeline | `isDragging && "opacity-50 scale-95"` |
| 复制成功 | Copy按钮 | `AnimatePresence` 切换图标 |
| 生成动画 | Generator | `rotate: 360` 3s无限循环 |

### Toast系统

| 类型 | 调用方式 | 样式 |
|------|----------|------|
| Success | `success(title, message)` | 绿色图标 |
| Warning | `warning(title, message, action?)` | 黄色图标 + 可选action按钮 |
| Error | `error(title, message)` | 红色图标 |

**Toast with Undo**: `warning("Dismissed", "...", { label: "Undo", onClick: () => {...} })`

---

## 关键演示点 Checklist

### 必须展示的功能
- [x] **URL智能提取** - Onboarding自动提取项目信息
- [x] **Profile Completion Card** - Dashboard进度追踪，7维度检查 ⭐
- [x] **Today's Focus Card** - AI每日智能推荐 ⭐
- [x] **AI Value Card** - AI价值统计展示 ⭐新增
- [x] **Dashboard统计概览** - 4个Stats卡片，紧急警告badge
- [x] **Pipeline Overview** - 5阶段进度条可视化
- [x] **Deadline Calendar** - 14天日历视图，颜色编码 ⭐
- [x] **Quick Actions** - 3个快速操作入口
- [x] **防抖搜索功能** - 300ms防抖+搜索图标脉冲动画 ⭐
- [x] **Score Tooltip** - 悬停显示四维度分解 ⭐新增
- [x] **悬停快速操作** - 收藏/忽略/添加Pipeline三按钮
- [x] **Quick Prep按钮** - 渐变背景一键准备 ⭐
- [x] **紧急度可视化** - 4px左边框+3种动画+URGENT badge ⭐
- [x] **四维度匹配分析** - 详情页Score Breakdown (Relevance/Eligibility/Timeline/Team Fit)
- [x] **Eligibility Status** - 三色图标状态显示 ⭐
- [x] **Fix Suggestions** - AI改进建议蓝色卡片 ⭐
- [x] **Calendar集成** - Google/Outlook/iCal三选项 ⭐
- [x] **拖拽Pipeline** - Kanban看板+Drop zone高亮
- [x] **Pipeline菜单操作** - 6个阶段快速移动
- [x] **Result Feedback Modal** - Won/Lost反馈收集 ⭐新增
- [x] **Archived区域** - 底部Lost items管理
- [x] **Profile Auto-fill** - Generator自动从Profile填充 ⭐新增
- [x] **AI材料生成** - 4类型多选+Bot旋转动画
- [x] **版本历史** - Materials版本管理+比较功能 ⭐
- [x] **Help按钮** - Dashboard右上角导览触发 ⭐
- [x] **Tour管理** - Settings中3个导览的Replay/Reset ⭐
- [x] **Data Export** - JSON/CSV两种格式导出
- [x] **Calendar Subscription** - 订阅URL+使用说明

### 可选展示的功能（如有额外时间）
- [ ] 移动端Pipeline单列视图 (Stage Selector + 进度点)
- [ ] 高级过滤面板 (AdvancedFilters组件)
- [ ] 键盘快捷键 (KeyboardShortcutsModal)
- [ ] 日历订阅详细设置
- [ ] 社区提交 (/community)
- [ ] 团队功能 (/teams)
- [ ] 通知中心 (/notifications)
- [ ] Admin后台 (/admin)

---

## DoxMind 项目信息参考

用于填写表单时的参考内容：

```
项目名称: DoxMind
一句话描述: AI-powered documentation assistant

问题陈述:
开发者和团队每天花费大量时间阅读、搜索和理解技术文档，
效率低下且容易遗漏关键信息。

解决方案:
DoxMind是一个AI驱动的文档助手，通过RAG技术实现智能问答，
帮助用户快速获取文档中的关键信息，提升10倍阅读效率。

技术栈:
Next.js, TypeScript, Python, FastAPI, LLM, RAG, Vector Database

目标用户:
- 软件开发者
- 技术团队
- 文档密集型企业

核心功能:
1. 智能文档问答
2. 自动摘要生成
3. 多文档关联分析
4. 团队知识库管理
```

---

## 录制后处理

- [ ] 剪辑去除多余等待时间（API响应等待）
- [ ] 添加字幕（中英双语字幕推荐）
- [ ] 添加背景音乐（可选，建议轻柔的科技感音乐）
- [ ] 添加Logo水印（右下角）
- [ ] 添加UI高亮标注（用箭头指向⭐新功能）
- [ ] 添加章节标记（按9幕分段）
- [ ] 导出为MP4格式（1080p 30fps）
- [ ] 上传到YouTube/视频平台
- [ ] 添加视频描述和时间戳跳转

---

## 备注

### 录制前准备
- 如遇到加载缓慢，可以提前预热页面（访问一遍所有页面）
- 准备备用方案：如果AI提取失败，手动填写信息继续
- **首次录制前请重置Tour状态**（Settings → Reset All Tours）
- 确保Profile有product_name和tech_stack字段，以展示Generator自动填充
- 清空Materials页面或确保有多版本材料展示版本历史

### 数据准备
- 确保数据库中有不同紧急度的机会：
  - 至少2个≤3天的（展示Critical动画）
  - 至少2个≤7天的（展示Urgent动画）
  - 至少2个≤14天的（展示Warning样式）
- 确保Pipeline各阶段有数据
- 确保至少有一个材料有多个版本（展示版本历史）

### 录制技巧
- 录制多个版本，选择最流畅的一个
- 鼠标移动要平稳，避免快速晃动
- 点击操作后稍作停顿，让动画完整展示
- 对于悬停效果（如Quick Prep按钮），悬停1-2秒再操作
- Toast提示出现后停顿1秒让观众看到

### 时间分配（总计约18分钟）
| 幕 | 内容 | 时长 |
|---|------|------|
| 1 | 开场与注册 | 1分钟 |
| 2 | Onboarding引导 | 2分30秒 |
| 3 | Dashboard概览 | 2分30秒 |
| 4 | 发现与筛选机会 | 3分30秒 |
| 5 | Pipeline管理 | 2分钟 |
| 6 | AI材料生成 | 2分30秒 |
| 7 | 材料管理 | 1分30秒 |
| 8 | Profile与Settings | 1分30秒 |
| 9 | 收尾 | 30秒 |
