"""Unit tests for Redis client functionality."""

import pytest


class TestRedisClientImport:
    """Test Redis client module imports."""

    def test_import_get_redis(self):
        """Test get_redis import."""
        from src.opportunity_radar.core.redis_client import get_redis

        assert get_redis is not None
        assert callable(get_redis)

    def test_import_close_redis(self):
        """Test close_redis import."""
        from src.opportunity_radar.core.redis_client import close_redis

        assert close_redis is not None
        assert callable(close_redis)

    def test_import_oauth_state_store(self):
        """Test OAuthStateStore import."""
        from src.opportunity_radar.core.redis_client import OAuthStateStore

        assert OAuthStateStore is not None


class TestOAuthStateStoreConfig:
    """Test OAuthStateStore configuration."""

    def test_oauth_state_prefix(self):
        """Test OAuth state key prefix is set."""
        from src.opportunity_radar.core.redis_client import OAuthStateStore

        assert hasattr(OAuthStateStore, "PREFIX")
        assert OAuthStateStore.PREFIX.startswith("oauth_state")

    def test_oauth_state_ttl(self):
        """Test OAuth state TTL is reasonable."""
        from src.opportunity_radar.core.redis_client import OAuthStateStore

        assert hasattr(OAuthStateStore, "TTL_SECONDS")
        # TTL should be between 1 and 10 minutes (60-600 seconds)
        assert 60 <= OAuthStateStore.TTL_SECONDS <= 600

    def test_oauth_state_store_methods(self):
        """Test OAuthStateStore has required methods."""
        from src.opportunity_radar.core.redis_client import OAuthStateStore

        assert hasattr(OAuthStateStore, "store")
        assert hasattr(OAuthStateStore, "get")
        assert hasattr(OAuthStateStore, "delete")
        assert hasattr(OAuthStateStore, "get_and_delete")

    def test_oauth_state_methods_are_async(self):
        """Test OAuthStateStore methods are async."""
        import asyncio
        from src.opportunity_radar.core.redis_client import OAuthStateStore

        # Check if methods are coroutine functions
        assert asyncio.iscoroutinefunction(OAuthStateStore.store)
        assert asyncio.iscoroutinefunction(OAuthStateStore.get)
        assert asyncio.iscoroutinefunction(OAuthStateStore.delete)
        assert asyncio.iscoroutinefunction(OAuthStateStore.get_and_delete)
