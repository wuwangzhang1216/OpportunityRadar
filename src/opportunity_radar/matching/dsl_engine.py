"""DSL Engine for eligibility rule evaluation.

The DSL (Domain Specific Language) allows defining eligibility rules in JSON format.
Rules can check various conditions like region, team size, profile type, etc.

Example DSL:
{
    "rules": [
        {"type": "region_in", "values": ["US", "EU", "Global"]},
        {"type": "team_min", "value": 2},
        {"type": "team_max", "value": 5},
        {"type": "profile_type_in", "values": ["student", "indie_hacker"]},
        {"type": "stage_in", "values": ["pre-seed", "seed"]},
        {"type": "tech_any", "values": ["python", "javascript", "rust"]},
        {"type": "not_student_only"},
    ],
    "mode": "all"  # all | any
}
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """Types of eligibility rules."""

    REGION_IN = "region_in"
    REGION_NOT_IN = "region_not_in"
    TEAM_MIN = "team_min"
    TEAM_MAX = "team_max"
    PROFILE_TYPE_IN = "profile_type_in"
    PROFILE_TYPE_NOT_IN = "profile_type_not_in"
    STAGE_IN = "stage_in"
    STAGE_NOT_IN = "stage_not_in"
    TECH_ANY = "tech_any"  # Has any of the required technologies
    TECH_ALL = "tech_all"  # Has all required technologies
    INDUSTRY_ANY = "industry_any"
    STUDENT_ONLY = "student_only"
    NOT_STUDENT_ONLY = "not_student_only"
    REMOTE_OK = "remote_ok"
    CUSTOM = "custom"


class EvalMode(str, Enum):
    """Rule evaluation mode."""

    ALL = "all"  # All rules must pass
    ANY = "any"  # Any rule must pass


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""

    rule_type: str
    passed: bool
    reason: str
    suggestion: Optional[str] = None


@dataclass
class EvaluationResult:
    """Result of evaluating all rules."""

    eligible: bool
    score: float  # 0.0 to 1.0
    passed_rules: List[RuleResult] = field(default_factory=list)
    failed_rules: List[RuleResult] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def reasons(self) -> List[str]:
        """Get all failure reasons."""
        return [r.reason for r in self.failed_rules]


@dataclass
class ProfileContext:
    """Profile data for rule evaluation."""

    profile_type: Optional[str] = None
    stage: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    industries: List[str] = field(default_factory=list)
    team_size: int = 1
    region: Optional[str] = None
    is_student: bool = False
    is_remote_ok: bool = True


@dataclass
class OpportunityContext:
    """Opportunity/Batch data for rule evaluation."""

    regions: List[str] = field(default_factory=list)
    team_min: Optional[int] = None
    team_max: Optional[int] = None
    student_only: bool = False
    remote_ok: bool = True
    required_tech: List[str] = field(default_factory=list)
    required_industries: List[str] = field(default_factory=list)
    allowed_profile_types: List[str] = field(default_factory=list)
    allowed_stages: List[str] = field(default_factory=list)


class DSLEngine:
    """Engine for parsing and evaluating eligibility DSL rules."""

    def __init__(self):
        self._rule_handlers = {
            RuleType.REGION_IN: self._eval_region_in,
            RuleType.REGION_NOT_IN: self._eval_region_not_in,
            RuleType.TEAM_MIN: self._eval_team_min,
            RuleType.TEAM_MAX: self._eval_team_max,
            RuleType.PROFILE_TYPE_IN: self._eval_profile_type_in,
            RuleType.PROFILE_TYPE_NOT_IN: self._eval_profile_type_not_in,
            RuleType.STAGE_IN: self._eval_stage_in,
            RuleType.STAGE_NOT_IN: self._eval_stage_not_in,
            RuleType.TECH_ANY: self._eval_tech_any,
            RuleType.TECH_ALL: self._eval_tech_all,
            RuleType.INDUSTRY_ANY: self._eval_industry_any,
            RuleType.STUDENT_ONLY: self._eval_student_only,
            RuleType.NOT_STUDENT_ONLY: self._eval_not_student_only,
            RuleType.REMOTE_OK: self._eval_remote_ok,
        }

    def evaluate(
        self,
        profile: ProfileContext,
        opportunity: OpportunityContext,
        rules_dsl: Optional[Dict] = None,
    ) -> EvaluationResult:
        """
        Evaluate eligibility rules against a profile.

        Args:
            profile: The user profile context
            opportunity: The opportunity/batch context
            rules_dsl: Optional DSL rules (if not provided, uses opportunity context)

        Returns:
            EvaluationResult with pass/fail status and reasons
        """
        # Build rules from DSL or opportunity context
        if rules_dsl:
            rules = self._parse_dsl(rules_dsl)
            mode = EvalMode(rules_dsl.get("mode", "all"))
        else:
            rules = self._build_rules_from_context(opportunity)
            mode = EvalMode.ALL

        if not rules:
            return EvaluationResult(eligible=True, score=1.0)

        passed_rules = []
        failed_rules = []
        suggestions = []

        for rule in rules:
            result = self._evaluate_rule(rule, profile, opportunity)
            if result.passed:
                passed_rules.append(result)
            else:
                failed_rules.append(result)
                if result.suggestion:
                    suggestions.append(result.suggestion)

        # Determine eligibility based on mode
        total_rules = len(rules)
        passed_count = len(passed_rules)

        if mode == EvalMode.ALL:
            eligible = len(failed_rules) == 0
        else:  # ANY
            eligible = len(passed_rules) > 0

        # Calculate score (percentage of rules passed)
        score = passed_count / total_rules if total_rules > 0 else 1.0

        return EvaluationResult(
            eligible=eligible,
            score=score,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            suggestions=suggestions,
        )

    def _parse_dsl(self, dsl: Dict) -> List[Dict]:
        """Parse DSL JSON into rules list."""
        rules = dsl.get("rules", [])
        return rules

    def _build_rules_from_context(self, opp: OpportunityContext) -> List[Dict]:
        """Build rules from opportunity context."""
        rules = []

        if opp.regions and "Global" not in opp.regions:
            rules.append({"type": RuleType.REGION_IN, "values": opp.regions})

        if opp.team_min:
            rules.append({"type": RuleType.TEAM_MIN, "value": opp.team_min})

        if opp.team_max:
            rules.append({"type": RuleType.TEAM_MAX, "value": opp.team_max})

        if opp.student_only:
            rules.append({"type": RuleType.STUDENT_ONLY})

        if opp.allowed_profile_types:
            rules.append({"type": RuleType.PROFILE_TYPE_IN, "values": opp.allowed_profile_types})

        if opp.allowed_stages:
            rules.append({"type": RuleType.STAGE_IN, "values": opp.allowed_stages})

        if opp.required_tech:
            rules.append({"type": RuleType.TECH_ANY, "values": opp.required_tech})

        if opp.required_industries:
            rules.append({"type": RuleType.INDUSTRY_ANY, "values": opp.required_industries})

        return rules

    def _evaluate_rule(
        self,
        rule: Dict,
        profile: ProfileContext,
        opportunity: OpportunityContext,
    ) -> RuleResult:
        """Evaluate a single rule."""
        rule_type = rule.get("type")

        try:
            rule_enum = RuleType(rule_type)
            handler = self._rule_handlers.get(rule_enum)

            if handler:
                return handler(rule, profile, opportunity)
            else:
                return RuleResult(
                    rule_type=rule_type,
                    passed=True,
                    reason=f"Unknown rule type: {rule_type}",
                )
        except ValueError:
            return RuleResult(
                rule_type=rule_type,
                passed=True,
                reason=f"Invalid rule type: {rule_type}",
            )

    # Rule handlers
    def _eval_region_in(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        allowed = set(v.lower() for v in rule.get("values", []))
        user_region = (profile.region or "").lower()

        # Global always passes
        if "global" in allowed:
            return RuleResult(
                rule_type="region_in",
                passed=True,
                reason="Open to all regions",
            )

        if user_region and user_region in allowed:
            return RuleResult(
                rule_type="region_in",
                passed=True,
                reason=f"Your region ({profile.region}) is eligible",
            )

        return RuleResult(
            rule_type="region_in",
            passed=False,
            reason=f"Limited to regions: {', '.join(rule.get('values', []))}",
            suggestion=f"This opportunity is only available in {', '.join(rule.get('values', []))}",
        )

    def _eval_region_not_in(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        excluded = set(v.lower() for v in rule.get("values", []))
        user_region = (profile.region or "").lower()

        if user_region and user_region in excluded:
            return RuleResult(
                rule_type="region_not_in",
                passed=False,
                reason=f"Your region ({profile.region}) is not eligible",
                suggestion=f"This opportunity excludes participants from {profile.region}",
            )

        return RuleResult(
            rule_type="region_not_in",
            passed=True,
            reason="Your region is not excluded",
        )

    def _eval_team_min(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        min_size = rule.get("value", 1)

        if profile.team_size >= min_size:
            return RuleResult(
                rule_type="team_min",
                passed=True,
                reason=f"Team size ({profile.team_size}) meets minimum ({min_size})",
            )

        return RuleResult(
            rule_type="team_min",
            passed=False,
            reason=f"Requires minimum team size of {min_size}",
            suggestion=f"Find {min_size - profile.team_size} more teammate(s) to be eligible",
        )

    def _eval_team_max(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        max_size = rule.get("value", 999)

        if profile.team_size <= max_size:
            return RuleResult(
                rule_type="team_max",
                passed=True,
                reason=f"Team size ({profile.team_size}) within maximum ({max_size})",
            )

        return RuleResult(
            rule_type="team_max",
            passed=False,
            reason=f"Maximum team size is {max_size}",
            suggestion=f"Your team ({profile.team_size}) exceeds the maximum of {max_size}",
        )

    def _eval_profile_type_in(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        allowed = set(v.lower() for v in rule.get("values", []))
        user_type = (profile.profile_type or "").lower()

        if not allowed or user_type in allowed:
            return RuleResult(
                rule_type="profile_type_in",
                passed=True,
                reason="Your profile type is eligible",
            )

        return RuleResult(
            rule_type="profile_type_in",
            passed=False,
            reason=f"Only for: {', '.join(rule.get('values', []))}",
            suggestion=f"This is targeted at {', '.join(rule.get('values', []))}",
        )

    def _eval_profile_type_not_in(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        excluded = set(v.lower() for v in rule.get("values", []))
        user_type = (profile.profile_type or "").lower()

        if user_type in excluded:
            return RuleResult(
                rule_type="profile_type_not_in",
                passed=False,
                reason=f"Not open to {profile.profile_type}",
            )

        return RuleResult(
            rule_type="profile_type_not_in",
            passed=True,
            reason="Your profile type is not excluded",
        )

    def _eval_stage_in(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        allowed = set(v.lower() for v in rule.get("values", []))
        user_stage = (profile.stage or "").lower()

        if not allowed or user_stage in allowed:
            return RuleResult(
                rule_type="stage_in",
                passed=True,
                reason="Your stage is eligible",
            )

        return RuleResult(
            rule_type="stage_in",
            passed=False,
            reason=f"Only for stages: {', '.join(rule.get('values', []))}",
            suggestion=f"This is for {', '.join(rule.get('values', []))} stage companies",
        )

    def _eval_stage_not_in(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        excluded = set(v.lower() for v in rule.get("values", []))
        user_stage = (profile.stage or "").lower()

        if user_stage in excluded:
            return RuleResult(
                rule_type="stage_not_in",
                passed=False,
                reason=f"Not open to {profile.stage} stage",
            )

        return RuleResult(
            rule_type="stage_not_in",
            passed=True,
            reason="Your stage is not excluded",
        )

    def _eval_tech_any(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        required = set(v.lower() for v in rule.get("values", []))
        user_tech = set(v.lower() for v in profile.tech_stack)

        if not required:
            return RuleResult(
                rule_type="tech_any",
                passed=True,
                reason="No specific tech requirements",
            )

        overlap = required & user_tech
        if overlap:
            return RuleResult(
                rule_type="tech_any",
                passed=True,
                reason=f"You have relevant tech: {', '.join(overlap)}",
            )

        return RuleResult(
            rule_type="tech_any",
            passed=False,
            reason=f"Requires tech: {', '.join(rule.get('values', []))}",
            suggestion=f"Learn one of: {', '.join(rule.get('values', []))} to participate",
        )

    def _eval_tech_all(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        required = set(v.lower() for v in rule.get("values", []))
        user_tech = set(v.lower() for v in profile.tech_stack)

        if not required:
            return RuleResult(
                rule_type="tech_all",
                passed=True,
                reason="No specific tech requirements",
            )

        missing = required - user_tech
        if not missing:
            return RuleResult(
                rule_type="tech_all",
                passed=True,
                reason="You have all required technologies",
            )

        return RuleResult(
            rule_type="tech_all",
            passed=False,
            reason=f"Missing required tech: {', '.join(missing)}",
            suggestion=f"Add these to your skillset: {', '.join(missing)}",
        )

    def _eval_industry_any(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        required = set(v.lower() for v in rule.get("values", []))
        user_industries = set(v.lower() for v in profile.industries)

        if not required:
            return RuleResult(
                rule_type="industry_any",
                passed=True,
                reason="Open to all industries",
            )

        overlap = required & user_industries
        if overlap:
            return RuleResult(
                rule_type="industry_any",
                passed=True,
                reason=f"You have relevant industry experience: {', '.join(overlap)}",
            )

        return RuleResult(
            rule_type="industry_any",
            passed=False,
            reason=f"Focused on industries: {', '.join(rule.get('values', []))}",
            suggestion=f"This is for {', '.join(rule.get('values', []))} industry",
        )

    def _eval_student_only(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        if profile.is_student or profile.profile_type == "student":
            return RuleResult(
                rule_type="student_only",
                passed=True,
                reason="You are a student",
            )

        return RuleResult(
            rule_type="student_only",
            passed=False,
            reason="This opportunity is for students only",
            suggestion="This hackathon is restricted to students",
        )

    def _eval_not_student_only(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        # This rule passes if the opportunity is NOT student-only
        # or if the user IS a student
        return RuleResult(
            rule_type="not_student_only",
            passed=True,
            reason="Open to non-students",
        )

    def _eval_remote_ok(
        self, rule: Dict, profile: ProfileContext, opp: OpportunityContext
    ) -> RuleResult:
        if opp.remote_ok or profile.is_remote_ok:
            return RuleResult(
                rule_type="remote_ok",
                passed=True,
                reason="Remote participation allowed",
            )

        return RuleResult(
            rule_type="remote_ok",
            passed=False,
            reason="In-person attendance required",
            suggestion="This requires in-person attendance",
        )


# Singleton instance
_dsl_engine: Optional[DSLEngine] = None


def get_dsl_engine() -> DSLEngine:
    """Get or create the DSL engine singleton."""
    global _dsl_engine
    if _dsl_engine is None:
        _dsl_engine = DSLEngine()
    return _dsl_engine
