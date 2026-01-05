# 009: Untyped Match Data (any type)

## Metadata
- **Status**: resolved
- **Priority**: P3 (Nice-to-have)
- **Issue ID**: 009
- **Tags**: code-review, typescript, type-safety
- **Dependencies**: 002-pending-p2-api-contract-mismatch

## Problem Statement

The opportunities page uses `match: any` which hides API response shape mismatches that TypeScript would catch with proper typing.

### Why It Matters

Type errors become runtime errors instead of compile-time errors, making debugging harder and reducing code reliability.

## Findings

### Evidence

**opportunities/page.tsx:219** - Untyped parameter:
```typescript
function MatchCard({ match }: { match: any }) {  // any type!
  const matchId = match.id || match._id;
  const batchId = match.batch_id;  // May not exist
  // ...
}
```

### Affected Files

- `frontend/app/(dashboard)/opportunities/page.tsx:219`
- `frontend/services/api-client.ts` (return types)

## Proposed Solutions

### Option A: Create proper Match interface

```typescript
interface EnrichedMatch {
  id: string;
  _id?: string;
  user_id: string;
  opportunity_id: string;
  batch_id?: string;  // Alias
  overall_score: number;
  score?: number;  // Alias
  opportunity_title?: string;
  opportunity_category?: string;
  deadline?: string;
  is_bookmarked: boolean;
  is_dismissed: boolean;
  eligibility_status?: string;
  reasons?: string[];
}

function MatchCard({ match }: { match: EnrichedMatch }) {
  // Type-safe access
}
```

**Effort**: Small
**Risk**: Low

## Acceptance Criteria

- [ ] Match interface defined in types
- [ ] MatchCard uses typed props
- [ ] API client returns typed responses

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |
