# 007: Match Status Doesn't Detect In-Progress Recalculation

## Metadata
- **Status**: pending
- **Priority**: P3 (Nice-to-have)
- **Issue ID**: 007
- **Tags**: code-review, ux, improvement
- **Dependencies**: None

## Problem Statement

The `/matches/status` endpoint reports "ready" whenever any match exists. Clients cannot detect when a recalculation is in progress, leading to stale UI states.

### Why It Matters

After profile update, users may see old matches instead of a loading state while new matches are being computed.

## Findings

### Evidence

**matches.py:146-178** - Status logic:
```python
@router.get("/status")
async def get_match_status(...):
    total_count = await Match.find(Match.user_id == current_user.id).count()

    if total_count > 0:
        status_value = "ready"  # Always "ready" if any matches exist!
    elif has_embedding:
        status_value = "calculating"
    else:
        status_value = "no_profile"
```

### Affected Files

- `src/opportunity_radar/api/v1/endpoints/matches.py:146-178`

## Proposed Solutions

### Option A: Add computation timestamp to Profile

Track `last_match_computation` and `last_profile_update` timestamps. Status is "calculating" if profile updated more recently than computation.

**Effort**: Medium
**Risk**: Low

### Option B: Use Redis flag for in-progress computation

Set a flag when computation starts, clear when done.

**Effort**: Small
**Risk**: Low

## Acceptance Criteria

- [ ] Status returns "calculating" during recomputation
- [ ] Frontend shows loading state appropriately

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |
