# P1: Matching Algorithm Optimization

> **Priority**: P1 (Core Experience)
> **Status**: `NOT_STARTED`
> **Progress**: 0%
> **Last Updated**: 2026-01-03

---

## Overview

Optimize the AI-powered matching algorithm to provide more accurate and explainable opportunity recommendations for startup teams.

---

## Why This Matters

- **Core Value Proposition**: "AI-powered matching" is the main differentiator
- **User Retention**: Poor matches = users leave
- **Trust**: Users need to understand why an opportunity is recommended

---

## Current State

Existing matching system:
- Uses OpenAI embeddings for profile and opportunity
- Cosine similarity scoring
- Basic filtering by category

**Limitations**:
- No consideration of team requirements
- No deadline awareness
- No eligibility filtering
- Matches lack explanations
- No learning from user feedback

---

## Proposed Improvements

### 1. Multi-Factor Scoring

Replace simple embedding similarity with weighted multi-factor scoring:

```python
class MatchScore:
    # Similarity Scores (0-1)
    embedding_similarity: float      # Semantic match
    tech_stack_overlap: float        # Skills match
    industry_alignment: float        # Industry match

    # Eligibility Scores (0 or 1)
    team_size_eligible: bool         # Meets team requirements
    funding_stage_eligible: bool     # Meets stage requirements
    location_eligible: bool          # Geographic eligibility

    # Timing Score (0-1)
    deadline_score: float            # Penalize near deadlines

    # Boost Factors
    goal_alignment_boost: float      # Matches user goals
    track_record_boost: float        # Past success indicators

    # Final Score
    @property
    def total_score(self) -> float:
        if not all([team_size_eligible, funding_stage_eligible, location_eligible]):
            return 0  # Hard filter

        base = (
            embedding_similarity * 0.3 +
            tech_stack_overlap * 0.25 +
            industry_alignment * 0.2 +
            deadline_score * 0.15 +
            goal_alignment_boost * 0.1
        )
        return base * (1 + track_record_boost * 0.1)
```

### 2. Match Explanations

Generate human-readable explanations:

```python
class MatchExplanation:
    primary_reason: str           # "Strong tech stack match"
    matching_skills: list[str]    # ["Python", "AI/ML"]
    matching_themes: list[str]    # ["Healthcare"]
    warnings: list[str]           # ["Deadline in 5 days"]
    tips: list[str]               # ["Similar to your YC experience"]
```

### 3. Smart Filtering

Apply hard filters before scoring:

```python
def apply_filters(opportunity, profile) -> bool:
    # Team size check
    if opportunity.team_size_min and profile.team_size < opportunity.team_size_min:
        return False
    if opportunity.team_size_max and profile.team_size > opportunity.team_size_max:
        return False

    # Already past deadline
    if opportunity.deadline and opportunity.deadline < now():
        return False

    # Geographic eligibility
    if opportunity.eligibility and not matches_eligibility(profile, opportunity):
        return False

    return True
```

### 4. Feedback Learning

Use user actions to improve future matches:

| Action | Signal |
|--------|--------|
| Bookmark | Strong positive |
| Add to pipeline | Strong positive |
| Apply | Very strong positive |
| Dismiss | Negative |
| View but no action | Weak negative |

```python
class UserFeedback:
    user_id: str
    opportunity_id: str
    action: Literal["bookmark", "pipeline", "apply", "dismiss", "view"]
    timestamp: datetime

# Use feedback to:
# 1. Boost similar opportunities
# 2. Demote similar to dismissed
# 3. Learn feature preferences
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Matching Engine                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐      ┌──────────────┐             │
│  │   Profile    │      │ Opportunity  │             │
│  │  Embedding   │      │  Embedding   │             │
│  └──────┬───────┘      └──────┬───────┘             │
│         │                     │                      │
│         └──────────┬──────────┘                      │
│                    │                                 │
│         ┌──────────▼──────────┐                      │
│         │   Hard Filters      │                      │
│         │  (team, deadline,   │                      │
│         │   eligibility)      │                      │
│         └──────────┬──────────┘                      │
│                    │                                 │
│         ┌──────────▼──────────┐                      │
│         │  Multi-Factor       │                      │
│         │  Scoring            │                      │
│         └──────────┬──────────┘                      │
│                    │                                 │
│         ┌──────────▼──────────┐                      │
│         │  Explanation        │                      │
│         │  Generator          │                      │
│         └──────────┬──────────┘                      │
│                    │                                 │
│         ┌──────────▼──────────┐                      │
│         │  Feedback           │                      │
│         │  Adjustment         │                      │
│         └──────────┬──────────┘                      │
│                    │                                 │
└────────────────────┼────────────────────────────────┘
                     │
              Ranked Matches
```

---

## Implementation Tasks

### Phase 1: Multi-Factor Scoring

- [ ] Create MatchScore model
- [ ] Implement tech stack overlap calculation
- [ ] Implement industry alignment calculation
- [ ] Implement deadline scoring
- [ ] Create weighted scoring function

### Phase 2: Hard Filters

- [ ] Implement team size filter
- [ ] Implement deadline filter
- [ ] Implement eligibility parser
- [ ] Implement location filter

### Phase 3: Explanations

- [ ] Create MatchExplanation model
- [ ] Build explanation generator
- [ ] Update API to return explanations
- [ ] Display explanations in UI

### Phase 4: Feedback Learning

- [ ] Create UserFeedback model
- [ ] Track user actions on opportunities
- [ ] Implement feedback-based adjustments
- [ ] A/B test with/without feedback

---

## API Changes

### Updated Match Response

```python
class MatchResponse:
    opportunity: OpportunityResponse
    score: float                         # Overall score
    score_breakdown: dict                # Factor breakdown
    explanation: MatchExplanation        # Human-readable
    matched_at: datetime
```

### New Feedback Endpoint

```python
POST /api/v1/matches/{id}/feedback
{
    "action": "bookmark" | "dismiss" | "apply"
}
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Click-through rate | ? | > 30% |
| Bookmark rate | ? | > 15% |
| Pipeline add rate | ? | > 10% |
| Dismiss rate | ? | < 20% |
| User reported relevance | ? | > 4/5 |

---

## Dependencies

- P1: Team Profile Enhancement (needs new profile fields)
- P0: Opportunity Crawler (needs opportunity data)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial plan created |
