"""Admin API router with all admin endpoints."""

import csv
import io
import json
import logging
from datetime import datetime
from typing import List, Literal, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

from ....core.security import require_admin
from ....models.opportunity import Opportunity
from ....models.user import User
from ....models.match import Match
from ....models.pipeline import Pipeline
from ....models.scraper_run import ScraperRun

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# =============================================================================
# Schemas
# =============================================================================


class OpportunityCreate(BaseModel):
    """Schema for creating an opportunity."""

    external_id: str
    title: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    opportunity_type: str = "hackathon"
    format: Optional[str] = None
    location_type: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    website_url: Optional[str] = None
    registration_url: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    total_prize_value: Optional[float] = None
    currency: str = "USD"
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    is_featured: bool = False
    is_active: bool = True


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity (partial update)."""

    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    opportunity_type: Optional[str] = None
    format: Optional[str] = None
    location_type: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    website_url: Optional[str] = None
    registration_url: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    themes: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    total_prize_value: Optional[float] = None
    currency: Optional[str] = None
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


class BulkActionRequest(BaseModel):
    """Schema for bulk actions on opportunities."""

    action: Literal["activate", "deactivate", "delete"]
    ids: List[str]


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""

    affected: int
    failed: int


class ImportResponse(BaseModel):
    """Response for bulk import."""

    imported: int
    failed: int
    skipped: int
    errors: List[dict]


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    full_name: Optional[str] = None


class AnalyticsOverview(BaseModel):
    """Analytics overview response."""

    opportunity_count: int
    user_count: int
    match_count: int
    pipeline_count: int
    opportunities_by_type: dict
    recent_signups: int


class CrawlerStatus(BaseModel):
    """Status of a crawler."""

    name: str
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    total_runs: int
    success_rate: float


# =============================================================================
# Opportunities Endpoints
# =============================================================================


@admin_router.get("/opportunities")
async def list_opportunities(
    category: Optional[str] = Query(None, description="Filter by opportunity type"),
    search: Optional[str] = Query(None, description="Search in title"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
):
    """List all opportunities with filters (admin only)."""
    query = {}

    if category:
        query["opportunity_type"] = category
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["title"] = {"$regex": search, "$options": "i"}

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
):
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
        "admin_action",
        extra={
            "action": "opportunity_created",
            "admin_id": str(_admin.id),
            "admin_email": _admin.email,
            "target_id": str(opportunity.id),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return opportunity


@admin_router.get("/opportunities/{opportunity_id}")
async def get_opportunity(
    opportunity_id: str,
    _admin: User = Depends(require_admin),
):
    """Get opportunity by ID (admin only)."""
    try:
        opportunity = await Opportunity.get(PydanticObjectId(opportunity_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    return opportunity


@admin_router.patch("/opportunities/{opportunity_id}")
async def update_opportunity(
    opportunity_id: str,
    data: OpportunityUpdate,
    _admin: User = Depends(require_admin),
):
    """Update an opportunity (partial update, admin only)."""
    try:
        opportunity = await Opportunity.get(PydanticObjectId(opportunity_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(opportunity, field, value)

    await opportunity.save()

    logger.info(
        "admin_action",
        extra={
            "action": "opportunity_updated",
            "admin_id": str(_admin.id),
            "admin_email": _admin.email,
            "target_id": str(opportunity.id),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return opportunity


@admin_router.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: str,
    hard: bool = Query(False, description="Perform hard delete instead of soft delete"),
    _admin: User = Depends(require_admin),
):
    """Delete an opportunity (soft delete by default, admin only)."""
    try:
        opportunity = await Opportunity.get(PydanticObjectId(opportunity_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if hard:
        await opportunity.delete()
        action = "opportunity_hard_deleted"
    else:
        opportunity.is_active = False
        opportunity.updated_at = datetime.utcnow()
        await opportunity.save()
        action = "opportunity_soft_deleted"

    logger.info(
        "admin_action",
        extra={
            "action": action,
            "admin_id": str(_admin.id),
            "admin_email": _admin.email,
            "target_id": str(opportunity_id),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return {"ok": True, "action": action}


@admin_router.post("/opportunities/import", response_model=ImportResponse)
async def import_opportunities(
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin),
):
    """Bulk import opportunities from CSV or JSON file (admin only)."""
    content = await file.read()
    content_str = content.decode("utf-8")

    imported = 0
    failed = 0
    skipped = 0
    errors = []

    # Determine file type and parse
    if file.filename.endswith(".json"):
        try:
            data = json.loads(content_str)
            if not isinstance(data, list):
                data = [data]
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON: {str(e)}",
            )
    elif file.filename.endswith(".csv"):
        try:
            reader = csv.DictReader(io.StringIO(content_str))
            data = list(reader)
        except csv.Error as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CSV: {str(e)}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be .json or .csv",
        )

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
            existing = await Opportunity.find_one(
                Opportunity.external_id == row["external_id"]
            )
            if existing:
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
            await opportunity.insert()
            imported += 1

        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
            failed += 1

    logger.info(
        "admin_action",
        extra={
            "action": "opportunities_imported",
            "admin_id": str(_admin.id),
            "admin_email": _admin.email,
            "imported": imported,
            "failed": failed,
            "skipped": skipped,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return ImportResponse(imported=imported, failed=failed, skipped=skipped, errors=errors)


@admin_router.post("/opportunities/bulk-action", response_model=BulkActionResponse)
async def bulk_action_opportunities(
    data: BulkActionRequest,
    _admin: User = Depends(require_admin),
):
    """Perform bulk actions on opportunities (admin only)."""
    affected = 0
    failed = 0

    for opp_id in data.ids:
        try:
            opportunity = await Opportunity.get(PydanticObjectId(opp_id))
            if not opportunity:
                failed += 1
                continue

            if data.action == "activate":
                opportunity.is_active = True
                opportunity.updated_at = datetime.utcnow()
                await opportunity.save()
            elif data.action == "deactivate":
                opportunity.is_active = False
                opportunity.updated_at = datetime.utcnow()
                await opportunity.save()
            elif data.action == "delete":
                await opportunity.delete()

            affected += 1
        except Exception:
            failed += 1

    logger.info(
        "admin_action",
        extra={
            "action": f"bulk_{data.action}",
            "admin_id": str(_admin.id),
            "admin_email": _admin.email,
            "affected": affected,
            "failed": failed,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return BulkActionResponse(affected=affected, failed=failed)


# =============================================================================
# Users Endpoints
# =============================================================================


@admin_router.get("/users")
async def list_users(
    search: Optional[str] = Query(None, description="Search by email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
):
    """List all users (admin only)."""
    query = {}

    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["email"] = {"$regex": search, "$options": "i"}

    users = await User.find(query).skip(skip).limit(limit).to_list()
    total = await User.find(query).count()

    # Exclude password hashes from response
    users_safe = []
    for user in users:
        user_dict = user.model_dump()
        del user_dict["hashed_password"]
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
):
    """Get user by ID (admin only)."""
    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_dict = user.model_dump()
    del user_dict["hashed_password"]
    return user_dict


@admin_router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    _admin: User = Depends(require_admin),
):
    """Update a user (admin only)."""
    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from demoting themselves
    if str(user.id) == str(_admin.id) and data.is_superuser is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin",
        )

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(user, field, value)

    await user.save()

    logger.info(
        "admin_action",
        extra={
            "action": "user_updated",
            "admin_id": str(_admin.id),
            "admin_email": _admin.email,
            "target_id": str(user.id),
            "changes": list(update_data.keys()),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    user_dict = user.model_dump()
    del user_dict["hashed_password"]
    return user_dict


# =============================================================================
# Analytics Endpoints
# =============================================================================


@admin_router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    _admin: User = Depends(require_admin),
):
    """Get overview analytics (admin only)."""
    opportunity_count = await Opportunity.find().count()
    user_count = await User.find().count()
    match_count = await Match.find().count()
    pipeline_count = await Pipeline.find().count()

    # Opportunities by type
    pipeline = [
        {"$group": {"_id": "$opportunity_type", "count": {"$sum": 1}}},
    ]
    type_results = await Opportunity.aggregate(pipeline).to_list()
    opportunities_by_type = {r["_id"]: r["count"] for r in type_results if r["_id"]}

    # Recent signups (last 7 days)
    from datetime import timedelta

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_signups = await User.find(User.created_at >= seven_days_ago).count()

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
):
    """List all crawlers with their status (admin only)."""
    # Get available scrapers
    scrapers = ["devpost", "mlh", "ethglobal", "kaggle", "hackerearth"]

    crawler_statuses = []
    for scraper_name in scrapers:
        # Get latest run for this scraper
        latest_run = await ScraperRun.find(
            ScraperRun.scraper_name == scraper_name
        ).sort("-started_at").first_or_none()

        # Get total runs and success rate
        total_runs = await ScraperRun.find(ScraperRun.scraper_name == scraper_name).count()
        success_runs = await ScraperRun.find(
            ScraperRun.scraper_name == scraper_name,
            ScraperRun.status == "success",
        ).count()

        success_rate = (success_runs / total_runs * 100) if total_runs > 0 else 0

        crawler_statuses.append(
            CrawlerStatus(
                name=scraper_name,
                last_run=latest_run.started_at if latest_run else None,
                last_status=latest_run.status if latest_run else None,
                total_runs=total_runs,
                success_rate=round(success_rate, 1),
            )
        )

    return {"crawlers": crawler_statuses}


@admin_router.post("/crawlers/{scraper_name}/runs")
async def trigger_crawler_run(
    scraper_name: str,
    _admin: User = Depends(require_admin),
):
    """Trigger a crawler run (admin only). Returns job ID for polling."""
    valid_scrapers = ["devpost", "mlh", "ethglobal", "kaggle", "hackerearth"]

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
        "admin_action",
        extra={
            "action": "crawler_triggered",
            "admin_id": str(_admin.id),
            "admin_email": _admin.email,
            "scraper_name": scraper_name,
            "run_id": str(run.id),
            "timestamp": datetime.utcnow().isoformat(),
        },
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
):
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
):
    """Get details of a specific crawler run (admin only)."""
    try:
        run = await ScraperRun.get(PydanticObjectId(run_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if not run or run.scraper_name != scraper_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return run
