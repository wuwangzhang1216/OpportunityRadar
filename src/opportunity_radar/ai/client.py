"""LLM client abstraction supporting OpenAI and Claude."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncIterator

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion for a prompt."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client implementation using the new responses API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5.2",
    ):
        settings = get_settings()
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion using OpenAI responses API."""
        # Combine system prompt with user prompt for the new API
        full_input = prompt
        if system_prompt:
            full_input = f"{system_prompt}\n\n{prompt}"

        try:
            response = self.client.responses.create(
                model=self.model,
                input=full_input,
            )
            return response.output_text or ""
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming using OpenAI responses API."""
        # Combine system prompt with user prompt for the new API
        full_input = prompt
        if system_prompt:
            full_input = f"{system_prompt}\n\n{prompt}"

        try:
            response = self.client.responses.create(
                model=self.model,
                input=full_input,
                stream=True,
            )

            for chunk in response:
                if hasattr(chunk, 'output_text') and chunk.output_text:
                    yield chunk.output_text
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude client implementation (placeholder for future use)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
    ):
        self.api_key = api_key
        self.model = model
        # Note: Requires anthropic package to be installed
        # from anthropic import AsyncAnthropic
        # self.client = AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion using Claude."""
        # Placeholder - would use Anthropic SDK
        raise NotImplementedError("Claude client requires anthropic package")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming using Claude."""
        raise NotImplementedError("Claude client requires anthropic package")
        yield  # Make this a generator


def get_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """
    Factory function to get LLM client based on provider.

    Args:
        provider: Provider name (openai, claude). Defaults to settings.llm_provider

    Returns:
        LLM client instance
    """
    settings = get_settings()
    provider = provider or settings.llm_provider

    if provider == "openai":
        return OpenAIClient()
    elif provider == "claude":
        return ClaudeClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


# Default client singleton
_llm_client: Optional[BaseLLMClient] = None


def get_default_llm_client() -> BaseLLMClient:
    """Get or create the default LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = get_llm_client()
    return _llm_client
