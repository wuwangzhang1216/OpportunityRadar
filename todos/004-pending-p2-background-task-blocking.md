# 004: Background Task Event Loop Blocking

## Metadata
- **Status**: pending
- **Priority**: P2 (Important)
- **Issue ID**: 004
- **Tags**: code-review, performance, architecture
- **Dependencies**: None

## Problem Statement

Heavy match computation runs in FastAPI's `BackgroundTasks` on the main API process. This loads all opportunities into memory and performs CPU-intensive scoring, risking event-loop blocking under load.

### Why It Matters

During match computation:
- API responsiveness degrades
- Other requests may timeout
- Single user action can impact all users
- Memory spikes when loading all opportunities

## Findings

### Evidence

1. **onboarding.py:26-35, 88-92** - Match computation in BackgroundTasks:
   ```python
   async def compute_matches_background(user_id: str, profile_id: str):
       service = MongoMatchingService()
       matches = await service.compute_matches_for_profile(profile_id, limit=100, min_score=0.0)
       await service.save_matches(user_id, matches)

   @router.post("/confirm", ...)
   async def confirm_profile(...):
       background_tasks.add_task(compute_matches_background, ...)
   ```

2. **matches.py:133-143** - Same pattern for manual calculation:
   ```python
   @router.post("/calculate")
   async def calculate_matches(...):
       async def compute_matches_task():
           service = MongoMatchingService()
           matches = await service.compute_matches_for_profile(...)
       background_tasks.add_task(compute_matches_task)
   ```

3. **mongo_matching_service.py:180-220** - Loads all opportunities:
   ```python
   async def compute_matches_for_profile(self, profile_id: str, ...):
       # Gets all active opportunities
       opportunities = await Opportunity.find(
           Opportunity.is_active == True
       ).to_list()  # Could be thousands!
   ```

### Affected Files

- `src/opportunity_radar/api/v1/endpoints/onboarding.py:26-35, 88-92`
- `src/opportunity_radar/api/v1/endpoints/matches.py:133-143`
- `src/opportunity_radar/api/v1/endpoints/profiles.py:17-27, 185-189`
- `src/opportunity_radar/services/mongo_matching_service.py:180-220`

## Proposed Solutions

### Option A: Use task queue (Celery/ARQ) - Recommended for production

**Pros**:
- Isolates heavy work from API process
- Scalable
- Retries/monitoring built-in

**Cons**:
- Infrastructure complexity
- Deployment changes

**Effort**: Large
**Risk**: Medium

### Option B: Add batching and yield points (Quick fix)

**Pros**:
- No infrastructure changes
- Reduces blocking

**Cons**:
- Still runs on API process
- Not truly scalable

**Effort**: Small
**Risk**: Low

```python
async def compute_matches_for_profile(self, profile_id: str, ...):
    opportunities = await Opportunity.find(...).to_list()

    for i, opp in enumerate(opportunities):
        # Yield every 50 opportunities to allow other tasks
        if i % 50 == 0:
            await asyncio.sleep(0)

        # Process opportunity
```

### Option C: Limit opportunity batch size

**Pros**:
- Reduces memory footprint
- Faster individual computations

**Cons**:
- May miss relevant opportunities

**Effort**: Small
**Risk**: Low

## Recommended Action

(To be filled during triage)

## Technical Details

### Current Flow
1. User confirms profile
2. API handler adds background task
3. Background task runs on same process
4. Loads ~500+ opportunities
5. Computes scores (CPU intensive)
6. Saves matches

### Estimated Impact
- With 500 opportunities: 2-5 seconds blocking
- With 5000 opportunities: 20-50 seconds blocking

## Acceptance Criteria

- [ ] Match computation doesn't block API responses
- [ ] API response time <500ms during computation
- [ ] Memory usage stable during computation
- [ ] Consider task queue for future scaling

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |

## Resources

- PR: feat/onboarding-tutorial-flow
- FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- ARQ (async task queue): https://arq-docs.helpmanual.io/
