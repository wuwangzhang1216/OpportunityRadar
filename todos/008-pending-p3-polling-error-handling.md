# 008: Polling Errors Silently Ignored

## Metadata
- **Status**: resolved
- **Priority**: P3 (Nice-to-have)
- **Issue ID**: 008
- **Tags**: code-review, error-handling, ux
- **Dependencies**: None

## Problem Statement

The `pollTopMatches` function in onboarding-store ignores all errors during polling. Users can end up with silent empty results without any feedback.

### Why It Matters

If the backend fails or network issues occur, users see nothing with no way to know what happened.

## Findings

### Evidence

**onboarding-store.ts:238-259** - Error ignored in catch:
```typescript
pollTopMatches: async (maxAttempts = 10) => {
  set({ isLoadingMatches: true });

  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await apiClient.getTopMatches(5);
      if (response.items?.length) {
        set({ topMatches: response.items, isLoadingMatches: false });
        return;
      }
    } catch (error) {
      // Ignore errors during polling  <-- Silent failure!
    }
    await new Promise((r) => setTimeout(r, Math.min(2000, 250 * 2 ** i)));
  }

  // Max attempts reached - no error message set!
  set({ isLoadingMatches: false });
};
```

### Affected Files

- `frontend/stores/onboarding-store.ts:238-259`

## Proposed Solutions

### Option A: Track error count and surface after threshold

```typescript
let errorCount = 0;
for (let i = 0; i < maxAttempts; i++) {
  try {
    // ...
  } catch (error) {
    errorCount++;
    if (errorCount >= 3) {
      set({
        isLoadingMatches: false,
        pollError: "Unable to load matches. Please try again later.",
      });
      return;
    }
  }
}
```

**Effort**: Small
**Risk**: Low

## Acceptance Criteria

- [ ] Persistent errors are surfaced to user
- [ ] User can retry after error
- [ ] Temporary network blips don't show error

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |
