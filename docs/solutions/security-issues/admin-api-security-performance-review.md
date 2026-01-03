# Admin API Security and Performance Review Fixes

---
title: Admin API Security and Performance Review Fixes
category: security-issues
component: admin-api
tags:
  - nosql-injection
  - file-upload
  - mongodb
  - performance
  - n-plus-one
  - bulk-operations
severity: high
symptoms:
  - Search parameters passed directly to MongoDB regex
  - No file size limits on uploads
  - Token content appearing in logs
  - Slow API responses on list endpoints
  - Individual database calls in loops
verified: true
date: 2026-01-03
pr: "#1"
---

## Problem Summary

During code review of the Admin Dashboard backend (PR #1), 14 security and performance issues were identified across 4 files. These included critical vulnerabilities like NoSQL injection and sensitive data logging.

## Symptoms

- Search queries vulnerable to regex injection attacks
- Unlimited file upload sizes could cause memory exhaustion
- JWT tokens partially logged, exposing sensitive credentials
- `list_crawlers` endpoint making N+1 database queries
- Bulk operations using O(n) individual updates instead of batch operations
- Deprecated `datetime.utcnow()` usage causing timezone issues

## Root Cause Analysis

### Security Issues

1. **NoSQL Regex Injection**: User-provided search strings passed directly to MongoDB `$regex` without escaping special characters like `.*`, `^`, `$`
2. **Unbounded File Uploads**: No validation of file size before reading into memory
3. **Token Logging**: Debug logs included partial token content for troubleshooting
4. **Overly Broad Exception Handling**: `except Exception` caught all errors, masking specific issues

### Performance Issues

5. **N+1 Query Pattern**: Loop fetching latest ScraperRun for each scraper individually
6. **O(n) Bulk Operations**: Individual `update()` calls in loop instead of `update_many()`
7. **Missing Indexes**: No index on `ScraperRun.status` for common filter queries

## Solution

### 1. NoSQL Injection Prevention

```python
import re

def escape_regex(pattern: str) -> str:
    """Escape special regex characters to prevent injection."""
    return re.escape(pattern)

# Usage in queries
query = {"title": {"$regex": escape_regex(search), "$options": "i"}}
```

### 2. File Size Validation

```python
MAX_IMPORT_SIZE = 10 * 1024 * 1024  # 10MB

@admin_router.post("/opportunities/import")
async def import_opportunities(file: UploadFile, admin: User = Depends(require_admin)):
    content = await file.read()
    if len(content) > MAX_IMPORT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_IMPORT_SIZE // (1024*1024)}MB"
        )
    # Also validate file extension
    if not file.filename.lower().endswith((".json", ".csv")):
        raise HTTPException(status_code=400, detail="Only JSON and CSV files supported")
```

### 3. Remove Sensitive Data from Logs

```python
# Before (INSECURE)
logger.error(f"JWT decode error: {e}, token[:50]: {token[:50]}...")
logger.debug(f"get_current_user called with token[:50]: {token[:50]}...")

# After (SECURE)
logger.error(f"JWT decode error: {e}")
logger.debug("get_current_user called")
```

### 4. Specific Exception Handling

```python
from bson.errors import InvalidId

async def get_or_404(model: type, id: str, entity_name: str = "Resource") -> Any:
    """Fetch entity by ID or raise appropriate HTTP exception."""
    try:
        entity = await model.get(PydanticObjectId(id))
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {entity_name} ID format"
        )
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found"
        )
    return entity
```

### 5. Fix N+1 Query with Aggregation

```python
# Before: N+1 queries (15 queries for 15 scrapers)
for scraper in scrapers:
    latest = await ScraperRun.find_one(
        ScraperRun.scraper_name == scraper,
        sort=[("started_at", -1)]
    )
    results.append({"scraper": scraper, "latest_run": latest})

# After: 1 query using aggregation
pipeline = [
    {"$match": {"scraper_name": {"$in": scrapers}}},
    {"$sort": {"started_at": -1}},
    {"$group": {
        "_id": "$scraper_name",
        "latest_run": {"$first": "$$ROOT"},
        "total_runs": {"$sum": 1},
        "success_runs": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
    }},
]
results = await ScraperRun.aggregate(pipeline).to_list()
```

### 6. Bulk MongoDB Operations

```python
# Before: O(n) individual updates
for id in ids:
    opp = await Opportunity.get(id)
    if opp:
        opp.is_active = True
        await opp.save()

# After: O(1) bulk update
valid_ids = [PydanticObjectId(id) for id in ids]
result = await Opportunity.find({"_id": {"$in": valid_ids}}).update_many(
    {"$set": {"is_active": True, "updated_at": utc_now()}}
)
return {"affected": result.modified_count}
```

### 7. Add Indexes to ScraperRun

```python
class ScraperRun(Document):
    scraper_name: Indexed(str)  # Already indexed
    status: Literal["pending", "running", "success", "partial", "failed"] = "pending"
    started_at: Indexed(datetime) = Field(default_factory=_utc_now)

    class Settings:
        name = "scraper_runs"
        indexes = [
            "status",  # Add index for status filtering
        ]
```

### 8. Timezone-Aware Datetime

```python
from datetime import datetime, timezone

def utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)

# Replace all datetime.utcnow() calls with utc_now()
```

### 9. Limit Bulk Operations

```python
MAX_BULK_IDS = 100

class BulkActionRequest(BaseModel):
    action: Literal["activate", "deactivate", "delete"]
    ids: list[str] = Field(..., max_length=MAX_BULK_IDS)
```

## Files Modified

| File | Changes |
|------|---------|
| `src/opportunity_radar/api/v1/admin/router.py` | All security/performance fixes |
| `src/opportunity_radar/core/security.py` | Remove token logging |
| `src/opportunity_radar/models/scraper_run.py` | Add indexes, fix datetime |
| `src/opportunity_radar/models/user.py` | Fix datetime deprecation |

## Prevention Strategies

### Code Review Checklist

- [ ] Search parameters escaped before regex queries?
- [ ] File uploads validated for size and type?
- [ ] No sensitive data (tokens, passwords) in log messages?
- [ ] Using specific exception types instead of bare `except`?
- [ ] List endpoints using aggregation instead of N+1 loops?
- [ ] Bulk operations using `update_many`/`delete_many`?
- [ ] Appropriate indexes on frequently filtered fields?
- [ ] Using timezone-aware datetime functions?

### Automated Detection

1. **NoSQL Injection**: Grep for `$regex` without `re.escape`
   ```bash
   grep -r '\$regex.*search\|query\|filter' --include="*.py" | grep -v 'escape_regex\|re.escape'
   ```

2. **Token Logging**: Grep for token in log statements
   ```bash
   grep -r 'logger\.\(debug\|info\|error\).*token' --include="*.py"
   ```

3. **datetime.utcnow()**: Deprecated usage
   ```bash
   grep -r 'datetime\.utcnow' --include="*.py"
   ```

4. **Bare except**: Overly broad exception handling
   ```bash
   grep -r 'except Exception:' --include="*.py"
   ```

## Related Documentation

- [P0 Admin Dashboard Plan](../plans/P0-admin-dashboard.md)
- [PR #1: Admin Dashboard Backend](https://github.com/wuwangzhang1216/OpportunityRadar/pull/1)

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial documentation after PR #1 code review fixes |
