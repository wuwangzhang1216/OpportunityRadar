# 002: API Contract Mismatch - skip/offset and Response Shape

## Metadata
- **Status**: resolved
- **Priority**: P2 (Important)
- **Issue ID**: 002
- **Tags**: code-review, architecture, api-contract
- **Dependencies**: None

## Problem Statement

The frontend API client and backend match endpoints have misaligned contracts:
1. Frontend sends `skip` parameter, backend expects `offset`
2. Frontend expects enriched match data (`batch_id`, `opportunity_title`), but `/matches` returns raw Match documents
3. This breaks pagination and list rendering

### Why It Matters

The opportunities page cannot properly paginate or display match cards because the data shape doesn't match expectations.

## Findings

### Evidence

1. **api-client.ts:113-115** - Frontend sends `skip`:
   ```typescript
   async getMatches(params?: { status?: string; skip?: number; limit?: number; ... }) {
     const response = await this.client.get("/matches", { params });
   ```

2. **matches.py:19-46** - Backend expects `offset`:
   ```python
   async def list_matches(
       limit: int = Query(20, ge=1, le=100),
       offset: int = Query(0, ge=0),  # Frontend sends 'skip', not 'offset'
   ```

3. **opportunities/page.tsx:223** - Frontend expects `batch_id` for navigation:
   ```typescript
   const batchId = match.batch_id;  // Used for router.push
   ```

4. **opportunities/page.tsx:356** - Card navigation uses batch_id:
   ```typescript
   router.push(`/opportunities/${batchId}`);
   ```

5. **matches.py:38-46** - `/matches` returns raw documents without enrichment:
   ```python
   return {
       "items": matches,  # Raw Match documents, no opportunity_* fields
       "total": total,
   }
   ```

### Affected Files

- `frontend/services/api-client.ts:113-115`
- `frontend/app/(dashboard)/opportunities/page.tsx:54-74, 219-233`
- `src/opportunity_radar/api/v1/endpoints/matches.py:18-46`

## Proposed Solutions

### Option A: Fix frontend to use correct parameter names (Recommended)

**Pros**:
- Quick fix
- Backend API stays consistent with offset semantics

**Cons**:
- Need to update frontend types

**Effort**: Small
**Risk**: Low

```typescript
async getMatches(params?: { status?: string; offset?: number; limit?: number; ... }) {
  const response = await this.client.get("/matches", { params });
```

### Option B: Backend accepts both skip/offset

**Pros**:
- Backward compatible

**Cons**:
- Confusing API
- Technical debt

**Effort**: Small
**Risk**: Low

### Option C: Enrich /matches response like /matches/top

**Pros**:
- Consistent response shape
- Single source of truth

**Cons**:
- Performance impact (bulk opportunity fetch)

**Effort**: Medium
**Risk**: Medium

## Recommended Action

(To be filled during triage)

## Technical Details

### Affected Components
- Backend: matches.py list_matches endpoint
- Frontend: api-client.ts, opportunities page

### API Contract Expected by Frontend
```typescript
interface Match {
  id: string;
  batch_id: string;  // Alias for opportunity_id
  score: number;     // Alias for overall_score
  opportunity_title?: string;
  opportunity_category?: string;
  deadline?: string;
  // ...
}
```

## Acceptance Criteria

- [ ] Frontend pagination works correctly
- [ ] Match cards display opportunity titles
- [ ] Card click navigates to correct opportunity detail
- [ ] API response shape is documented

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |

## Resources

- PR: feat/onboarding-tutorial-flow
- Files: matches.py:18-46, api-client.ts:113-115, opportunities/page.tsx
