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
- Delete/archive opportunity (soft delete via `is_active`)
- Bulk import via CSV/JSON
- Bulk actions (activate, deactivate, delete)

### 2. Crawler Management

- View crawler status (last run, success/fail)
- Manually trigger crawler run (async with job ID)
- View crawl history via ScraperRun model
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
GET    /api/v1/admin/opportunities              # List with pagination
POST   /api/v1/admin/opportunities              # Create
PATCH  /api/v1/admin/opportunities/{id}         # Partial update
DELETE /api/v1/admin/opportunities/{id}         # Soft delete (is_active=False)
DELETE /api/v1/admin/opportunities/{id}?hard=true  # Hard delete
POST   /api/v1/admin/opportunities/import       # Bulk import
POST   /api/v1/admin/opportunities/bulk-action  # Bulk actions

# Crawlers Admin
GET    /api/v1/admin/crawlers                   # List crawlers with status
POST   /api/v1/admin/crawlers/{name}/runs       # Trigger run (returns job_id)
GET    /api/v1/admin/crawlers/{name}/runs       # List run history
GET    /api/v1/admin/crawlers/{name}/runs/{id}  # Run details

# Users Admin
GET    /api/v1/admin/users                      # List users
GET    /api/v1/admin/users/{id}                 # User details
PATCH  /api/v1/admin/users/{id}                 # Update user

# Analytics
GET    /api/v1/admin/analytics/overview         # Dashboard stats
```

### Pagination Response Schema

All list endpoints return:
```python
{
    "items": [...],
    "total": 1234,
    "skip": 0,
    "limit": 20
}
```

### Auth: Use Existing `is_superuser` Field

**IMPORTANT**: The User model already has `is_superuser: bool = False` at `models/user.py:18`.
Do NOT add a separate `role` field - use the existing field.

```python
# src/opportunity_radar/api/v1/dependencies.py

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin (superuser) access."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
```

### Admin Bootstrap Script

Create `scripts/create_admin.py` for first admin user:

```python
#!/usr/bin/env python
"""Create or promote a user to admin."""
import asyncio
from src.opportunity_radar.models.user import User
from src.opportunity_radar.core.security import get_password_hash

async def create_admin(email: str, password: str = None):
    user = await User.find_one(User.email == email)
    if user:
        user.is_superuser = True
        await user.save()
        print(f"Promoted {email} to admin")
    else:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_superuser=True,
            is_active=True
        )
        await user.insert()
        print(f"Created admin user: {email}")

if __name__ == "__main__":
    import sys
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(create_admin(email, password))
```

### New Model: ScraperRun (MongoDB/Beanie)

The existing `Batch` model is legacy PostgreSQL. Create new Beanie model for crawler history:

```python
# src/opportunity_radar/models/scraper_run.py

class ScraperRun(Document):
    """Record of a scraper execution."""

    scraper_name: str
    status: Literal["pending", "running", "success", "partial", "failed"] = "pending"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    opportunities_found: int = 0
    opportunities_created: int = 0
    opportunities_updated: int = 0
    errors: List[str] = Field(default_factory=list)
    triggered_by: Optional[PydanticObjectId] = None  # Admin user ID if manual

    class Settings:
        name = "scraper_runs"
```

### Bulk Import Error Handling

```python
# POST /api/v1/admin/opportunities/import response
{
    "imported": 46,
    "failed": 4,
    "skipped": 3,  # duplicates
    "errors": [
        {"row": 12, "error": "Missing required field: title"},
        {"row": 47, "error": "Invalid date format for deadline"},
        ...
    ]
}
```

Behavior:
- Partial success is OK - import what we can
- Duplicates (by `external_id`) are skipped with warning
- Return detailed error report for failed rows

### Bulk Actions Endpoint

```python
# POST /api/v1/admin/opportunities/bulk-action
{
    "action": "activate" | "deactivate" | "delete",
    "ids": ["id1", "id2", ...]
}

# Response
{
    "affected": 5,
    "failed": 0
}
```

---

## Security Considerations

### Rate Limiting

Apply rate limits to expensive admin operations:

| Endpoint | Limit |
|----------|-------|
| Crawler trigger | 1 per scraper per 5 minutes |
| Bulk import | 1 per 30 seconds |
| Bulk actions | 1 per 10 seconds |

### Audit Logging

Log all admin actions for accountability:

```python
# Simple structured logging approach
logger.info("admin_action", extra={
    "action": "opportunity_deleted",
    "admin_id": str(user.id),
    "admin_email": user.email,
    "target_id": str(opportunity_id),
    "timestamp": datetime.utcnow().isoformat()
})
```

Consider dedicated `AdminAuditLog` model if compliance requires persistent audit trail.

### Token Invalidation for Disabled Users

When disabling a user, their JWT tokens remain valid until expiry (30min access, 7d refresh).

Options:
1. **Accept the risk**: Document that disabled users can access for up to 7 days
2. **Redis blacklist**: Add disabled user IDs to Redis, check on each request
3. **Shorter tokens**: Reduce refresh token lifetime for security-sensitive apps

Recommendation: Start with option 1, implement option 2 if needed.

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

- Search (title only for MVP)
- Category (single select dropdown)
- Status (active/inactive)

### Forms

- Opportunity create/edit form
- Bulk import modal (CSV upload)
- User edit modal

---

## Implementation Tasks

### Phase 1a: Auth Infrastructure

- [ ] Create `require_admin` dependency in `api/v1/dependencies.py`
- [ ] Create `scripts/create_admin.py` bootstrap script
- [ ] Test admin auth in isolation
- [ ] Document admin creation in README

### Phase 1b: Backend - Models & CRUD

- [ ] Create `ScraperRun` Beanie model for crawler history
- [ ] Create admin router at `api/v1/admin/router.py`
- [ ] Implement opportunity CRUD endpoints (direct Beanie queries, no repositories)
- [ ] Implement bulk import endpoint with error handling
- [ ] Implement bulk actions endpoint
- [ ] Add admin analytics endpoint (simple counts)

### Phase 1c: Backend - Crawlers

- [ ] Update scrapers to create ScraperRun records
- [ ] Implement crawler status endpoint
- [ ] Implement async crawler trigger (returns job_id)
- [ ] Implement run history endpoints

### Phase 2: Frontend - Layout

- [ ] Create admin layout with sidebar
- [ ] Add admin route protection (check `is_superuser`)
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
- [ ] Analytics dashboard (simple stat cards)

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

- P0: Opportunity Crawler (for crawler management UI in Phase 4)

---

## Review Feedback Incorporated

This plan was reviewed by three specialized reviewers on 2026-01-03:

| Reviewer | Key Feedback |
|----------|--------------|
| DHH | Use existing `is_superuser`, direct Beanie queries, no admin stores |
| Kieran | Add ScraperRun model, use PATCH not PUT, define async crawler pattern |
| Simplicity | Split Phase 1, defer complex features if needed |

Critical fixes applied:
- ✅ Use `is_superuser` instead of adding `role` field
- ✅ Create `ScraperRun` MongoDB model for crawler history
- ✅ Add admin bootstrap script
- ✅ Change PUT to PATCH for partial updates
- ✅ Add bulk actions endpoint
- ✅ Define async pattern for crawler triggers
- ✅ Add rate limiting and audit logging guidance
- ✅ Define bulk import error handling behavior
- ✅ Split Phase 1 into auth infrastructure and CRUD

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial plan created |
| 2026-01-03 | Updated with review feedback: is_superuser, ScraperRun model, bootstrap script, PATCH endpoints, security considerations |
