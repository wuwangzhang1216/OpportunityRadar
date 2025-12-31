"""Material generator service for AI-powered content generation."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .client import get_default_llm_client, BaseLLMClient
from .prompts.templates import TEMPLATES, SYSTEM_PROMPTS

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Project information for material generation."""

    name: str
    problem: str
    solution: str
    tech_stack: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    demo_url: Optional[str] = None


@dataclass
class OpportunityContext:
    """Opportunity context for material generation."""

    title: str
    themes: List[str] = field(default_factory=list)
    judge_profiles: List[str] = field(default_factory=list)
    requirements: Optional[str] = None


@dataclass
class GenerationResult:
    """Result of material generation."""

    content: str
    material_type: str
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MaterialGenerator:
    """Service for generating hackathon materials using LLM."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.client = llm_client or get_default_llm_client()

    async def generate_readme(
        self,
        project: ProjectContext,
        opportunity: OpportunityContext,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """Generate a README.md for the project."""

        prompt = TEMPLATES["readme"](
            project_name=project.name,
            problem=project.problem,
            solution=project.solution,
            tech_stack=project.tech_stack,
            opportunity_title=opportunity.title,
            opportunity_themes=opportunity.themes,
            demo_url=project.demo_url,
            constraints=constraints,
        )

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["readme"],
            max_tokens=3000,
            temperature=0.7,
        )

        return GenerationResult(
            content=content,
            material_type="readme",
            metadata={"project": project.name, "opportunity": opportunity.title},
        )

    async def generate_pitch(
        self,
        project: ProjectContext,
        opportunity: OpportunityContext,
        time_limit_min: int = 3,
        highlight_demo: bool = False,
        include_user_evidence: bool = False,
    ) -> GenerationResult:
        """Generate a pitch script for the project."""

        # Select appropriate template based on time
        template_key = f"pitch_{time_limit_min}min"
        if template_key not in TEMPLATES:
            template_key = "pitch_3min"

        from .prompts.templates import build_pitch_prompt

        prompt = build_pitch_prompt(
            project_name=project.name,
            problem=project.problem,
            solution=project.solution,
            tech_stack=project.tech_stack,
            opportunity_title=opportunity.title,
            time_limit_min=time_limit_min,
            highlight_demo=highlight_demo,
            include_user_evidence=include_user_evidence,
        )

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["pitch"],
            max_tokens=2500,
            temperature=0.7,
        )

        return GenerationResult(
            content=content,
            material_type=f"pitch_{time_limit_min}min",
            metadata={
                "project": project.name,
                "time_limit": time_limit_min,
            },
        )

    async def generate_demo_script(
        self,
        project: ProjectContext,
        time_limit_min: int = 2,
    ) -> GenerationResult:
        """Generate a demo script for the project."""

        from .prompts.templates import build_demo_script_prompt

        prompt = build_demo_script_prompt(
            project_name=project.name,
            solution=project.solution,
            tech_stack=project.tech_stack,
            features=project.features,
            demo_url=project.demo_url,
            time_limit_min=time_limit_min,
        )

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["demo_script"],
            max_tokens=2000,
            temperature=0.6,
        )

        return GenerationResult(
            content=content,
            material_type="demo_script",
            metadata={"project": project.name, "time_limit": time_limit_min},
        )

    async def generate_qa_predictions(
        self,
        project: ProjectContext,
        opportunity: OpportunityContext,
    ) -> GenerationResult:
        """Generate predicted Q&A for judges."""

        from .prompts.templates import build_qa_prompt

        prompt = build_qa_prompt(
            project_name=project.name,
            problem=project.problem,
            solution=project.solution,
            tech_stack=project.tech_stack,
            opportunity_title=opportunity.title,
            opportunity_themes=opportunity.themes,
            judge_profiles=opportunity.judge_profiles,
        )

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["qa_pred"],
            max_tokens=3000,
            temperature=0.7,
        )

        return GenerationResult(
            content=content,
            material_type="qa_pred",
            metadata={"project": project.name, "opportunity": opportunity.title},
        )

    async def generate_all(
        self,
        project: ProjectContext,
        opportunity: OpportunityContext,
        targets: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, GenerationResult]:
        """
        Generate multiple materials at once.

        Args:
            project: Project context
            opportunity: Opportunity context
            targets: List of material types to generate
            constraints: Optional generation constraints

        Returns:
            Dictionary mapping material type to generation result
        """
        results = {}

        for target in targets:
            try:
                if target == "readme":
                    results["readme"] = await self.generate_readme(
                        project, opportunity, constraints
                    )

                elif target.startswith("pitch"):
                    # Extract time from target like "pitch_3min"
                    time_limit = 3
                    if "_" in target:
                        try:
                            time_str = target.split("_")[1].replace("min", "")
                            time_limit = int(time_str)
                        except (IndexError, ValueError):
                            pass

                    highlight_demo = constraints.get("highlight_demo", False) if constraints else False
                    include_evidence = constraints.get("include_user_evidence", False) if constraints else False

                    results[target] = await self.generate_pitch(
                        project,
                        opportunity,
                        time_limit_min=time_limit,
                        highlight_demo=highlight_demo,
                        include_user_evidence=include_evidence,
                    )

                elif target == "demo_script":
                    time_limit = constraints.get("time_limit_min", 2) if constraints else 2
                    results["demo_script"] = await self.generate_demo_script(
                        project, time_limit_min=time_limit
                    )

                elif target == "qa_pred":
                    results["qa_pred"] = await self.generate_qa_predictions(
                        project, opportunity
                    )

                else:
                    logger.warning(f"Unknown material target: {target}")

            except Exception as e:
                logger.error(f"Failed to generate {target}: {e}")
                results[target] = GenerationResult(
                    content=f"Error generating {target}: {str(e)}",
                    material_type=target,
                    metadata={"error": str(e)},
                )

        return results


# Singleton instance
_generator: Optional[MaterialGenerator] = None


def get_material_generator() -> MaterialGenerator:
    """Get or create the material generator singleton."""
    global _generator
    if _generator is None:
        _generator = MaterialGenerator()
    return _generator
