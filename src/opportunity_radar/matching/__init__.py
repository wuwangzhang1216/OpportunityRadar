"""Matching engine package."""

from .dsl_engine import (
    DSLEngine,
    RuleType,
    EvalMode,
    RuleResult,
    EvaluationResult,
    ProfileContext,
    OpportunityContext,
    get_dsl_engine,
)
from .scorer import (
    MatchingScorer,
    ScoreBreakdown,
    MatchResult,
    get_scorer,
)

__all__ = [
    # DSL Engine
    "DSLEngine",
    "RuleType",
    "EvalMode",
    "RuleResult",
    "EvaluationResult",
    "ProfileContext",
    "OpportunityContext",
    "get_dsl_engine",
    # Scorer
    "MatchingScorer",
    "ScoreBreakdown",
    "MatchResult",
    "get_scorer",
]
