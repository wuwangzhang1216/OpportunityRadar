# P1: Team Profile Enhancement

> **Priority**: P1 (Core Experience)
> **Status**: `NOT_STARTED`
> **Progress**: 0%
> **Last Updated**: 2026-01-03

---

## Overview

Enhance the user profile system to better support startup teams, enabling more accurate opportunity matching.

---

## Why This Matters

- **Target Users**: Primary users are startup teams, not just individual developers
- **Better Matching**: Team context improves recommendation accuracy
- **User Value**: Teams can showcase their full capabilities

---

## Current State

The existing profile model supports:
- Individual skills/tech stack
- Industries of interest
- Personal goals
- Weekly availability

**Missing for Teams**:
- Team composition
- Company/product info
- Funding stage
- Team member roles

---

## Proposed Enhancements

### New Profile Fields

```python
class Profile(Document):
    # Existing fields...

    # NEW: Team/Company Info
    team_name: str | None                    # "Acme Labs"
    team_size: int | None                    # Number of members
    company_stage: Literal[
        "idea",
        "prototype",
        "mvp",
        "launched",
        "revenue",
        "funded"
    ] | None

    # NEW: Funding Info
    funding_stage: Literal[
        "bootstrapped",
        "pre_seed",
        "seed",
        "series_a",
        "series_b_plus"
    ] | None
    seeking_funding: bool = False
    funding_amount_seeking: str | None       # "$500K - $1M"

    # NEW: Product Info
    product_name: str | None
    product_description: str | None
    product_url: str | None
    product_stage: Literal[
        "concept",
        "development",
        "beta",
        "live"
    ] | None

    # NEW: Team Members (simplified)
    team_members: list[TeamMember] = []

    # NEW: Previous Experience
    previous_accelerators: list[str] = []    # ["YC", "Techstars"]
    previous_hackathon_wins: int = 0
    notable_achievements: list[str] = []

class TeamMember:
    name: str
    role: str                                # "CEO", "CTO", "Engineer"
    linkedin_url: str | None
    skills: list[str]
```

---

## UI Changes

### Profile Page Sections

```
1. Personal Info (existing)
   - Name, email, avatar

2. Team Info (NEW)
   - Team/Company name
   - Team size
   - Company stage
   - Team members list

3. Product Info (NEW)
   - Product name & description
   - Product URL
   - Product stage

4. Funding (NEW)
   - Current funding stage
   - Seeking funding?
   - Amount seeking

5. Skills & Interests (enhanced)
   - Tech stack
   - Industries
   - Goals

6. Track Record (NEW)
   - Previous accelerators
   - Hackathon wins
   - Notable achievements

7. Availability (existing)
   - Hours per week
   - Team preference
   - Location
```

### Onboarding Updates

Update onboarding to collect team info:

**Step 2 (Confirm Data)** - Add sections:
- Team/Company info
- Product info
- Funding stage

---

## Implementation Tasks

### Phase 1: Backend

- [ ] Update Profile model with new fields
- [ ] Create TeamMember embedded model
- [ ] Update profile API schemas
- [ ] Migrate existing profiles (add nullable fields)
- [ ] Update onboarding extract logic

### Phase 2: Frontend - Profile Page

- [ ] Add Team Info section
- [ ] Add Product Info section
- [ ] Add Funding section
- [ ] Add Track Record section
- [ ] Add team member management UI

### Phase 3: Onboarding Updates

- [ ] Update Step 2 form with team fields
- [ ] Update extract logic to parse team info
- [ ] Test full onboarding flow

### Phase 4: Matching Integration

- [ ] Update matching algorithm to use new fields
- [ ] Weight team size for team-required opportunities
- [ ] Factor funding stage for accelerators

---

## Matching Algorithm Impact

New fields enable better matching:

| Field | Matching Use |
|-------|--------------|
| `team_size` | Filter opportunities requiring specific team sizes |
| `company_stage` | Match accelerators for right stage |
| `funding_stage` | Filter grants for eligible stages |
| `product_stage` | Match opportunities needing working product |
| `previous_accelerators` | Avoid recommending completed programs |
| `hackathon_wins` | Boost confidence for competitive events |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Profile completion rate | > 60% |
| Team info filled | > 40% of users |
| Match relevance score | +15% improvement |

---

## Dependencies

- None (can start immediately)
- Blocks: P1-matching-algorithm (needs these fields)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial plan created |
