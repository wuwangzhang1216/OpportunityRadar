"""Services package."""

from .auth_service import AuthService
from .opportunity_service import OpportunityService, run_scraper_and_ingest
from .embedding_service import EmbeddingService, get_embedding_service, EmbeddingResult
from .matching_service import MatchingService, recompute_all_matches
from .mongo_matching_service import (
    MongoMatchingService,
    get_mongo_matching_service,
    recompute_all_matches_mongo,
)
from .profile_service import ProfileService
from .material_service import MaterialService
from .pipeline_service import PipelineService

__all__ = [
    "AuthService",
    "OpportunityService",
    "run_scraper_and_ingest",
    "EmbeddingService",
    "EmbeddingResult",
    "get_embedding_service",
    "MatchingService",
    "recompute_all_matches",
    "MongoMatchingService",
    "get_mongo_matching_service",
    "recompute_all_matches_mongo",
    "ProfileService",
    "MaterialService",
    "PipelineService",
]
