# 006: Industries Field Data Loss During Onboarding

## Metadata
- **Status**: resolved
- **Priority**: P2 (Important)
- **Issue ID**: 006
- **Tags**: code-review, data-integrity, bug
- **Dependencies**: None

## Problem Statement

The onboarding flow captures user-selected `industries`, but the `confirm_profile` service only persists `interests`. User industry selections are silently dropped.

### Why It Matters

- Users lose their industry preferences
- Match quality degrades (missing industry context)
- Poor user experience (silent data loss)

## Findings

### Evidence

1. **onboarding-store.ts:16-17, 125-127** - Frontend captures industries:
   ```typescript
   interface OnboardingData {
     industries: string[];
     interests: string[];
     // ...
   }

   industries: Array.isArray(extracted?.industries?.value)
     ? extracted.industries.value
     : [],
   ```

2. **schemas/onboarding.py:67** - Schema accepts industries:
   ```python
   class OnboardingConfirmRequest(BaseModel):
       industries: List[str] = Field(default_factory=list)
       interests: List[str] = Field(default_factory=list)
   ```

3. **onboarding_service.py:443-490** - confirm_profile only uses interests:
   ```python
   async def confirm_profile(self, user: User, data: OnboardingConfirmRequest):
       profile = Profile(
           user_id=user.id,
           interests=data.interests,  # Only interests!
           # industries NOT used!
       )
   ```

4. **step2-confirm.tsx:295-311** - UI shows industries field to user:
   ```tsx
   <MultiSelectEditableField
     label="Industries"
     value={confirmedData.industries}
     // User edits this, but it's never saved
   />
   ```

### Affected Files

- `frontend/stores/onboarding-store.ts:16-17, 125-127`
- `frontend/app/(auth)/onboarding/components/step2-confirm.tsx:295-311`
- `src/opportunity_radar/schemas/onboarding.py:67`
- `src/opportunity_radar/services/onboarding_service.py:443-490`
- `src/opportunity_radar/models/profile.py`

## Proposed Solutions

### Option A: Map industries to interests field (Quick fix)

**Pros**:
- Minimal changes
- Data gets saved

**Cons**:
- Semantic confusion (industries vs interests)
- May need to merge arrays

**Effort**: Small
**Risk**: Low

```python
async def confirm_profile(self, user: User, data: OnboardingConfirmRequest):
    # Merge industries into interests
    all_interests = list(set(data.interests + data.industries))

    profile = Profile(
        user_id=user.id,
        interests=all_interests,
    )
```

### Option B: Add industries field to Profile model (Recommended)

**Pros**:
- Proper data modeling
- Clear distinction

**Cons**:
- Schema migration
- More fields to maintain

**Effort**: Medium
**Risk**: Low

```python
# models/profile.py
class Profile(Document):
    interests: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)  # New field

# onboarding_service.py
profile = Profile(
    user_id=user.id,
    interests=data.interests,
    industries=data.industries,
)
```

### Option C: Remove industries from frontend (Simplify)

**Pros**:
- Simpler data model
- No confusion

**Cons**:
- Lost functionality
- May affect matching quality

**Effort**: Small
**Risk**: Medium

## Recommended Action

(To be filled during triage)

## Technical Details

### Current Profile Model Fields
```python
class Profile(Document):
    user_id: PydanticObjectId
    tech_stack: List[str]
    interests: List[str]  # Also called "industries" in UI
    goals: List[str]
    # ... no explicit industries field
```

### Frontend/Backend Field Mapping
| Frontend | Backend Schema | Profile Model | Saved? |
|----------|---------------|---------------|--------|
| tech_stack | tech_stack | tech_stack | Yes |
| industries | industries | - | **No** |
| interests | interests | interests | Yes |
| goals | goals | goals | Yes |

## Acceptance Criteria

- [ ] User-selected industries are persisted
- [ ] Industries appear in user profile view
- [ ] Industries are used in matching algorithm
- [ ] No silent data loss

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |

## Resources

- PR: feat/onboarding-tutorial-flow
- Files: onboarding-store.ts, onboarding_service.py
