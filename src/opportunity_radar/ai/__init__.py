"""AI generation package."""

from .client import (
    BaseLLMClient,
    OpenAIClient,
    ClaudeClient,
    get_llm_client,
    get_default_llm_client,
)
from .generator import (
    MaterialGenerator,
    ProjectContext,
    OpportunityContext,
    GenerationResult,
    get_material_generator,
)

__all__ = [
    # LLM Clients
    "BaseLLMClient",
    "OpenAIClient",
    "ClaudeClient",
    "get_llm_client",
    "get_default_llm_client",
    # Generator
    "MaterialGenerator",
    "ProjectContext",
    "OpportunityContext",
    "GenerationResult",
    "get_material_generator",
]
