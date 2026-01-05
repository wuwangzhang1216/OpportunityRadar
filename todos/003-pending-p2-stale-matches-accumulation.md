# 003: Stale Matches Accumulation and Embedding Refresh

## Metadata
- **Status**: resolved
- **Priority**: P2 (Important)
- **Issue ID**: 003
- **Tags**: code-review, data-integrity, performance
- **Dependencies**: None

## Problem Statement

Match recomputation upserts new matches without deleting stale ones, and profile updates don't regenerate embeddings. This causes:
1. Outdated match records to accumulate in the database
2. Match scores calculated against stale profile embeddings

### Why It Matters

Users may see matches that no longer reflect their current profile, and the database grows unbounded with obsolete data.

## Findings

### Evidence

1. **mongo_matching_service.py:502-530** - `save_matches` upserts but doesn't clean up:
   ```python
   async def save_matches(
       self, user_id: str, matches: List[MatchResult]
   ) -> List[Match]:
       # Upserts matches, but never deletes old ones
       for result in matches:
           existing = await Match.find_one(...)
           if existing:
               # Update existing
           else:
               # Create new
   ```

2. **profiles.py:143-189** - Profile update triggers match recalculation but doesn't refresh embedding:
   ```python
   @router.put("/me", response_model=ProfileResponse)
   async def update_profile(...):
       # Updates profile fields
       # Triggers recalculate_matches_background
       # BUT: No embedding regeneration!
   ```

3. **mongo_matching_service.py:261-265** - Matching relies on embeddings:
   ```python
   if profile.embedding and opportunity.embedding:
       breakdown.semantic_score = self._cosine_similarity(
           profile.embedding, opportunity.embedding
       )
   ```

### Affected Files

- `src/opportunity_radar/services/mongo_matching_service.py:502-530`
- `src/opportunity_radar/api/v1/endpoints/profiles.py:143-189`
- `src/opportunity_radar/api/v1/endpoints/onboarding.py:26-35`

## Proposed Solutions

### Option A: Delete all user matches before recomputation (Recommended)

**Pros**:
- Simple, clean state
- No stale data

**Cons**:
- Loses bookmark/dismiss state (need to preserve these)

**Effort**: Small
**Risk**: Medium (need to preserve user actions)

```python
async def save_matches(self, user_id: str, matches: List[MatchResult]) -> List[Match]:
    # Preserve user actions
    existing_bookmarks = await Match.find(
        Match.user_id == user_id,
        Match.is_bookmarked == True
    ).to_list()
    bookmark_opp_ids = {m.opportunity_id for m in existing_bookmarks}

    # Delete non-bookmarked matches
    await Match.find(
        Match.user_id == user_id,
        Match.is_bookmarked == False
    ).delete()

    # Insert new matches (respecting existing bookmarks)
```

### Option B: Add versioning/timestamps and filter by freshness

**Pros**:
- Preserves history
- Flexible filtering

**Cons**:
- More complex
- Database growth

**Effort**: Medium
**Risk**: Low

### Option C: Regenerate embeddings on critical field changes

**Pros**:
- Matches reflect current profile

**Cons**:
- OpenAI API costs
- Requires detecting "critical" changes

**Effort**: Medium
**Risk**: Low

## Recommended Action

(To be filled during triage)

## Technical Details

### Critical Fields for Embedding Refresh
- tech_stack
- goals
- industries/interests
- experience_level

### Database Changes
Consider adding `computed_at` timestamp to Match model

## Acceptance Criteria

- [ ] Profile update with tech_stack change triggers embedding refresh
- [ ] Old matches are cleaned up on recomputation
- [ ] Bookmarked/dismissed state is preserved
- [ ] Match scores reflect current profile

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |

## Resources

- PR: feat/onboarding-tutorial-flow
- Files: mongo_matching_service.py, profiles.py
