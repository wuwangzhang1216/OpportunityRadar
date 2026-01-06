# OpportunityRadar 系统架构文档

> 最后更新: 2026-01-07

## 目录

- [整体架构](#整体架构)
- [核心数据模型](#核心数据模型)
- [工作流程](#工作流程)
- [API 端点](#api-端点)
- [技术栈](#技术栈)
- [目录结构](#目录结构)

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js :3000)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Auth Pages │  │  Onboarding  │  │  Dashboard   │  │   Generator  │    │
│  │  login/signup│  │   3-step     │  │ opportunities│  │  materials   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│  ┌──────┴─────────────────┴─────────────────┴─────────────────┴──────┐     │
│  │                     Zustand Stores                                 │     │
│  │  ┌─────────────┐  ┌─────────────────┐  ┌─────────────┐            │     │
│  │  │ auth-store  │  │ onboarding-store│  │ tour-store  │            │     │
│  │  └─────────────┘  └─────────────────┘  └─────────────┘            │     │
│  └────────────────────────────┬──────────────────────────────────────┘     │
│                               │                                            │
│  ┌────────────────────────────┴──────────────────────────────────────┐     │
│  │                      API Client (Axios)                            │     │
│  │              Authorization: Bearer {access_token}                  │     │
│  └────────────────────────────┬──────────────────────────────────────┘     │
└───────────────────────────────┼──────────────────────────────────────────┘
                                │ HTTP/REST
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND (FastAPI :8001)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API Layer (/api/v1/)                         │   │
│  ├─────────┬──────────┬──────────┬─────────┬──────────┬────────────────┤   │
│  │  auth   │onboarding│ profiles │ matches │materials │   pipelines    │   │
│  └────┬────┴────┬─────┴────┬─────┴────┬────┴────┬─────┴───────┬────────┘   │
│       │         │          │          │         │             │            │
│  ┌────┴─────────┴──────────┴──────────┴─────────┴─────────────┴────────┐   │
│  │                        Services Layer                                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ ┌─────────────┐ ┌──────────────────┐ ┌───────────────────────────┐  │   │
│  │ │ AuthService │ │OnboardingService │ │  MongoMatchingService     │  │   │
│  │ └─────────────┘ └──────────────────┘ └───────────────────────────┘  │   │
│  │ ┌─────────────┐ ┌──────────────────┐ ┌───────────────────────────┐  │   │
│  │ │EmbeddingServ│ │ MaterialGenerator│ │  ProfileService           │  │   │
│  │ │  (OpenAI)   │ │     (OpenAI)     │ │  PipelineService          │  │   │
│  │ └─────────────┘ └──────────────────┘ └───────────────────────────┘  │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────┴───────────────────────────────────────┐   │
│  │                      Models (Beanie ODM)                             │   │
│  │  User │ Profile │ Opportunity │ Match │ Pipeline │ Material │ Host  │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │ Motor (async)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MongoDB (:27017)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  users │ profiles │ opportunities │ matches │ pipelines │ materials │ hosts│
│                                                                             │
│  profiles.embedding (vector 1536)    opportunities.embedding (vector 1536) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 核心数据模型

### 模型关系图

```
┌──────────┐       1:1        ┌───────────┐
│   User   │─────────────────▶│  Profile  │
│          │                  │           │
│ • email  │                  │• tech_stack│
│ • password                  │• interests │
│ • oauth  │                  │• goals     │
└────┬─────┘                  │• embedding │
     │                        └─────┬─────┘
     │                              │
     │ 1:N                          │ computed
     ▼                              ▼
┌──────────┐                  ┌───────────┐
│  Match   │◀─────────────────│Opportunity│
│          │      N:1         │           │
│• score   │                  │• title    │
│• semantic│                  │• themes   │
│• bookmark│                  │• tech     │
│• dismiss │                  │• embedding│
└────┬─────┘                  └───────────┘
     │
     │ optional
     ▼
┌──────────┐                  ┌───────────┐
│ Pipeline │──────────────────│ Material  │
│          │      1:N         │           │
│• status  │                  │• type     │
│• notes   │                  │• content  │
└──────────┘                  └───────────┘
```

### User 模型

```python
class User(Document):
    email: str                    # 唯一索引
    hashed_password: str | None   # OAuth 用户可为空
    full_name: str | None
    avatar_url: str | None
    is_active: bool = True
    is_superuser: bool = False
    oauth_connections: list       # [{provider, provider_id, access_token}]
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
```

### Profile 模型

```python
class Profile(Document):
    user_id: PydanticObjectId     # 关联 User
    display_name: str | None
    bio: str | None
    tech_stack: list[str]         # ["Python", "React", "AWS"]
    interests: list[str]          # ["FinTech", "AI/ML"]
    goals: list[str]              # ["funding", "learning", "networking"]
    experience_level: str | None
    team_size: int | None
    company_stage: str | None     # idea, prototype, mvp, launched
    funding_stage: str | None     # bootstrapped, pre_seed, seed
    embedding: list[float] | None # 1536 维向量 (OpenAI text-embedding-3-small)
    created_at: datetime
    updated_at: datetime
    last_match_computation: datetime | None
```

### Opportunity 模型

```python
class Opportunity(Document):
    title: str
    description: str
    opportunity_type: str         # hackathon, grant, competition, accelerator
    format: str                   # online, in-person, hybrid
    themes: list[str]             # ["AI/ML", "Web3", "FinTech"]
    technologies: list[str]       # ["Python", "TensorFlow"]
    total_prize_value: float | None
    team_size_min: int | None
    team_size_max: int | None
    application_deadline: datetime | None
    event_start_date: datetime | None
    is_active: bool = True
    embedding: list[float] | None # 1536 维向量
    created_at: datetime
    updated_at: datetime
```

### Match 模型

```python
class Match(Document):
    user_id: PydanticObjectId
    opportunity_id: PydanticObjectId
    overall_score: float          # 最终分数 (0-1)
    semantic_score: float | None  # 语义相似度分数
    rule_score: float | None      # (已弃用)
    time_score: float | None      # recency boost
    team_score: float | None      # 团队匹配度
    score_breakdown: dict         # 详细分数分解
    eligibility_status: str       # eligible, ineligible
    eligibility_issues: list[str]
    is_bookmarked: bool = False
    is_dismissed: bool = False
    created_at: datetime
    updated_at: datetime
```

### Pipeline 模型

```python
class Pipeline(Document):
    user_id: PydanticObjectId
    opportunity_id: PydanticObjectId
    match_id: PydanticObjectId | None
    status: str                   # interested, preparing, submitted, won, lost
    notes: str | None
    team_members: list[str]
    project_idea: str | None
    submission_url: str | None
    created_at: datetime
    updated_at: datetime
```

### Material 模型

```python
class Material(Document):
    user_id: PydanticObjectId
    opportunity_id: PydanticObjectId | None
    pipeline_id: PydanticObjectId | None
    material_type: str            # readme, pitch_3min, demo_script, qa_pred
    title: str
    content: str                  # 生成的内容
    metadata: dict
    prompt_used: str | None
    model_used: str | None
    is_favorite: bool = False
    created_at: datetime
    updated_at: datetime
```

---

## 工作流程

### 1. 用户注册 & Onboarding 流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ONBOARDING WORKFLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐         ┌──────────────┐         ┌─────────────┐
     │  Signup  │         │   Extract    │         │   Confirm   │
     │  /Login  │────────▶│   Profile    │────────▶│   Profile   │
     │          │         │   from URL   │         │             │
     └──────────┘         └──────────────┘         └──────┬──────┘
          │                     │                         │
          ▼                     ▼                         ▼
    ┌───────────┐        ┌────────────┐           ┌─────────────┐
    │Create User│        │ AI Parses  │           │Create/Update│
    │  + JWT    │        │GitHub/Site │           │   Profile   │
    └───────────┘        │ extracts:  │           │             │
                         │ • tech     │           │ Generate    │
                         │ • bio      │           │ Embedding   │──────┐
                         │ • name     │           └─────────────┘      │
                         └────────────┘                                │
                                                           ┌───────────▼───────┐
                                                           │  Background Task  │
                                                           │  compute_matches  │
                                                           │  for 500+ opps    │
                                                           └─────────┬─────────┘
                                                                     │
                                                                     ▼
                                                           ┌─────────────────┐
                                                           │   Redirect to   │
                                                           │   Dashboard     │
                                                           └─────────────────┘
```

**详细步骤:**

1. 用户通过 Email 或 OAuth (GitHub/Google) 注册
2. Frontend 存储 JWT token (access 30min + refresh 7d)
3. 重定向到 onboarding 页面
4. **Step 1**: 用户输入 GitHub/website URL
5. Backend 通过 AI 解析提取 profile 数据
6. **Step 2**: 用户确认/编辑提取的数据
7. Backend 创建 Profile 并生成 embedding
8. Background task 计算 matches
9. 重定向到 dashboard

### 2. 匹配计算流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MATCHING WORKFLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  Profile                                              Opportunity
┌──────────────┐                                    ┌──────────────┐
│ tech_stack   │                                    │ technologies │
│ interests    │                                    │ themes       │
│ goals        │                                    │ description  │
│ bio          │                                    │ prizes       │
└──────┬───────┘                                    └──────┬───────┘
       │                                                   │
       │  create_embedding_text()                          │
       ▼                                                   ▼
┌──────────────┐                                    ┌──────────────┐
│   Profile    │                                    │ Opportunity  │
│   Embedding  │                                    │  Embedding   │
│  (1536 dim)  │                                    │  (1536 dim)  │
└──────┬───────┘                                    └──────┬───────┘
       │                                                   │
       └───────────────────┬───────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │     Cosine Similarity       │
              │    + Score Stretching       │
              │   [0.25-0.55] → [0.50-0.95] │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │     MatchScoreBreakdown     │
              │  ┌─────────────────────┐    │
              │  │ semantic_score      │    │  ← Primary (余弦相似度)
              │  │ recency_boost       │    │  ← +2% if < 1 week
              │  │ popularity_boost    │    │  ← +1% if > 100 participants
              │  │ team_size_eligible  │    │  ← Hard filter
              │  │ location_eligible   │    │  ← Hard filter
              │  └─────────────────────┘    │
              │                             │
              │  total_score = semantic     │
              │              + min(5%, boosts)│
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │     Save to Match           │
              │  overall_score = 0.944      │
              │  semantic_score = 0.92      │
              │  eligibility = "eligible"   │
              └─────────────────────────────┘
```

**MatchScoreBreakdown 字段说明:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `semantic_score` | float | 主要分数 - 余弦相似度 (0-1) |
| `recency_boost` | float | 新鲜度加成 (≤7天 +2%, ≤14天 +1%) |
| `popularity_boost` | float | 热门度加成 (>100人 +1%) |
| `team_size_eligible` | bool | 团队大小是否符合 |
| `funding_stage_eligible` | bool | 融资阶段是否符合 |
| `location_eligible` | bool | 地区是否符合 |
| `is_eligible` | property | 所有 hard filters 是否通过 |
| `total_score` | property | 最终分数 = semantic + min(5%, boosts) |

### 3. Material 生成流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MATERIAL GENERATION WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

         Frontend                         Backend                    OpenAI
            │                                │                          │
            │  POST /materials/generate      │                          │
            │  {                             │                          │
            │    project_name,               │                          │
            │    problem,                    │                          │
            │    solution,                   │                          │
            │    tech_stack,                 │                          │
            │    targets: ["readme",         │                          │
            │              "pitch_3min"]     │                          │
            │  }                             │                          │
            │──────────────────────────────▶│                          │
            │                               │  Jinja2 Template         │
            │                               │  + Context               │
            │                               │─────────────────────────▶│
            │                               │                          │
            │                               │◀─────────────────────────│
            │                               │  Generated Content       │
            │                               │                          │
            │                               │  Save to MongoDB         │
            │◀──────────────────────────────│                          │
            │  {id, type, content, ...}     │                          │
```

**支持的 Material 类型:**

| 类型 | 说明 |
|------|------|
| `readme` | 项目 README |
| `pitch_1min` | 1 分钟 pitch |
| `pitch_3min` | 3 分钟 pitch |
| `pitch_5min` | 5 分钟 pitch |
| `demo_script` | Demo 脚本 |
| `qa_pred` | 预测的 Q&A |
| `submission_text` | 提交文本 |
| `one_liner` | 一句话描述 |

### 4. Pipeline 管理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE WORKFLOW                                     │
└─────────────────────────────────────────────────────────────────────────────┘

    Discover           Interested         Preparing         Submitted         Result
       │                   │                  │                 │               │
       ▼                   ▼                  ▼                 ▼               ▼
  ┌─────────┐        ┌─────────┐        ┌─────────┐       ┌─────────┐    ┌─────────┐
  │  Match  │───────▶│ Pipeline│───────▶│ Pipeline│──────▶│ Pipeline│───▶│ Pipeline│
  │ created │  add   │ status: │  move  │ status: │ submit│ status: │    │ status: │
  │         │  to    │interested│  to   │preparing│       │submitted│    │ won/lost│
  └─────────┘ pipeline└─────────┘       └─────────┘       └─────────┘    └─────────┘
                          │                  │
                          │                  │
                          ▼                  ▼
                    ┌─────────────┐    ┌─────────────┐
                    │ Add Notes   │    │  Generate   │
                    │ Team Members│    │  Materials  │
                    └─────────────┘    └─────────────┘
```

**Pipeline 状态:**

| 状态 | 说明 |
|------|------|
| `interested` | 感兴趣，刚添加 |
| `preparing` | 准备中，在写材料 |
| `submitted` | 已提交 |
| `won` | 获奖 |
| `lost` | 未中选 |

---

## API 端点

### Authentication (`/api/v1/auth`)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/signup` | 注册新用户 |
| POST | `/login` | 登录 |
| POST | `/logout` | 登出 |
| GET | `/me` | 获取当前用户 |
| GET | `/oauth/{provider}/authorize` | 获取 OAuth URL |
| POST | `/oauth/{provider}/callback` | OAuth 回调 |

### Onboarding (`/api/v1/onboarding`)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/extract` | 从 URL 提取 profile |
| POST | `/confirm` | 确认 profile + 生成 embedding + 计算 matches |
| GET | `/status` | 检查 onboarding 状态 |
| GET | `/suggestions` | 获取建议列表 |

### Profiles (`/api/v1/profiles`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/me` | 获取当前用户的 profile |
| POST | `/` | 创建 profile |
| PUT | `/me` | 更新 profile (触发重新生成 embedding + 计算 matches) |

### Matches (`/api/v1/matches`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 获取 matches 列表 (分页) |
| GET | `/top` | 获取 top N matches |
| GET | `/stats` | 匹配统计 |
| GET | `/status` | 匹配计算状态 |
| POST | `/calculate` | 触发匹配计算 |
| POST | `/{match_id}/dismiss` | 忽略 match |
| POST | `/{match_id}/bookmark` | 收藏 match |
| POST | `/{match_id}/unbookmark` | 取消收藏 |
| POST | `/{match_id}/restore` | 恢复已忽略的 match |

### Materials (`/api/v1/materials`)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/generate` | 生成材料 |
| GET | `/` | 列出所有材料 |
| GET | `/{material_id}` | 获取特定材料 |
| DELETE | `/{material_id}` | 删除材料 |

### Pipelines (`/api/v1/pipelines`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 获取 pipeline 列表 |
| GET | `/stats` | Pipeline 统计 |
| GET | `/deadlines` | 即将到期的 deadlines |
| POST | `/` | 添加到 pipeline |
| PATCH | `/{pipeline_id}` | 更新 pipeline item |
| POST | `/{pipeline_id}/stage/{stage}` | 更新状态 |
| DELETE | `/{pipeline_id}` | 从 pipeline 移除 |

### Opportunities (`/api/v1/opportunities`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 列出 opportunities (带过滤) |
| GET | `/{id}` | 获取 opportunity 详情 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| **Frontend** | Next.js 14, React 18, TypeScript |
| **State Management** | Zustand (with persist) |
| **HTTP Client** | Axios |
| **UI Components** | Radix UI, Tailwind CSS |
| **Backend** | FastAPI, Python 3.12, async/await |
| **ODM** | Beanie (MongoDB ODM) |
| **Database Driver** | Motor (async MongoDB) |
| **Database** | MongoDB |
| **AI/Embeddings** | OpenAI (text-embedding-3-small, GPT-4) |
| **Auth** | JWT (PyJWT), OAuth 2.0 |
| **Web Scraping** | Playwright |
| **Validation** | Pydantic v2 |
| **Testing** | Pytest, pytest-asyncio |

---

## 目录结构

### Backend (`src/opportunity_radar/`)

```
src/opportunity_radar/
├── api/
│   └── v1/
│       ├── endpoints/           # API 路由处理器
│       │   ├── auth.py          # 认证端点
│       │   ├── onboarding.py    # Onboarding 端点
│       │   ├── profiles.py      # Profile 端点
│       │   ├── matches.py       # Match 端点
│       │   ├── materials.py     # Material 端点
│       │   ├── pipelines.py     # Pipeline 端点
│       │   └── opportunities.py # Opportunity 端点
│       └── router.py            # API 路由聚合
├── services/                    # 业务逻辑层
│   ├── auth_service.py          # 认证服务
│   ├── onboarding_service.py    # Onboarding 服务
│   ├── mongo_matching_service.py # 匹配服务 (主要)
│   ├── embedding_service.py     # Embedding 服务
│   ├── profile_service.py       # Profile 服务
│   └── pipeline_service.py      # Pipeline 服务
├── models/                      # Beanie ODM 文档
│   ├── user.py
│   ├── profile.py
│   ├── opportunity.py
│   ├── match.py
│   ├── pipeline.py
│   └── material.py
├── schemas/                     # Pydantic 请求/响应模型
├── matching/                    # 匹配引擎
│   ├── scorer.py                # 评分器 (legacy)
│   └── dsl_engine.py            # DSL 规则引擎
├── ai/                          # AI 生成
│   └── prompts/                 # Jinja2 模板
├── core/
│   └── security.py              # JWT 认证, 密码哈希
├── scrapers/                    # Web 爬虫
└── config.py                    # 配置管理
```

### Frontend (`frontend/`)

```
frontend/
├── app/
│   ├── (auth)/                  # 认证相关页面
│   │   ├── login/
│   │   ├── signup/
│   │   ├── onboarding/
│   │   └── oauth/callback/
│   ├── (dashboard)/             # Dashboard 页面
│   │   ├── dashboard/
│   │   ├── opportunities/
│   │   ├── matches/
│   │   ├── pipeline/
│   │   ├── materials/
│   │   ├── generator/
│   │   └── profile/
│   └── (admin)/                 # Admin 页面
├── stores/                      # Zustand stores
│   ├── auth-store.ts
│   ├── onboarding-store.ts
│   └── tour-store.ts
├── services/
│   └── api-client.ts            # Axios API 客户端
└── components/
    └── ui/                      # UI 组件
```

---

## 环境变量

### Backend (`.env`)

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=opportunity_radar

# OpenAI
OPENAI_API_KEY=sk-...

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth (可选)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## 端口

| 服务 | 端口 |
|------|------|
| Frontend (Next.js) | 3000 |
| Backend (FastAPI) | 8001 |
| MongoDB | 27017 |
| PostgreSQL (legacy) | 5432 |
| Redis | 6380 |

---

## 启动命令

### Backend

```bash
# 启动开发服务器
uvicorn src.opportunity_radar.main:app --reload --port 8001

# 运行测试
pytest

# 代码格式化
black src/ --line-length 100
ruff check src/
```

### Frontend

```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建
npm run build

# Lint
npm run lint
```

### Database

```bash
# 启动开发数据库
docker-compose -f docker-compose.dev.yml up -d

# 初始化数据库
python scripts/init_db.py

# 填充测试数据
python scripts/populate_opportunities.py
```
