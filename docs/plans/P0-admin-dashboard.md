# P0: Admin Dashboard

> **Priority**: P0 (Blocking)
> **Status**: `NOT_STARTED`
> **Progress**: 0%
> **Last Updated**: 2026-01-03

---

## Overview

Build an admin dashboard to manage opportunity data, monitor crawler health, and perform manual data operations.

---

## Why This Matters

- **Data Quality**: Crawlers may miss or misparse data, need manual correction
- **Operations**: Monitor system health and crawler status
- **Bootstrap**: Manually add opportunities before crawlers are complete

---

## Core Features

### 1. Opportunity Management

- List all opportunities with search/filter
- Create new opportunity manually
- Edit existing opportunity
- Delete/archive opportunity
- Bulk import via CSV/JSON
- Bulk actions (activate, deactivate, delete)

### 2. Crawler Management

- View crawler status (last run, success/fail)
- Manually trigger crawler run
- View crawl history/batches
- See errors and failures

### 3. User Management (Basic)

- List all users
- View user details
- Disable/enable accounts

### 4. Analytics (Basic)

- Total opportunities by category
- Total users
- Match statistics
- Pipeline statistics

---

## Technical Approach

### Option A: Separate Admin App

```
/admin (Next.js separate app)
├── /login
├── /opportunities
├── /crawlers
├── /users
└── /analytics
```

**Pros**: Clean separation, different auth
**Cons**: More code to maintain

### Option B: Protected Routes in Main App

```
/app/(admin)/
├── admin/
│   ├── opportunities/
│   ├── crawlers/
│   ├── users/
│   └── analytics/
```

**Pros**: Shared components, single deploy
**Cons**: Need role-based auth

### Recommendation: Option B

Use protected routes with admin role check. Simpler to maintain.

---

## Backend Requirements

### New API Endpoints

```python
# Opportunities Admin
GET    /api/v1/admin/opportunities          # List with pagination
POST   /api/v1/admin/opportunities          # Create
PUT    /api/v1/admin/opportunities/{id}     # Update
DELETE /api/v1/admin/opportunities/{id}     # Delete
POST   /api/v1/admin/opportunities/import   # Bulk import

# Crawlers Admin
GET    /api/v1/admin/crawlers               # List crawlers
POST   /api/v1/admin/crawlers/{name}/run    # Trigger run
GET    /api/v1/admin/crawlers/batches       # List batches
GET    /api/v1/admin/crawlers/batches/{id}  # Batch details

# Users Admin
GET    /api/v1/admin/users                  # List users
GET    /api/v1/admin/users/{id}             # User details
PATCH  /api/v1/admin/users/{id}             # Update user

# Analytics
GET    /api/v1/admin/analytics/overview     # Dashboard stats
```

### Auth: Admin Role

```python
class User(Document):
    # ... existing fields
    role: Literal["user", "admin"] = "user"

def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
```

---

## UI Components

### Opportunities Table

| Column | Type |
|--------|------|
| Title | Link to edit |
| Category | Badge |
| Source | Text |
| Deadline | Date |
| Prize | Text |
| Status | Toggle |
| Actions | Edit/Delete |

### Filters

- Category (multi-select)
- Source (multi-select)
- Status (active/inactive)
- Date range (deadline)
- Search (title, description)

### Forms

- Opportunity create/edit form
- Bulk import modal (CSV upload)
- User edit modal

---

## Implementation Tasks

### Phase 1: Backend

- [ ] Add `role` field to User model
- [ ] Create admin middleware/dependency
- [ ] Implement admin opportunity CRUD endpoints
- [ ] Implement bulk import endpoint
- [ ] Add admin analytics endpoint

### Phase 2: Frontend - Layout

- [ ] Create admin layout with sidebar
- [ ] Add admin route protection
- [ ] Create admin navigation

### Phase 3: Frontend - Opportunities

- [ ] Opportunities list page with table
- [ ] Search and filter UI
- [ ] Create/edit opportunity form
- [ ] Bulk import modal
- [ ] Bulk actions

### Phase 4: Frontend - Other

- [ ] Crawler status page
- [ ] Users list page
- [ ] Analytics dashboard

---

## Page Designs

### Admin Dashboard (`/admin`)

```
┌──────────────────────────────────────────────────────┐
│  OpportunityRadar Admin                    [Logout]  │
├────────────┬─────────────────────────────────────────┤
│            │                                         │
│ Dashboard  │   Overview                              │
│ ---------- │   ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│ Opportun.. │   │  1,234  │ │   567   │ │    89   │  │
│ Crawlers   │   │ Opport. │ │  Users  │ │ Matches │  │
│ Users      │   └─────────┘ └─────────┘ └─────────┘  │
│ Analytics  │                                         │
│            │   Recent Activity                       │
│            │   • Devpost crawler ran (2h ago)        │
│            │   • 12 new opportunities added          │
│            │   • 5 new users signed up               │
│            │                                         │
└────────────┴─────────────────────────────────────────┘
```

### Opportunities List (`/admin/opportunities`)

```
┌──────────────────────────────────────────────────────┐
│  Opportunities                    [+ Add] [Import]   │
├──────────────────────────────────────────────────────┤
│  Search: [_______________]  Category: [All ▼]        │
│  Status: [All ▼]            Source: [All ▼]          │
├──────────────────────────────────────────────────────┤
│  □ Title              Category   Deadline   Actions  │
│  ─────────────────────────────────────────────────── │
│  □ ETH Denver 2026    Hackathon  Feb 28     [✎][🗑] │
│  □ Gitcoin GG21       Grant      Mar 15     [✎][🗑] │
│  □ YC W26 Batch       Accelerat  Jan 10     [✎][🗑] │
│  ...                                                 │
├──────────────────────────────────────────────────────┤
│  Showing 1-20 of 1,234          [<] 1 2 3 ... 62 [>] │
└──────────────────────────────────────────────────────┘
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Admin can add opportunity | < 2 min |
| Bulk import 100 records | < 30 sec |
| Find and edit opportunity | < 30 sec |

---

## Dependencies

- P0: Opportunity Crawler (for crawler management UI)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial plan created |
