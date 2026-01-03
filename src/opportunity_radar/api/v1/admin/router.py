"""Admin API router with all admin endpoints."""

import asyncio
import csv
import io
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from bson.errors import InvalidId
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from ....core.security import require_admin
from ....models.opportunity import Opportunity
from ....models.user import User
from ....models.match import Match
from ....models.pipeline import Pipeline
from ....models.scraper_run import ScraperRun
from ....scrapers.scheduler import ScraperRegistry

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# Constants
MAX_IMPORT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_BULK_IDS = 100  # Maximum IDs per bulk operation
MAX_SEARCH_LENGTH = 100  # Maximum search query length


# =============================================================================
# Helpers
# =============================================================================


async def get_or_404(
    model: type,
    id: str,
    entity_name: str = "Resource",
) -> Any:
    """Fetch entity by ID or raise 404.

    Args:
        model: The Beanie Document class to query.
        id: The string ID to look up.
        entity_name: Name for error messages.

    Returns:
        The found document.

    Raises:
        HTTPException: 400 if ID format is invalid, 404 if not found.
    """
    try:
        entity = await model.get(PydanticObjectId(id))
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {entity_name} ID format",
        )
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found",
        )
    return entity


def escape_regex(pattern: str) -> str:
    """Escape special regex characters to prevent injection."""
    return re.escape(pattern)


def utc_now() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


# =============================================================================
# Schemas
# =============================================================================


class OpportunityCreate(BaseModel):
    """Schema for creating an opportunity."""

    external_id: str
    title: str
    description: str | None = None
    short_description: str | None = None
    opportunity_type: str = "hackathon"
    format: str | None = None
    location_type: str | None = None
    location_city: str | None = None
    location_country: str | None = None
    website_url: str | None = None
    registration_url: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    themes: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    total_prize_value: float | None = None
    currency: str = "USD"
    team_size_min: int | None = None
    team_size_max: int | None = None
    is_featured: bool = False
    is_active: bool = True


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity (partial update)."""

    title: str | None = None
    description: str | None = None
    short_description: str | None = None
    opportunity_type: str | None = None
    format: str | None = None
    location_type: str | None = None
    location_city: str | None = None
    location_country: str | None = None
    website_url: str | None = None
    registration_url: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    themes: list[str] | None = None
    technologies: list[str] | None = None
    total_prize_value: float | None = None
    currency: str | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class BulkActionRequest(BaseModel):
    """Schema for bulk actions on opportunities."""

    action: str = Field(..., pattern="^(activate|deactivate|delete)$")
    ids: list[str] = Field(..., max_length=MAX_BULK_IDS)


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""

    affected: int
    failed: int


class ImportResponse(BaseModel):
    """Response for bulk import."""

    imported: int
    failed: int
    skipped: int
    errors: list[dict[str, str | int]]


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = None


class AnalyticsOverview(BaseModel):
    """Analytics overview response."""

    opportunity_count: int
    user_count: int
    match_count: int
    pipeline_count: int
    opportunities_by_type: dict[str, int]
    recent_signups: int


class CrawlerStatus(BaseModel):
    """Status of a crawler."""

    name: str
    last_run: datetime | None = None
    last_status: str | None = None
    total_runs: int
    success_rate: float


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: list[Any]
    total: int
    skip: int
    limit: int


# =============================================================================
# Opportunities Endpoints
# =============================================================================


@admin_router.get("/opportunities")
async def list_opportunities(
    category: str | None = Query(None, description="Filter by opportunity type"),
    search: str | None = Query(None, description="Search in title", max_length=MAX_SEARCH_LENGTH),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """List all opportunities with filters (admin only)."""
    query: dict[str, Any] = {}

    if category:
        query["opportunity_type"] = category
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        # Escape regex to prevent NoSQL injection
        query["title"] = {"$regex": escape_regex(search), "$options": "i"}

    opportunities = await Opportunity.find(query).skip(skip).limit(limit).to_list()
    total = await Opportunity.find(query).count()

    return {
        "items": opportunities,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@admin_router.post("/opportunities", status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: OpportunityCreate,
    _admin: User = Depends(require_admin),
) -> Opportunity:
    """Create a new opportunity (admin only)."""
    # Check for duplicate external_id
    existing = await Opportunity.find_one(Opportunity.external_id == data.external_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Opportunity with external_id '{data.external_id}' already exists",
        )

    opportunity = Opportunity(**data.model_dump())
    await opportunity.insert()

    logger.info(
        f"Admin {_admin.email} created opportunity {opportunity.id}",
        extra={"action": "opportunity_created", "admin_id": str(_admin.id), "target_id": str(opportunity.id)},
    )

    return opportunity


@admin_router.get("/opportunities/{opportunity_id}")
async def get_opportunity(
    opportunity_id: str,
    _admin: User = Depends(require_admin),
) -> Opportunity:
    """Get opportunity by ID (admin only)."""
    return await get_or_404(Opportunity, opportunity_id, "Opportunity")


@admin_router.patch("/opportunities/{opportunity_id}")
async def update_opportunity(
    opportunity_id: str,
    data: OpportunityUpdate,
    _admin: User = Depends(require_admin),
) -> Opportunity:
    """Update an opportunity (partial update, admin only)."""
    opportunity = await get_or_404(Opportunity, opportunity_id, "Opportunity")

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = utc_now()

    for field, value in update_data.items():
        setattr(opportunity, field, value)

    await opportunity.save()

    logger.info(
        f"Admin {_admin.email} updated opportunity {opportunity.id}",
        extra={"action": "opportunity_updated", "admin_id": str(_admin.id), "target_id": str(opportunity.id)},
    )

    return opportunity


@admin_router.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: str,
    hard: bool = Query(False, description="Perform hard delete instead of soft delete"),
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """Delete an opportunity (soft delete by default, admin only)."""
    opportunity = await get_or_404(Opportunity, opportunity_id, "Opportunity")

    if hard:
        await opportunity.delete()
        action = "opportunity_hard_deleted"
    else:
        opportunity.is_active = False
        opportunity.updated_at = utc_now()
        await opportunity.save()
        action = "opportunity_soft_deleted"

    logger.info(
        f"Admin {_admin.email} {action.replace('_', ' ')} {opportunity_id}",
        extra={"action": action, "admin_id": str(_admin.id), "target_id": str(opportunity_id)},
    )

    return {"ok": True, "action": action}


@admin_router.post("/opportunities/import", response_model=ImportResponse)
async def import_opportunities(
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin),
) -> ImportResponse:
    """Bulk import opportunities from CSV or JSON file (admin only)."""
    # Check file size before reading
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if size > MAX_IMPORT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_IMPORT_SIZE // (1024 * 1024)}MB",
        )

    # Validate file extension (case-insensitive)
    filename = file.filename or ""
    if not filename.lower().endswith((".json", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be .json or .csv",
        )

    content = await file.read()
    content_str = content.decode("utf-8")

    imported = 0
    failed = 0
    skipped = 0
    errors: list[dict[str, str | int]] = []

    # Determine file type and parse
    if filename.lower().endswith(".json"):
        try:
            data = json.loads(content_str)
            if not isinstance(data, list):
                data = [data]
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON: {str(e)}",
            )
    else:  # .csv
        try:
            reader = csv.DictReader(io.StringIO(content_str))
            data = list(reader)
        except csv.Error as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CSV: {str(e)}",
            )

    # Bulk lookup for duplicates (optimization: 1 query instead of N)
    external_ids = [row.get("external_id") for row in data if row.get("external_id")]
    existing_docs = await Opportunity.find({"external_id": {"$in": external_ids}}).to_list()
    existing_ids = {doc.external_id for doc in existing_docs}

    opportunities_to_insert = []

    for row_num, row in enumerate(data, start=1):
        try:
            # Check required fields
            if "title" not in row or not row["title"]:
                errors.append({"row": row_num, "error": "Missing required field: title"})
                failed += 1
                continue

            if "external_id" not in row or not row["external_id"]:
                errors.append({"row": row_num, "error": "Missing required field: external_id"})
                failed += 1
                continue

            # Check for duplicate
            if row["external_id"] in existing_ids:
                skipped += 1
                continue

            # Parse list fields from CSV (comma-separated strings)
            themes = row.get("themes", [])
            if isinstance(themes, str):
                themes = [t.strip() for t in themes.split(",") if t.strip()]

            technologies = row.get("technologies", [])
            if isinstance(technologies, str):
                technologies = [t.strip() for t in technologies.split(",") if t.strip()]

            # Create opportunity
            opportunity = Opportunity(
                external_id=row["external_id"],
                title=row["title"],
                description=row.get("description"),
                short_description=row.get("short_description"),
                opportunity_type=row.get("opportunity_type", "hackathon"),
                format=row.get("format"),
                location_city=row.get("location_city"),
                location_country=row.get("location_country"),
                website_url=row.get("website_url"),
                themes=themes,
                technologies=technologies,
                total_prize_value=float(row["total_prize_value"]) if row.get("total_prize_value") else None,
                is_active=True,
            )
            opportunities_to_insert.append(opportunity)
            # Track this ID as now "existing" to handle duplicates within the same file
            existing_ids.add(row["external_id"])

        except ValueError as e:
            errors.append({"row": row_num, "error": f"Value error: {str(e)}"})
            failed += 1
        except KeyError as e:
            errors.append({"row": row_num, "error": f"Missing field: {str(e)}"})
            failed += 1

    # Bulk insert all at once (optimization: 1 operation instead of N)
    if opportunities_to_insert:
        await Opportunity.insert_many(opportunities_to_insert)
        imported = len(opportunities_to_insert)

    logger.info(
        f"Admin {_admin.email} imported {imported} opportunities ({failed} failed, {skipped} skipped)",
        extra={"action": "opportunities_imported", "admin_id": str(_admin.id), "imported": imported},
    )

    return ImportResponse(imported=imported, failed=failed, skipped=skipped, errors=errors)


@admin_router.post("/opportunities/bulk-action", response_model=BulkActionResponse)
async def bulk_action_opportunities(
    data: BulkActionRequest,
    _admin: User = Depends(require_admin),
) -> BulkActionResponse:
    """Perform bulk actions on opportunities (admin only)."""
    # Convert string IDs to ObjectIds, tracking failures
    valid_ids = []
    failed = 0

    for opp_id in data.ids:
        try:
            valid_ids.append(PydanticObjectId(opp_id))
        except InvalidId:
            failed += 1

    if not valid_ids:
        return BulkActionResponse(affected=0, failed=failed)

    # Use MongoDB bulk operations instead of individual queries
    if data.action == "activate":
        result = await Opportunity.find({"_id": {"$in": valid_ids}}).update_many(
            {"$set": {"is_active": True, "updated_at": utc_now()}}
        )
        affected = result.modified_count
    elif data.action == "deactivate":
        result = await Opportunity.find({"_id": {"$in": valid_ids}}).update_many(
            {"$set": {"is_active": False, "updated_at": utc_now()}}
        )
        affected = result.modified_count
    elif data.action == "delete":
        result = await Opportunity.find({"_id": {"$in": valid_ids}}).delete()
        affected = result.deleted_count
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {data.action}",
        )

    # Calculate failed based on requested vs affected
    failed += len(valid_ids) - affected

    logger.info(
        f"Admin {_admin.email} performed bulk {data.action} on {affected} opportunities",
        extra={"action": f"bulk_{data.action}", "admin_id": str(_admin.id), "affected": affected},
    )

    return BulkActionResponse(affected=affected, failed=failed)


# =============================================================================
# Users Endpoints
# =============================================================================


@admin_router.get("/users")
async def list_users(
    search: str | None = Query(None, description="Search by email", max_length=MAX_SEARCH_LENGTH),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """List all users (admin only)."""
    query: dict[str, Any] = {}

    if is_active is not None:
        query["is_active"] = is_active
    if search:
        # Escape regex to prevent NoSQL injection
        query["email"] = {"$regex": escape_regex(search), "$options": "i"}

    users = await User.find(query).skip(skip).limit(limit).to_list()
    total = await User.find(query).count()

    # Exclude password hashes from response
    users_safe = []
    for user in users:
        user_dict = user.model_dump()
        user_dict.pop("hashed_password", None)  # Safe removal
        users_safe.append(user_dict)

    return {
        "items": users_safe,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@admin_router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """Get user by ID (admin only)."""
    user = await get_or_404(User, user_id, "User")
    user_dict = user.model_dump()
    user_dict.pop("hashed_password", None)
    return user_dict


@admin_router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """Update a user (admin only)."""
    user = await get_or_404(User, user_id, "User")

    # Prevent admin from demoting themselves
    if str(user.id) == str(_admin.id) and data.is_superuser is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin",
        )

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = utc_now()

    for field, value in update_data.items():
        setattr(user, field, value)

    await user.save()

    logger.info(
        f"Admin {_admin.email} updated user {user.id}",
        extra={"action": "user_updated", "admin_id": str(_admin.id), "target_id": str(user.id)},
    )

    user_dict = user.model_dump()
    user_dict.pop("hashed_password", None)
    return user_dict


# =============================================================================
# Analytics Endpoints
# =============================================================================


@admin_router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    _admin: User = Depends(require_admin),
) -> AnalyticsOverview:
    """Get overview analytics (admin only)."""
    seven_days_ago = utc_now() - timedelta(days=7)

    # Run all counts in parallel for better performance
    (
        opportunity_count,
        user_count,
        match_count,
        pipeline_count,
        recent_signups,
        type_results,
    ) = await asyncio.gather(
        Opportunity.find().count(),
        User.find().count(),
        Match.find().count(),
        Pipeline.find().count(),
        User.find(User.created_at >= seven_days_ago).count(),
        Opportunity.aggregate([
            {"$group": {"_id": "$opportunity_type", "count": {"$sum": 1}}}
        ]).to_list(),
    )

    opportunities_by_type = {r["_id"]: r["count"] for r in type_results if r["_id"]}

    return AnalyticsOverview(
        opportunity_count=opportunity_count,
        user_count=user_count,
        match_count=match_count,
        pipeline_count=pipeline_count,
        opportunities_by_type=opportunities_by_type,
        recent_signups=recent_signups,
    )


# =============================================================================
# Crawlers Endpoints
# =============================================================================


@admin_router.get("/crawlers")
async def list_crawlers(
    _admin: User = Depends(require_admin),
) -> dict[str, list[CrawlerStatus]]:
    """List all crawlers with their status (admin only)."""
    # Get available scrapers dynamically from registry
    scrapers = ScraperRegistry.list_all()

    # Use aggregation to get all stats in ONE query instead of N*3 queries
    pipeline = [
        {"$match": {"scraper_name": {"$in": scrapers}}},
        {"$sort": {"started_at": -1}},
        {"$group": {
            "_id": "$scraper_name",
            "latest_run": {"$first": "$$ROOT"},
            "total_runs": {"$sum": 1},
            "success_runs": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
        }},
    ]
    results = await ScraperRun.aggregate(pipeline).to_list()

    # Build response from aggregation results
    stats_map = {r["_id"]: r for r in results}

    crawler_statuses = []
    for scraper_name in scrapers:
        stats = stats_map.get(scraper_name, {})
        total = stats.get("total_runs", 0)
        success = stats.get("success_runs", 0)
        latest = stats.get("latest_run")

        crawler_statuses.append(
            CrawlerStatus(
                name=scraper_name,
                last_run=latest["started_at"] if latest else None,
                last_status=latest["status"] if latest else None,
                total_runs=total,
                success_rate=round((success / total * 100) if total > 0 else 0, 1),
            )
        )

    return {"crawlers": crawler_statuses}


@admin_router.post("/crawlers/{scraper_name}/runs")
async def trigger_crawler_run(
    scraper_name: str,
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """Trigger a crawler run (admin only). Returns job ID for polling."""
    valid_scrapers = ScraperRegistry.list_all()

    if scraper_name not in valid_scrapers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scraper. Valid options: {valid_scrapers}",
        )

    # Check if a run is already in progress
    running = await ScraperRun.find(
        ScraperRun.scraper_name == scraper_name,
        ScraperRun.status == "running",
    ).first_or_none()

    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scraper '{scraper_name}' is already running",
        )

    # Create a new run record
    run = ScraperRun(
        scraper_name=scraper_name,
        status="pending",
        triggered_by=_admin.id,
    )
    await run.insert()

    logger.info(
        f"Admin {_admin.email} triggered crawler {scraper_name}",
        extra={"action": "crawler_triggered", "admin_id": str(_admin.id), "scraper_name": scraper_name},
    )

    # Note: Actual scraper execution would be handled by a background task
    # For now, we just create the record. The scheduler or a worker would pick it up.

    return {
        "job_id": str(run.id),
        "scraper_name": scraper_name,
        "status": "pending",
        "message": "Scraper run queued. Poll /crawlers/{name}/runs/{id} for status.",
    }


@admin_router.get("/crawlers/{scraper_name}/runs")
async def list_crawler_runs(
    scraper_name: str,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """List run history for a crawler (admin only)."""
    runs = await ScraperRun.find(
        ScraperRun.scraper_name == scraper_name
    ).sort("-started_at").skip(skip).limit(limit).to_list()

    total = await ScraperRun.find(ScraperRun.scraper_name == scraper_name).count()

    return {
        "items": runs,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@admin_router.get("/crawlers/{scraper_name}/runs/{run_id}")
async def get_crawler_run(
    scraper_name: str,
    run_id: str,
    _admin: User = Depends(require_admin),
) -> ScraperRun:
    """Get details of a specific crawler run (admin only)."""
    run = await get_or_404(ScraperRun, run_id, "Run")

    if run.scraper_name != scraper_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return run
