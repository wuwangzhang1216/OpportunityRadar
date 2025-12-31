"""Prompt templates for material generation."""

from typing import Dict, Any, List, Optional

# System prompts for different material types
SYSTEM_PROMPTS = {
    "readme": """You are an expert technical writer who creates compelling README files for hackathon projects.
You understand what judges look for and how to present projects professionally.
Write in clear, concise markdown with proper formatting.""",

    "pitch": """You are a startup pitch coach who has helped hundreds of teams win hackathons and competitions.
You know how to structure compelling narratives that highlight problem-solution fit and technical innovation.
Keep the pitch conversational but impactful.""",

    "demo_script": """You are a product demo expert who creates engaging live demonstration scripts.
You understand timing, audience engagement, and how to showcase features effectively.
Include specific timing cues and transition points.""",

    "qa_pred": """You are an experienced hackathon judge and technical interviewer.
You can anticipate the questions that judges commonly ask based on the project and opportunity context.
Provide thoughtful answers that demonstrate deep understanding.""",
}


def build_readme_prompt(
    project_name: str,
    problem: str,
    solution: str,
    tech_stack: List[str],
    opportunity_title: str,
    opportunity_themes: List[str],
    demo_url: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
) -> str:
    """Build prompt for README generation."""

    themes_str = ", ".join(opportunity_themes) if opportunity_themes else "general"
    tech_str = ", ".join(tech_stack) if tech_stack else "various technologies"

    prompt = f"""Create a compelling hackathon README for the following project:

**Hackathon:** {opportunity_title}
**Themes:** {themes_str}

**Project Name:** {project_name}
**Problem:** {problem}
**Solution:** {solution}
**Tech Stack:** {tech_str}
"""

    if demo_url:
        prompt += f"**Demo URL:** {demo_url}\n"

    prompt += """
Generate a README.md that includes:
1. A catchy project title with emoji
2. Brief one-liner description
3. Screenshots/demo placeholder
4. Problem statement section
5. Solution overview
6. Key features (3-5 bullet points)
7. Tech stack with brief explanations
8. Getting started / Installation
9. Usage examples
10. Team section placeholder
11. License

Make it visually appealing with proper markdown formatting, badges placeholders, and clear sections.
Focus on what judges want to see: clarity, innovation, and completeness.
"""

    return prompt


def build_pitch_prompt(
    project_name: str,
    problem: str,
    solution: str,
    tech_stack: List[str],
    opportunity_title: str,
    time_limit_min: int = 3,
    highlight_demo: bool = False,
    include_user_evidence: bool = False,
) -> str:
    """Build prompt for pitch script generation."""

    prompt = f"""Create a {time_limit_min}-minute pitch script for the following hackathon project:

**Hackathon:** {opportunity_title}
**Project Name:** {project_name}
**Problem:** {problem}
**Solution:** {solution}
**Tech Stack:** {', '.join(tech_stack) if tech_stack else 'various technologies'}

Generate a pitch script with:
1. Hook/Opening (15 seconds) - grab attention
2. Problem statement (30 seconds) - make them feel the pain
3. Solution introduction (45 seconds) - your unique approach
4. Demo highlights (60 seconds) - key features to show
5. Technical depth (30 seconds) - impressive technical decisions
6. Impact/Vision (20 seconds) - why it matters
7. Closing (10 seconds) - memorable ending

Include:
- Timing marks [0:00] at each section
- Speaker notes in (parentheses)
- Transition phrases
"""

    if highlight_demo:
        prompt += "\n- Emphasize the live demo portions with specific UI/UX callouts"

    if include_user_evidence:
        prompt += "\n- Include placeholders for user testimonials or data points"

    prompt += f"\n\nTotal time: {time_limit_min} minutes. Be precise with timing."

    return prompt


def build_demo_script_prompt(
    project_name: str,
    solution: str,
    tech_stack: List[str],
    features: List[str],
    demo_url: Optional[str] = None,
    time_limit_min: int = 2,
) -> str:
    """Build prompt for demo script generation."""

    features_str = "\n".join(f"- {f}" for f in features) if features else "- Main feature"

    prompt = f"""Create a {time_limit_min}-minute live demo script for:

**Project:** {project_name}
**Solution:** {solution}
**Tech Stack:** {', '.join(tech_stack) if tech_stack else 'various technologies'}

**Features to demonstrate:**
{features_str}

Generate a step-by-step demo script with:
1. Setup (what should be pre-loaded)
2. Opening state description
3. Step-by-step actions with:
   - Exact clicks/inputs to make
   - What to say while doing it
   - Expected results
   - Timing for each step
4. Fallback plans for common issues
5. Closing state

Format:
```
[SETUP]
- Browser open to: ...
- Pre-filled data: ...

[DEMO FLOW]
[0:00-0:15] Action: ...
Say: "..."
Expected: ...
Fallback: ...
```

Keep it natural and conversational while being technically precise.
"""

    return prompt


def build_qa_prompt(
    project_name: str,
    problem: str,
    solution: str,
    tech_stack: List[str],
    opportunity_title: str,
    opportunity_themes: List[str],
    judge_profiles: Optional[List[str]] = None,
) -> str:
    """Build prompt for Q&A prediction generation."""

    prompt = f"""Predict and answer likely judge questions for this hackathon project:

**Hackathon:** {opportunity_title}
**Themes:** {', '.join(opportunity_themes) if opportunity_themes else 'general'}

**Project:** {project_name}
**Problem:** {problem}
**Solution:** {solution}
**Tech Stack:** {', '.join(tech_stack) if tech_stack else 'various technologies'}
"""

    if judge_profiles:
        prompt += f"\n**Judge backgrounds:** {', '.join(judge_profiles)}"

    prompt += """

Generate 10-15 likely questions organized by category:

1. **Technical Questions** (3-4)
   - Architecture decisions
   - Scalability
   - Security considerations

2. **Product Questions** (3-4)
   - User validation
   - Market fit
   - Competition

3. **Business Questions** (2-3)
   - Monetization
   - Go-to-market
   - Team capabilities

4. **Hackathon-Specific Questions** (2-3)
   - Theme relevance
   - Innovation factor
   - Completeness

For each question provide:
**Q:** [Question]
**A:** [2-3 sentence answer]
**Pro tip:** [What judges really want to hear]
"""

    return prompt


# Template registry
TEMPLATES = {
    "readme": build_readme_prompt,
    "pitch_1min": lambda **kw: build_pitch_prompt(**kw, time_limit_min=1),
    "pitch_3min": lambda **kw: build_pitch_prompt(**kw, time_limit_min=3),
    "pitch_5min": lambda **kw: build_pitch_prompt(**kw, time_limit_min=5),
    "demo_script": build_demo_script_prompt,
    "qa_pred": build_qa_prompt,
}
