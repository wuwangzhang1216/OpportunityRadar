# OpportunityRadar Demo 录制计划

> 使用网站: https://doxmind.com/

---

## 概述

- **预计时长**: 7-8分钟 (使用预设账号，跳过注册)
- **目标受众**: 潜在用户、投资人、合作伙伴
- **核心卖点**: AI驱动的机会匹配 + 智能材料生成

---

## 录制前准备

### 环境检查
- [ ] 后端服务运行正常 (`docker-compose up`)
- [ ] 前端服务运行正常 (`npm run dev`)
- [ ] 数据库中有足够的机会数据
- [ ] 清除浏览器缓存，使用无痕模式
- [ ] **运行Demo账号创建脚本** (见下方)

### 录制工具
- [ ] 屏幕录制软件 (OBS / Loom / 系统自带)
- [ ] 分辨率设置: 1920x1080
- [ ] 麦克风测试 (如需配音)

---

## Demo 账号信息

### 创建Demo账号

在录制前运行以下命令创建/更新Demo账号：

```bash
python scripts/demo/create_demo_account.py
```

### 测试所有Demo API

运行测试脚本验证所有演示中会用到的API：

```bash
python scripts/demo/test_demo_apis.py
```

测试覆盖的功能：
- 认证登录
- Dashboard统计和Top匹配
- 机会列表和详情
- 匹配收藏/驳回
- Pipeline创建和阶段更新
- AI材料生成
- Profile获取
- 通知系统

### 登录凭证

| 字段 | 值 |
|------|-----|
| **Email** | `demo@doxmind.com` |
| **Password** | `DemoRadar2024!` |
| **Name** | DoxMind Team |

### 预设Profile信息

Demo账号已预填以下信息（基于 https://doxmind.com/）：

| 字段 | 值 |
|------|-----|
| 团队名称 | DoxMind |
| 产品描述 | AI-powered documentation assistant |
| 技术栈 | Python, TypeScript, Next.js, FastAPI, LLM, RAG, Vector Database |
| 团队规模 | 3人 |
| 公司阶段 | MVP |
| 产品阶段 | Beta |
| 融资状态 | Bootstrapped, 寻求 $100K-$500K |
| 目标 | win_hackathons, get_funding, build_network, learn_skills |
| 兴趣领域 | AI/ML, Developer Tools, Productivity, Documentation, SaaS |

---

## Demo 脚本

### 第一幕：开场与登录 (30秒)

| 时间 | 页面 | 操作 | 旁白要点 |
|------|------|------|----------|
| 0:00 | `/` | 展示首页 | "欢迎使用OpportunityRadar，一个AI驱动的机会发现平台" |
| 0:15 | `/` | 滚动查看功能介绍 | "帮助开发者和创业团队发现最匹配的Hackathon、Grant、Bounty等机会" |
| 0:25 | `/login` | 点击登录 | "让我们登录一个已有账号来查看完整功能" |
| 0:30 | `/login` | 输入Demo账号登录 | 输入: `demo@doxmind.com` / `DemoRadar2024!` |

> **使用预设Demo账号，跳过注册流程，节省时间**

---

### 第二幕：Dashboard概览 (1分钟)

| 时间 | 页面 | 操作 | 旁白要点 |
|------|------|------|----------|
| 0:40 | `/dashboard` | 展示整体界面 | "这是你的个人仪表板" |
| 0:50 | `/dashboard` | 指向统计卡片 | "顶部显示匹配总数、进行中的机会、已赢得的机会" |
| 1:05 | `/dashboard` | 指向Top Matches | "这里是匹配度最高的机会，绿色表示高匹配度" |
| 1:20 | `/dashboard` | 指向Pipeline Overview | "Pipeline显示你的机会追踪进度" |
| 1:30 | `/dashboard` | 点击Quick Action | "快速操作可以直接跳转到各个功能" |

---

### 第三幕：发现与筛选机会 (2分钟)

| 时间 | 页面 | 操作 | 旁白要点 |
|------|------|------|----------|
| 1:40 | `/opportunities` | 展示机会列表 | "Opportunities页面显示所有为你匹配的机会" |
| 1:55 | `/opportunities` | 使用类型过滤器 | "可以按类型筛选：Hackathon、Grant、Bounty、加速器等" |
| 2:10 | `/opportunities` | 选择Hackathon | "比如只看Hackathon类型的机会" |
| 2:25 | `/opportunities` | 悬停在卡片上 | "悬停可以快速收藏、忽略或添加到Pipeline" |
| 2:40 | `/opportunities` | 点击一个高匹配度的机会 | "让我们看看这个89%匹配度的机会" |
| 2:50 | `/opportunities/[id]` | 展示详情页顶部 | "详情页显示完整的机会信息" |
| 3:05 | 详情页 | **重点展示匹配分析卡片** | "这是AI的四维度匹配分析" |
| 3:15 | 详情页 | 逐个解释四个维度 | "相关性、资格审查、时间表、团队适配" |
| 3:30 | 详情页 | 展示改进建议 | "AI还会给出如何提高匹配度的建议" |
| 3:40 | 详情页 | 点击"Add to Pipeline" | "把这个机会加入我们的追踪Pipeline" |

---

### 第四幕：Pipeline管理 (1分钟)

| 时间 | 页面 | 操作 | 旁白要点 |
|------|------|------|----------|
| 3:50 | `/pipeline` | 展示Kanban看板 | "Pipeline是一个Kanban风格的看板" |
| 4:00 | `/pipeline` | 介绍6个阶段 | "从发现、准备、提交、待审、到最终的赢得或失败" |
| 4:15 | `/pipeline` | **拖拽卡片演示** | "拖拽卡片就可以更新状态" |
| 4:25 | `/pipeline` | 将卡片从Discovered拖到Preparing | "比如开始准备这个机会" |
| 4:35 | `/pipeline` | 右键点击卡片 | "右键可以快速生成材料或标记状态" |

---

### 第五幕：AI材料生成 (2分钟) ⭐核心功能

| 时间 | 页面 | 操作 | 旁白要点 |
|------|------|------|----------|
| 4:50 | `/generator` | 进入AI Generator | "现在来看最强大的功能：AI材料生成器" |
| 5:00 | `/generator` | 展示材料类型选项 | "支持生成README、演讲稿、Demo脚本、Q&A准备" |
| 5:15 | `/generator` | 选择"3分钟演讲稿" | "让我们为DoxMind生成一个3分钟的演讲稿" |
| 5:25 | `/generator` | 填写项目信息 | "输入项目名称和核心信息" |
| 5:35 | `/generator` | 项目名: DoxMind | - |
| 5:40 | `/generator` | 问题: 开发者花费大量时间阅读和理解文档 | - |
| 5:50 | `/generator` | 解决方案: AI驱动的文档问答和摘要工具 | - |
| 6:00 | `/generator` | 技术栈: Next.js, Python, LLM, RAG | - |
| 6:10 | `/generator` | **点击生成按钮** | "点击生成，AI开始工作" |
| 6:15 | `/generator` | 展示生成动画 | "几秒钟后..." |
| 6:30 | `/generator` | **展示生成结果** | "一份专业的3分钟演讲稿就生成好了" |
| 6:45 | `/generator` | 滚动查看内容 | "包含开场白、问题陈述、解决方案、技术亮点、结尾" |
| 7:00 | `/generator` | 点击复制按钮 | "一键复制到剪贴板，直接使用" |

---

### 第六幕：收尾 (30秒)

| 时间 | 页面 | 操作 | 旁白要点 |
|------|------|------|----------|
| 7:10 | `/materials` | 展示材料库 | "所有生成的材料都保存在材料库中" |
| 7:20 | `/profile` | 快速展示Profile | "随时可以更新个人资料以获得更精准的匹配" |
| 7:30 | `/dashboard` | 回到Dashboard | "这就是OpportunityRadar" |
| 7:40 | - | 结束画面 | "让AI帮你发现机会，赢得比赛" |

---

## 关键演示点 Checklist

### 必须展示的功能
- [x] **Dashboard统计概览** - 展示匹配数、进度
- [x] **四维度匹配分析** - 机会详情页
- [x] **拖拽Pipeline** - Kanban看板
- [x] **AI材料生成** - 生成演讲稿

### 可选展示的功能（如有额外时间）
- [ ] URL智能提取 (Onboarding) - 可单独录制
- [ ] OAuth登录 (GitHub/Google)
- [ ] 搜索功能
- [ ] 日历集成
- [ ] 社区提交

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
- [ ] 导出为MP4格式
- [ ] 上传到YouTube/视频平台

---

## 备注

- 如遇到加载缓慢，可以提前预热页面
- 准备备用方案：如果AI提取失败，手动填写信息继续
- 录制多个版本，选择最流畅的一个
