# 001: Match.batch_id Field Missing in MongoDB Model

## Metadata
- **Status**: resolved
- **Priority**: P2 (Important)
- **Issue ID**: 001
- **Tags**: code-review, architecture, data-integrity
- **Dependencies**: None

## Problem Statement

The `/matches/by-batch/{batch_id}` endpoint queries `Match.batch_id`, but this field does not exist in the MongoDB Match model. This causes the endpoint to always return `None`, breaking the opportunity detail view's ability to load match data for bookmark/dismiss functionality.

### Why It Matters

Users cannot bookmark or dismiss opportunities from the detail view because the match data is never loaded. This is a core user flow that is completely broken.

## Findings

### Evidence

1. **matches.py:101-112** - The endpoint queries for `Match.batch_id`:
   ```python
   @router.get("/by-batch/{batch_id}")
   async def get_match_by_batch(
       batch_id: str,
       current_user: User = Depends(get_current_user),
   ):
       try:
           match = await Match.find_one(
               Match.user_id == current_user.id,
               Match.batch_id == PydanticObjectId(batch_id),  # Field doesn't exist!
           )
   ```

2. **models/match.py:10-20** - The Match model has `opportunity_id` but no `batch_id`:
   ```python
   class Match(Document):
       user_id: Indexed(PydanticObjectId)
       opportunity_id: Indexed(PydanticObjectId)  # This is the actual field
       overall_score: float = 0.0
       # ... no batch_id field
   ```

3. **opportunities/[id]/page.tsx:48** - Frontend expects `getMatchByBatch` to work

### Affected Files

- `src/opportunity_radar/api/v1/endpoints/matches.py:101-112`
- `src/opportunity_radar/models/match.py`
- `frontend/app/(dashboard)/opportunities/[id]/page.tsx`
- `frontend/services/api-client.ts:118-121`

## Proposed Solutions

### Option A: Change endpoint to use opportunity_id (Recommended)

**Pros**:
- Minimal changes
- Aligns with actual data model
- No migration needed

**Cons**:
- Requires frontend changes to use correct field name

**Effort**: Small
**Risk**: Low

```python
@router.get("/by-opportunity/{opportunity_id}")
async def get_match_by_opportunity(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
):
    match = await Match.find_one(
        Match.user_id == current_user.id,
        Match.opportunity_id == PydanticObjectId(opportunity_id),
    )
    return match
```

### Option B: Add batch_id alias field

**Pros**:
- Maintains backward compatibility

**Cons**:
- Adds confusion with duplicate IDs
- Requires migration

**Effort**: Medium
**Risk**: Medium

## Recommended Action

(To be filled during triage)

## Technical Details

### Affected Components
- Backend: matches.py endpoint
- Frontend: api-client.ts, opportunity detail page

### Database Changes
None required if using Option A

## Acceptance Criteria

- [ ] `/matches/by-opportunity/{id}` returns the correct match data
- [ ] Opportunity detail page loads match status correctly
- [ ] Bookmark/dismiss buttons work from detail view
- [ ] Frontend uses consistent ID field name

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |

## Resources

- PR: feat/onboarding-tutorial-flow
- File: src/opportunity_radar/api/v1/endpoints/matches.py:101-112
