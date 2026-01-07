# OpportunityRadar Demo 录制计划

> 使用网站: https://doxmind.com/

---

## 概述

- **预计时长**: 约14分钟 (包含注册、完整Onboarding 3步流程、所有核心功能展示)
- **目标受众**: 潜在用户、投资人、合作伙伴
- **核心卖点**: AI驱动的机会匹配 + 智能材料生成 + 智能Onboarding + 紧急度管理

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

### 第三幕：Dashboard概览 (2分钟) ⭐新增功能展示

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 3:30 | `/dashboard` | 展示整体界面 | "这是你的个人仪表板" | 页面进入动画(opacity + y偏移) |
| 3:35 | `/dashboard` | **指向Help按钮(右上角)** | "首次访问会自动开始产品导览，也可以随时点击问号按钮重新查看" | 帮助图标(HelpCircle) + tooltip |
| 3:45 | `/dashboard` | **展示Profile Completion卡片** | "这里显示你的个人资料完成度" | 进度条动画填充 |
| 3:50 | `/dashboard` | 指向7个检查项 | "7个维度：基本信息、简介、技能、兴趣、经历、目标、可用时间" | 小图标显示完成状态(✓/○) |
| 4:00 | `/dashboard` | 点击"Complete Next Step"按钮 | "点击可以快速完善下一项" | 按钮hover效果 |
| 4:10 | `/dashboard` | **展示Today's Focus卡片** | "AI每天为你推荐最重要的事项" | 渐变背景卡片 |
| 4:20 | `/dashboard` | 指向主推荐 | "主推荐显示最紧急的deadline或待处理事项" | 优先级badge(high/medium/low) |
| 4:30 | `/dashboard` | 指向辅助推荐列表 | "下方还有2个辅助推荐" | 小卡片列表 |
| 4:40 | `/dashboard` | 指向统计卡片 | "顶部4个统计卡片显示关键数据" | 彩色卡片(primary/green/yellow/purple) |
| 4:50 | `/dashboard` | **指向Pipeline卡片的紧急警告** | "注意这里的红色警告，表示有紧急deadline" | 红色感叹号badge + "X urgent" 文字 |
| 5:00 | `/dashboard` | 指向Top Matches | "这里是匹配度最高的机会" | 绿色分数badge表示高匹配度 |
| 5:10 | `/dashboard` | **展示Deadline Calendar** | "日历视图显示未来14天的所有deadline" | 14列时间线 |
| 5:15 | `/dashboard` | 指向日历颜色 | "红色表示紧急，橙色表示即将到期" | 颜色编码(red/orange/yellow/gray) |
| 5:20 | `/dashboard` | 悬停一个日期 | "悬停查看当天的机会详情" | Tooltip显示机会名称 |
| 5:25 | `/dashboard` | 点击导航进入Opportunities | "让我们看看所有匹配的机会" | 侧边栏nav item hover效果 |

---

### 第四幕：发现与筛选机会 (3分钟) ⭐搜索+紧急度+快速操作

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 5:30 | `/opportunities` | 展示机会列表 | "Opportunities页面显示所有为你匹配的机会" | 3列网格布局 |
| 5:40 | `/opportunities` | **展示搜索框** | "可以通过关键词搜索感兴趣的机会" | 搜索图标 + placeholder文字 |
| 5:50 | `/opportunities` | 输入搜索词"AI" | "比如搜索AI相关的机会" | **输入时搜索图标有脉冲动画** |
| 5:55 | `/opportunities` | 等待搜索结果 | "搜索使用防抖技术，输入停止后自动搜索" | **300ms防抖后列表过滤** |
| 6:00 | `/opportunities` | 点击清除按钮 | "点击X清除搜索" | 清除按钮hover效果 |
| 6:05 | `/opportunities` | 展示类型过滤器 | "可以按类型筛选" | 4个类别按钮(All/Hackathon/Grant/Bounty) |
| 6:10 | `/opportunities` | 选择Hackathon | "比如只看Hackathon类型的机会" | 按钮选中状态(filled背景) |
| 6:15 | `/opportunities` | 展示过滤状态切换 | "还可以查看已收藏或已忽略的机会" | All/Bookmarked/Dismissed tabs |
| 6:25 | `/opportunities` | **指向机会卡片的紧急度边框** | "注意卡片左边的彩色边框表示紧急度" | 红色=紧急，橙色=即将，黄色=注意 |
| 6:30 | `/opportunities` | **指向一个紧急机会的脉冲动画** | "红色边框还会有脉冲动画，提醒你注意" | 左边框4px + 脉冲效果 |
| 6:40 | `/opportunities` | 悬停在卡片上 | "悬停可以看到快速操作按钮" | **顶部工具栏滑入动画** |
| 6:45 | `/opportunities` | **指向3个悬停按钮** | "收藏、忽略、添加到Pipeline" | 星标/X/+图标 |
| 6:50 | `/opportunities` | **点击收藏按钮** | "点击星标收藏感兴趣的机会" | 星标变为填充状态(黄色) |
| 6:55 | `/opportunities` | 展示收藏成功反馈 | "收藏的机会可以在Bookmarked中查看" | Toast提示 |
| 7:00 | `/opportunities` | **指向Quick Prep按钮** | "Quick Prep一键开始准备这个机会" | 渐变背景按钮 |
| 7:05 | `/opportunities` | 点击Quick Prep | "它会自动添加到Pipeline并跳转到AI生成器" | 按钮loading → 页面跳转 |
| 7:10 | - | (跳过，先返回) | "稍后我们会详细演示，先看看机会详情" | 点击浏览器返回 |
| 7:15 | `/opportunities` | 点击一个高匹配度的机会 | "点击卡片查看详情" | 卡片hover阴影效果 |
| 7:20 | `/opportunities/[id]` | 展示详情页顶部 | "详情页显示完整的机会信息" | 返回按钮 + 标题区域 |
| 7:30 | 详情页 | 指向顶部操作按钮 | "顶部有多个操作按钮" | 收藏/忽略/加入Pipeline/生成材料 |
| 7:35 | 详情页 | **展示Calendar下拉菜单** | "点击日历图标可以添加到你的日历" | 下拉显示3个选项 |
| 7:40 | 详情页 | 指向3个日历选项 | "支持Google Calendar、Outlook和iCal下载" | Google/Outlook/iCal图标 |
| 7:50 | 详情页 | **重点展示Match Score卡片** | "这是AI的匹配分析核心" | 大号分数显示 |
| 8:00 | 详情页 | **指向四维度分数** | "四个维度详细评估" | 4列grid布局 |
| 8:05 | 详情页 | 解释Relevance | "Relevance - 项目与机会的语义相关性" | 分数百分比 |
| 8:10 | 详情页 | 解释Eligibility | "Eligibility - 资格审查是否通过" | 绿色/黄色/红色指示 |
| 8:15 | 详情页 | 解释Timeline | "Timeline - 时间表是否匹配" | 分数百分比 |
| 8:20 | 详情页 | 解释Team Fit | "Team Fit - 团队规模是否适合" | 分数百分比 |
| 8:25 | 详情页 | **展示Eligibility Issues(如有)** | "如果有资格问题，会列出具体原因" | 问题列表 + 黄色/红色图标 |
| 8:30 | 详情页 | **展示Fix Suggestions** | "AI还会给出改进建议" | 蓝色背景卡片 + 建议列表 |
| 8:40 | 详情页 | 点击"Add to Pipeline" | "把这个机会加入我们的追踪Pipeline" | 按钮状态变化 |

---

### 第五幕：Pipeline管理 (1分30秒) ⭐拖拽+紧急度

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 8:45 | `/pipeline` | 展示Kanban看板 | "Pipeline是一个Kanban风格的看板" | 5列布局(桌面版) |
| 8:50 | `/pipeline` | 介绍5个阶段 | "从发现、准备、提交、待审、到赢得" | 列标题 + 项目计数badge |
| 8:55 | `/pipeline` | **指向卡片左边框颜色** | "颜色表示紧急度" | 红/橙/黄/灰色边框 |
| 9:00 | `/pipeline` | **指向紧急卡片的动画** | "紧急的机会有脉冲动画和URGENT徽章" | 脉冲效果 + 红色URGENT badge |
| 9:10 | `/pipeline` | **拖拽卡片演示** | "拖拽卡片就可以更新状态" | 拖拽时卡片阴影增强 |
| 9:15 | `/pipeline` | 将卡片拖到目标列 | "目标列会高亮显示" | **Drop zone边框高亮** |
| 9:20 | `/pipeline` | 放下卡片 | "松开完成移动" | 卡片动画到新位置 |
| 9:25 | `/pipeline` | **点击卡片右上角三点菜单** | "点击更多选项" | 垂直三点图标 |
| 9:30 | `/pipeline` | 展示菜单选项 | "可以快速移动到任意阶段" | 下拉菜单显示所有阶段 |
| 9:35 | `/pipeline` | 指向"Generate Materials"选项 | "或者直接生成材料" | 菜单项hover效果 |
| 9:40 | `/pipeline` | 指向"Mark as Won"选项 | "标记为赢得会移到Won列" | - |
| 9:45 | `/pipeline` | **展示底部Archived区域** | "失败的机会会归档在底部" | Lost items网格 |
| 9:50 | `/pipeline` | 指向恢复按钮 | "可以恢复归档的机会" | Restore按钮 |
| 9:55 | `/pipeline` | 悬停列标题 | "悬停列标题查看说明和提示" | Stage helper tooltip |

> **移动端展示（可选）**：展示手机端的单列滑动视图，左右滑动切换阶段，点击进度点快速跳转

---

### 第六幕：AI材料生成 (2分钟) ⭐核心功能

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 10:00 | `/generator` | 进入AI Generator | "现在来看最强大的功能：AI材料生成器" | 页面进入动画 |
| 10:10 | `/generator` | 展示材料类型选项 | "支持生成4种材料" | 4列网格卡片 |
| 10:15 | `/generator` | 指向每种类型 | "README、3分钟演讲稿、Demo脚本、Q&A准备" | 图标：FileText/Mic/PlayCircle/HelpCircle |
| 10:25 | `/generator` | 点击选择"3分钟演讲稿" | "让我们生成一个3分钟的演讲稿" | **卡片选中：彩色边框 + 背景 + 对勾** |
| 10:30 | `/generator` | 可以多选其他类型 | "可以同时选择多种类型" | 多个卡片选中状态 |
| 10:35 | `/generator` | 展示表单区域 | "填写项目信息" | 表单自动从Profile填充(如有) |
| 10:40 | `/generator` | 输入Project Name | "DoxMind" | 输入框focus效果 |
| 10:45 | `/generator` | 输入Problem Statement | "开发者花费大量时间阅读和理解文档" | textarea自动增高 |
| 10:55 | `/generator` | 输入Your Solution | "AI驱动的文档问答和摘要工具" | - |
| 11:05 | `/generator` | 输入Tech Stack | "Next.js, Python, LLM, RAG" | 逗号分隔 |
| 11:15 | `/generator` | **点击生成按钮** | "点击生成，AI开始工作" | 按钮变为loading |
| 11:20 | `/generator` | **展示生成动画** | "几秒钟后..." | 旋转机器人图标 + 脉冲效果 |
| 11:25 | `/generator` | 展示进度列表 | "显示正在生成的材料类型" | 选中的material列表 |
| 11:40 | `/generator` | **展示生成结果** | "一份专业的3分钟演讲稿就生成好了" | 材料卡片渐入动画 |
| 11:50 | `/generator` | 滚动查看内容 | "包含开场白、问题陈述、解决方案、技术亮点、结尾" | 可滚动内容区(max-h-400px) |
| 12:00 | `/generator` | **点击复制按钮** | "一键复制到剪贴板" | 按钮文字变"Copied!" + 对勾图标 |
| 12:05 | `/generator` | 如有多个材料，展示切换 | "其他材料也都生成好了" | 多个材料卡片 |

---

### 第七幕：材料管理 (1分钟) ⭐版本历史功能

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 12:10 | `/materials` | 展示材料库 | "所有生成的材料都保存在材料库中" | 卡片列表 |
| 12:15 | `/materials` | 指向材料卡片 | "每个材料显示类型、创建时间、关联的机会" | 图标 + badge + 时间戳 |
| 12:20 | `/materials` | **指向版本号徽章** | "如果重新生成过，会显示版本号" | v1, v2等版本badge |
| 12:25 | `/materials` | **点击Version History按钮** | "点击查看版本历史" | 按钮展开面板 |
| 12:30 | `/materials` | 展示版本列表 | "可以查看所有历史版本" | 版本列表 + 时间戳 |
| 12:35 | `/materials` | 指向恢复按钮 | "可以恢复到任意历史版本" | Restore按钮 |
| 12:40 | `/materials` | 点击Expand按钮 | "点击展开查看完整内容" | 内容区域展开动画 |
| 12:45 | `/materials` | 点击Copy按钮 | "随时复制使用" | 复制成功反馈 |
| 12:50 | `/materials` | 点击"Generate New"按钮 | "点击这里生成新材料" | 按钮链接到/generator |

---

### 第八幕：Profile与Settings (1分钟)

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 12:55 | `/profile` | 快速展示Profile页面 | "在Profile页面可以完善个人资料" | 表单布局 |
| 13:00 | `/profile` | 指向Tech Stack选择 | "选择你的技术栈" | 标签式多选网格 |
| 13:05 | `/profile` | 指向Goals选择 | "设置你的目标" | 2列网格多选 |
| 13:10 | `/profile` | 指向Availability设置 | "设置可用时间和团队规模" | 数字输入框 |
| 13:15 | `/settings` | 进入Settings页面 | "Settings页面有更多设置选项" | - |
| 13:20 | `/settings` | 展示Connected Accounts | "可以连接GitHub和Google账号" | 连接状态显示 |
| 13:25 | `/settings` | **展示Calendar Subscription** | "可以订阅日历获取所有deadline" | URL + 复制按钮 |
| 13:30 | `/settings` | 指向使用说明 | "支持Google Calendar、Outlook、Apple Calendar" | 说明文字 |
| 13:35 | `/settings` | **展示Guided Tours区域** | "这里可以管理产品导览" | Tour状态列表 |
| 13:40 | `/settings` | 指向Replay按钮 | "可以重新播放任意导览" | Replay/Start按钮 |
| 13:45 | `/settings` | 指向Reset All Tours | "或者重置所有导览状态" | 红色按钮 |

---

### 第九幕：收尾 (30秒)

| 时间 | 页面 | 操作 | 旁白要点 | UI细节 |
|------|------|------|----------|--------|
| 13:50 | `/dashboard` | 回到Dashboard | "这就是OpportunityRadar的完整体验" | 页面过渡动画 |
| 13:55 | `/dashboard` | 展示整体界面 | "AI帮你发现机会、管理进度、准备材料" | - |
| 14:00 | - | 展示Logo | "让AI帮你发现机会，赢得比赛" | 结束画面 |

---

## UI交互细节参考

### 紧急度系统 (Urgency System)

| 级别 | 天数 | 颜色 | 动画效果 | 位置 |
|------|------|------|----------|------|
| Critical | ≤3天 | 红色 (#DC2626) | 脉冲动画 | 卡片左边框、日历、badge |
| Urgent | ≤7天 | 橙色 (#EA580C) | 发光效果 | 卡片左边框、日历、badge |
| Warning | ≤14天 | 黄色 (#D97706) | 微妙动画 | 卡片左边框、日历 |
| Safe | >14天 | 灰色 | 无 | 卡片左边框、日历 |
| Expired | 已过期 | 灰色 | 无 | - |

### 匹配分数颜色

| 分数范围 | 颜色 | 含义 |
|----------|------|------|
| 80-100% | 绿色 | 高匹配度 |
| 60-79% | 蓝色 | 良好匹配 |
| 40-59% | 黄色 | 一般匹配 |
| 0-39% | 灰色 | 低匹配度 |

### 四维度匹配分析

| 维度 | 说明 | 数据来源 |
|------|------|----------|
| Relevance | 语义相关性分数 | semantic_score |
| Eligibility | 资格审查结果 | rule_score (绿✓/黄⚠/红✗) |
| Timeline | 时间表匹配度 | time_score |
| Team Fit | 团队规模适配 | team_score |

### Profile Completion检查项

| 检查项 | 说明 |
|--------|------|
| Basic Info | 基本信息(姓名、邮箱) |
| Bio | 个人简介 |
| Skills | 技术栈选择 |
| Interests | 兴趣领域 |
| Experience | 经验水平 |
| Goals | 目标设置 |
| Availability | 可用时间 |

---

## 关键演示点 Checklist

### 必须展示的功能
- [x] **URL智能提取** - Onboarding自动提取项目信息
- [x] **Profile Completion Card** - Dashboard进度追踪 ⭐新增
- [x] **Today's Focus Card** - AI每日推荐 ⭐新增
- [x] **Dashboard统计概览** - 展示匹配数、进度、紧急警告
- [x] **Deadline Calendar** - 14天日历视图 ⭐新增
- [x] **防抖搜索功能** - 关键词搜索+脉冲动画
- [x] **悬停快速操作** - 收藏/忽略/添加Pipeline
- [x] **Quick Prep按钮** - 一键开始准备 ⭐新增
- [x] **紧急度可视化** - 颜色边框+动画+badge ⭐新增
- [x] **四维度匹配分析** - 机会详情页Score Breakdown
- [x] **Fix Suggestions** - AI改进建议 ⭐新增
- [x] **Calendar集成** - Google/Outlook/iCal ⭐新增
- [x] **拖拽Pipeline** - Kanban看板+视觉反馈
- [x] **Pipeline菜单操作** - 快速移动/生成材料
- [x] **AI材料生成** - 多类型选择+生成动画
- [x] **版本历史** - Materials版本管理 ⭐新增
- [x] **Help按钮** - 产品导览触发 ⭐新增
- [x] **Tour管理** - Settings中的导览设置 ⭐新增

### 可选展示的功能（如有额外时间）
- [ ] 移动端Pipeline单列视图
- [ ] 高级过滤面板
- [ ] 键盘快捷键
- [ ] 日历订阅详细设置
- [ ] 社区提交
- [ ] 团队功能

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

- [ ] 剪辑去除多余等待时间
- [ ] 添加字幕（如需要）
- [ ] 添加背景音乐（可选）
- [ ] 添加Logo水印
- [ ] 添加UI高亮标注（指向新功能）
- [ ] 导出为MP4格式
- [ ] 上传到YouTube/视频平台

---

## 备注

- 如遇到加载缓慢，可以提前预热页面
- 准备备用方案：如果AI提取失败，手动填写信息继续
- 录制多个版本，选择最流畅的一个
- **首次录制前请重置Tour状态**，确保自动导览能正常触发
- 确保数据库中有不同紧急度的机会（3天内、7天内、14天内），以展示紧急度系统
- 确保至少有一个材料有多个版本，以展示版本历史功能
