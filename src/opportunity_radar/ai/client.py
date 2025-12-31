"""LLM client abstraction supporting OpenAI and Claude."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncIterator

from openai import OpenAI, AsyncOpenAI

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
    """OpenAI GPT client implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion using OpenAI."""
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
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
        """Generate completion with streaming using OpenAI."""
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
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
