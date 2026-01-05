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

    async def generate_submission_text(
        self,
        project: ProjectContext,
        opportunity: OpportunityContext,
        max_chars: int = 1000,
    ) -> GenerationResult:
        """Generate submission form text for hackathon/grant applications."""

        prompt = f"""Create a compelling submission text for "{project.name}" applying to "{opportunity.title}".

Project Details:
- Problem: {project.problem}
- Solution: {project.solution}
- Tech Stack: {', '.join(project.tech_stack)}
- Key Features: {', '.join(project.features)}

Opportunity Themes: {', '.join(opportunity.themes)}

Requirements:
- Maximum {max_chars} characters
- Focus on impact and innovation
- Match the opportunity's themes
- Be concise but compelling
- Include measurable outcomes if possible

Generate a submission text that will stand out to judges."""

        system_prompt = """You are an expert at writing winning hackathon and grant submissions.
Create concise, impactful text that highlights innovation and potential impact."""

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.7,
        )

        return GenerationResult(
            content=content,
            material_type="submission_text",
            metadata={"project": project.name, "max_chars": max_chars},
        )

    async def generate_one_liner(
        self,
        project: ProjectContext,
    ) -> GenerationResult:
        """Generate a memorable one-liner tagline for the project."""

        prompt = f"""Create 5 memorable one-liner taglines for "{project.name}".

Project: {project.name}
Problem it solves: {project.problem}
Solution: {project.solution}

Requirements for each tagline:
- Maximum 10 words
- Catchy and memorable
- Explains the value proposition
- Could work as a Twitter/X pitch

Format: Number each tagline (1-5)."""

        system_prompt = "You are a creative marketing expert who crafts memorable product taglines."

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=500,
            temperature=0.8,
        )

        return GenerationResult(
            content=content,
            material_type="one_liner",
            metadata={"project": project.name},
        )

    async def generate_technical_doc(
        self,
        project: ProjectContext,
        doc_type: str = "architecture",
    ) -> GenerationResult:
        """Generate technical documentation.

        Args:
            project: Project context
            doc_type: One of 'architecture', 'api', 'setup'
        """

        prompts = {
            "architecture": f"""Create a technical architecture document for "{project.name}".

Solution: {project.solution}
Tech Stack: {', '.join(project.tech_stack)}
Features: {', '.join(project.features)}

Include:
1. System Overview (high-level architecture)
2. Component Diagram (describe in text)
3. Data Flow
4. Technology Choices and Rationale
5. Scalability Considerations

Format in Markdown.""",

            "api": f"""Create API documentation for "{project.name}".

Solution: {project.solution}
Tech Stack: {', '.join(project.tech_stack)}
Features: {', '.join(project.features)}

Include for each endpoint:
- HTTP method and path
- Description
- Request parameters
- Response format
- Example

Format in Markdown with code blocks.""",

            "setup": f"""Create a setup/installation guide for "{project.name}".

Tech Stack: {', '.join(project.tech_stack)}
Features: {', '.join(project.features)}
{'Demo URL: ' + project.demo_url if project.demo_url else ''}

Include:
1. Prerequisites
2. Installation Steps
3. Configuration
4. Running the Project
5. Troubleshooting Common Issues

Format in Markdown with code blocks.""",
        }

        prompt = prompts.get(doc_type, prompts["architecture"])
        system_prompt = "You are a senior software architect who creates clear, comprehensive technical documentation."

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.5,
        )

        return GenerationResult(
            content=content,
            material_type=f"technical_{doc_type}",
            metadata={"project": project.name, "doc_type": doc_type},
        )

    async def generate_social_media(
        self,
        project: ProjectContext,
        platform: str = "twitter",
    ) -> GenerationResult:
        """Generate social media post for the project.

        Args:
            project: Project context
            platform: One of 'twitter', 'linkedin', 'product_hunt'
        """

        platform_specs = {
            "twitter": {
                "max_chars": 280,
                "style": "casual, engaging, uses emojis, includes relevant hashtags",
                "name": "Twitter/X",
            },
            "linkedin": {
                "max_chars": 3000,
                "style": "professional, story-driven, focuses on impact and lessons learned",
                "name": "LinkedIn",
            },
            "product_hunt": {
                "max_chars": 500,
                "style": "product-focused, highlights features and benefits, includes call-to-action",
                "name": "Product Hunt",
            },
        }

        spec = platform_specs.get(platform, platform_specs["twitter"])

        prompt = f"""Create a {spec['name']} post for "{project.name}".

Project: {project.name}
Problem: {project.problem}
Solution: {project.solution}
Tech Stack: {', '.join(project.tech_stack)}
{'Demo URL: ' + project.demo_url if project.demo_url else ''}

Requirements:
- Maximum {spec['max_chars']} characters
- Style: {spec['style']}
- Should drive engagement

Create 3 variations."""

        system_prompt = f"You are a social media expert who creates viral {spec['name']} content."

        content = await self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.8,
        )

        return GenerationResult(
            content=content,
            material_type=f"social_{platform}",
            metadata={"project": project.name, "platform": platform},
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

                elif target == "submission_text":
                    max_chars = constraints.get("max_chars", 1000) if constraints else 1000
                    results["submission_text"] = await self.generate_submission_text(
                        project, opportunity, max_chars=max_chars
                    )

                elif target == "one_liner":
                    results["one_liner"] = await self.generate_one_liner(project)

                elif target.startswith("technical_"):
                    doc_type = target.replace("technical_", "") or "architecture"
                    results[target] = await self.generate_technical_doc(
                        project, doc_type=doc_type
                    )

                elif target.startswith("social_"):
                    platform = target.replace("social_", "") or "twitter"
                    results[target] = await self.generate_social_media(
                        project, platform=platform
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
