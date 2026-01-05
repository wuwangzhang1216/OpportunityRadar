# 010: Missing Tests for New Endpoints

## Metadata
- **Status**: pending
- **Priority**: P3 (Nice-to-have)
- **Issue ID**: 010
- **Tags**: code-review, testing, quality
- **Dependencies**: None

## Problem Statement

The new `/matches/top`, `/matches/status`, and `/matches/calculate` endpoints have no test coverage. The onboarding polling flow is also untested.

### Why It Matters

Regressions can slip through unnoticed. The API contract is not verified.

## Findings

### Evidence

No test files found for the new endpoints:

```bash
$ rg -l "test.*matches" tests/
# No results for new endpoints
```

### New Endpoints Needing Tests

1. `GET /matches/top` - Returns enriched matches
2. `GET /matches/status` - Returns computation status
3. `POST /matches/calculate` - Triggers background computation
4. Integration: Onboarding → matches polling

### Affected Files

- `tests/` (new test files needed)
- `src/opportunity_radar/api/v1/endpoints/matches.py:49-88, 115-143, 146-178`

## Proposed Solutions

### Option A: Add pytest tests for each endpoint

```python
# tests/test_matches.py

@pytest.mark.asyncio
async def test_get_top_matches_returns_enriched_data(
    authenticated_client, user_with_profile_and_matches
):
    response = await authenticated_client.get("/api/v1/matches/top?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) <= 5
    for item in data["items"]:
        assert "score" in item
        assert "batch_id" in item
        assert "opportunity_title" in item


@pytest.mark.asyncio
async def test_get_match_status_no_profile(authenticated_client):
    response = await authenticated_client.get("/api/v1/matches/status")
    assert response.status_code == 200
    assert response.json()["status"] == "no_profile"


@pytest.mark.asyncio
async def test_calculate_matches_requires_profile(authenticated_client):
    response = await authenticated_client.post("/api/v1/matches/calculate")
    assert response.status_code == 400
```

**Effort**: Medium
**Risk**: None

## Acceptance Criteria

- [ ] Tests for /matches/top endpoint
- [ ] Tests for /matches/status endpoint
- [ ] Tests for /matches/calculate endpoint
- [ ] Integration test for onboarding flow
- [ ] All tests pass in CI

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |
