# OpportunityRadar Demo Guide

> AI-powered hackathon opportunity matching and material generation platform

---

## Overview

OpportunityRadar helps developers and teams discover the best hackathons, grants, bounties, and competitions matched to their skills and goals. With AI-powered matching and material generation, users can find opportunities and prepare winning submissions efficiently.

**Key Features:**
- Smart opportunity matching with 4-dimensional scoring
- Kanban-style pipeline management
- AI-powered material generation (README, Pitch, Demo Script, Q&A Prep)
- Profile-based recommendations
- Calendar integration for deadlines

---

## Demo Flow

### 1. Landing Page

![Landing Page](screenshots/01_landing_page.png)

The landing page showcases OpportunityRadar's value proposition:
- **"Discover Your Perfect Hackathon"** - Hero section with clear CTA
- **Smart Matching** - AI analyzes your profile for best matches
- **AI Materials** - Generate README, pitch scripts, and demo guides
- **Track Progress** - Kanban-style pipeline management

**Actions:** Click "Start Free" or "Get Started" to begin signup.

---

### 2. Signup Flow

![Signup Flow](gifs/01_signup_flow.gif)

Registration form with:
- Full Name
- Email
- Password & Confirm Password
- OAuth options (GitHub, Google)

**Features demonstrated:**
- Clean split-screen design
- Feature highlights on the right side
- Easy social login options

---

### 3. Onboarding Flow

![Onboarding Flow](gifs/02_onboarding_flow.gif)

3-step onboarding process:
1. **Profile Type** - Select your role (Developer, Student, etc.)
2. **URL Extraction** - AI extracts skills from your portfolio/GitHub
3. **Goals & Availability** - Set your preferences

---

### 4. Dashboard

![Dashboard](gifs/03_dashboard_overview.gif)

The personalized command center includes:

| Component | Description |
|-----------|-------------|
| **Profile Completion** | 7-dimension progress tracker (15% shown) |
| **AI Assistant** | Recommended next steps and smart suggestions |
| **Stats Cards** | Total Matches (100), In Pipeline (2), Preparing (1), Won (0) |
| **Top Matches** | High-scoring opportunities with match % |
| **Pipeline Overview** | Visual progress through stages |
| **Upcoming Deadlines** | Calendar view of important dates |

**Guided Tour:** 6-step onboarding tour explains each section.

---

### 5. Opportunities Page

![Opportunities Search & Filter](gifs/04_opportunities_search_filter.gif)

Browse and filter matched opportunities:

**Search & Filters:**
- Debounced search (300ms) with pulse animation
- Status filter: All Matches, Bookmarked, Dismissed
- Type filter: Hackathons, Grants, Bounties, Accelerators, Competitions

**Opportunity Cards:**
- Match score badge (84%, 83%, etc.)
- Type badge (hackathon, bug-bounty)
- Prize pool information
- Eligibility status indicator
- "Quick Prep" button for instant material generation
- "Details" button for full information

---

### 6. Pipeline Management

![Pipeline Stage Transition](gifs/05_pipeline_stage_transition.gif)

Kanban-style opportunity tracking:

**Stages:**
1. **Discovered** - New matched opportunities
2. **Preparing** - Active preparation
3. **Submitted** - Applications sent
4. **Pending** - Awaiting results
5. **Won** - Successful outcomes

**Features:**
- Drag-and-drop cards between stages
- Quick move buttons on each card
- Context menu for more options
- Urgency indicators (color-coded borders)

---

### 7. AI Material Generator

![AI Generator](gifs/06_ai_generator_material.gif)

Generate winning hackathon materials with AI:

**Material Types:**
| Type | Description |
|------|-------------|
| README | Project documentation |
| 3-min Pitch | Elevator pitch script |
| Demo Script | Live demo guide |
| Q&A Prep | Judge question preparation |

**Form Fields:**
- Project Name (pre-filled from profile)
- Problem Statement
- Your Solution
- Tech Stack (pre-filled from profile)

**Badge:** "Pre-filled from profile" indicates auto-completion.

---

### 8. Profile Settings

![Profile](gifs/08_profile.gif)

Customize your matching profile:

**Sections:**
- **Profile Type:** Developer, Student, Startup, Designer, Researcher
- **Tech Stack:** 27+ technologies to select
- **Industries:** FinTech, HealthTech, EdTech, Climate, etc.
- **Goals:** Win Prizes, Learn New Skills, Network, Build Portfolio
- **Availability:** Hours per week, team size preference

---

### 9. Settings

![Settings](gifs/09_settings.gif)

Account and app settings:

| Section | Options |
|---------|---------|
| **Connected Accounts** | GitHub, Google OAuth |
| **Data Export** | JSON, CSV formats |
| **Calendar Subscription** | Subscribe to deadlines |
| **Guided Tours** | Replay/reset onboarding tours |

---

## Assets

All demo assets are organized in dedicated folders:

- **`gifs/`** - Animated GIF recordings of key interactions (embedded in sections above)
- **`screenshots/`** - Static PNG screenshots extracted from GIFs

---

## Technical Highlights

### Match Score Algorithm
- **Semantic Score:** RAG-based profile-to-opportunity matching
- **Rule Score:** Eligibility requirements checking
- **Time Score:** Deadline and availability alignment
- **Team Score:** Team size compatibility

### UI/UX Features
- Framer Motion animations throughout
- Debounced search with visual feedback
- Urgency color system (critical/urgent/warning/safe)
- Responsive design (mobile Pipeline uses stage selector)
- Toast notifications for all actions

### AI Integration
- Profile extraction from website URLs
- Material generation with customizable templates
- Smart suggestions based on pipeline state

---

## Demo Credentials

| Field | Value |
|-------|-------|
| Name | DoxMind Team |
| Email | demo@doxmind.com |
| Password | DemoRadar2024! |

---

## Quick Start

1. Visit `http://localhost:3000`
2. Click "Get Started" to sign up
3. Complete the 3-step onboarding
4. Explore your personalized Dashboard
5. Browse matched Opportunities
6. Add opportunities to your Pipeline
7. Generate AI materials for your submissions

---

## Demo Session Summary

**Recorded:** January 7, 2026

### What Was Demonstrated

| Section | Feature | GIF |
|---------|---------|-----|
| 1 | Landing Page | Screenshot |
| 2 | Signup Flow | `01_signup_flow.gif` |
| 3 | Onboarding | `02_onboarding_flow.gif` |
| 4 | Dashboard | `03_dashboard_overview.gif` |
| 5 | Opportunities | `04_opportunities_search_filter.gif` |
| 6 | Pipeline | `05_pipeline_stage_transition.gif` |
| 7 | AI Generator | `06_ai_generator_material.gif` |
| 8 | Profile | `08_profile.gif` |
| 9 | Settings | `09_settings.gif` |

### Key Highlights Captured

1. **AI-Powered Profile Extraction** - URL `https://doxmind.com` → 100% quality profile extraction
2. **Smart Matching** - 86%, 85%, 85% match scores for top opportunities
3. **4-Dimension Scoring** - Relevance 84%, Eligibility 100%, Timeline 2%, Team Fit 100%
4. **Profile Auto-Fill** - Tech Stack pre-populated in AI Generator
5. **Real AI Generation** - DoxMind README generated with RAG technology description

### Demo Account Created

- **Team:** DoxMind Team
- **Email:** demo@doxmind.com
- **Profile Tech Stack:** TipTap, Vue 3, Tauri, JavaScript/TypeScript, Rust, AI/ML

---

*Generated with OpportunityRadar Demo Recording Tool*
