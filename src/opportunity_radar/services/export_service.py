"""Data export service for user data."""

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from beanie import PydanticObjectId

from ..models.user import User
from ..models.profile import Profile
from ..models.opportunity import Opportunity
from ..models.pipeline import Pipeline
from ..models.match import Match
from ..models.material import Material

logger = logging.getLogger(__name__)

ExportFormat = Literal["json", "csv"]


def _serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects for JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, PydanticObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [_serialize_datetime(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _serialize_datetime(v) for k, v in obj.items()}
    return obj


class ExportService:
    """Service for exporting user data."""

    async def export_user_data(
        self,
        user: User,
        include_profile: bool = True,
        include_matches: bool = True,
        include_pipelines: bool = True,
        include_materials: bool = True,
        format: ExportFormat = "json",
    ) -> tuple[str, str]:
        """
        Export all user data.

        Returns (content, filename)
        """
        data = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "user": await self._export_user_info(user),
        }

        if include_profile:
            data["profile"] = await self._export_profile(user.id)

        if include_matches:
            data["matches"] = await self._export_matches(user.id)

        if include_pipelines:
            data["pipelines"] = await self._export_pipelines(user.id)

        if include_materials:
            data["materials"] = await self._export_materials(user.id)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if format == "json":
            content = json.dumps(_serialize_datetime(data), indent=2, ensure_ascii=False)
            filename = f"opportunity_radar_export_{timestamp}.json"
        else:
            # For CSV, we flatten the data
            content = self._convert_to_csv(data)
            filename = f"opportunity_radar_export_{timestamp}.csv"

        return content, filename

    async def _export_user_info(self, user: User) -> Dict[str, Any]:
        """Export user account info (excluding sensitive data)."""
        return {
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at,
            "oauth_providers": [conn.provider for conn in user.oauth_connections],
        }

    async def _export_profile(self, user_id: PydanticObjectId) -> Optional[Dict[str, Any]]:
        """Export user profile."""
        profile = await Profile.find_one({"user_id": user_id})
        if not profile:
            return None

        return {
            "display_name": profile.display_name,
            "bio": profile.bio,
            "skills": profile.skills,
            "interests": profile.interests,
            "experience_level": profile.experience_level,
            "goals": profile.goals,
            "available_hours_per_week": profile.available_hours_per_week,
            "preferred_team_size": profile.preferred_team_size,
            "team_name": getattr(profile, "team_name", None),
            "company_stage": getattr(profile, "company_stage", None),
            "github_url": profile.github_url,
            "linkedin_url": profile.linkedin_url,
            "portfolio_url": profile.portfolio_url,
            "location": profile.location,
            "timezone": profile.timezone,
        }

    async def _export_matches(self, user_id: PydanticObjectId) -> List[Dict[str, Any]]:
        """Export user's opportunity matches."""
        # Find profile first
        profile = await Profile.find_one({"user_id": user_id})
        if not profile:
            return []

        matches = await Match.find({"profile_id": profile.id}).to_list()

        result = []
        for match in matches:
            # Get opportunity details
            opportunity = await Opportunity.get(match.opportunity_id)
            if opportunity:
                result.append({
                    "opportunity_title": opportunity.title,
                    "opportunity_type": opportunity.opportunity_type,
                    "score": match.score,
                    "status": match.status,
                    "feedback": match.feedback,
                    "matched_at": match.created_at,
                    "website_url": opportunity.website_url,
                    "application_deadline": opportunity.application_deadline,
                })

        return result

    async def _export_pipelines(self, user_id: PydanticObjectId) -> List[Dict[str, Any]]:
        """Export user's pipelines with opportunities."""
        pipelines = await Pipeline.find({"user_id": user_id}).to_list()

        result = []
        for pipeline in pipelines:
            pipeline_data = {
                "name": pipeline.name,
                "description": pipeline.description,
                "created_at": pipeline.created_at,
                "stages": [],
            }

            for stage in pipeline.stages:
                stage_data = {
                    "name": stage.name,
                    "opportunities": [],
                }

                for opp_id in stage.opportunity_ids:
                    opp = await Opportunity.get(opp_id)
                    if opp:
                        stage_data["opportunities"].append({
                            "title": opp.title,
                            "type": opp.opportunity_type,
                            "website_url": opp.website_url,
                            "deadline": opp.application_deadline,
                        })

                pipeline_data["stages"].append(stage_data)

            result.append(pipeline_data)

        return result

    async def _export_materials(self, user_id: PydanticObjectId) -> List[Dict[str, Any]]:
        """Export user's generated materials."""
        materials = await Material.find({"user_id": user_id}).to_list()

        return [
            {
                "material_type": mat.material_type,
                "title": mat.title,
                "content": mat.content,
                "created_at": mat.created_at,
            }
            for mat in materials
        ]

    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert export data to CSV format."""
        output = io.StringIO()

        # Export matches as the main CSV content
        if "matches" in data and data["matches"]:
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "opportunity_title",
                    "opportunity_type",
                    "score",
                    "status",
                    "feedback",
                    "matched_at",
                    "website_url",
                    "application_deadline",
                ],
                extrasaction="ignore",
            )
            writer.writeheader()

            for match in data["matches"]:
                row = {k: _serialize_datetime(v) for k, v in match.items()}
                writer.writerow(row)

        return output.getvalue()

    async def export_opportunities(
        self,
        opportunity_ids: List[PydanticObjectId],
        format: ExportFormat = "json",
    ) -> tuple[str, str]:
        """Export a list of opportunities."""
        opportunities = []
        for opp_id in opportunity_ids:
            opp = await Opportunity.get(opp_id)
            if opp:
                opportunities.append({
                    "id": str(opp.id),
                    "title": opp.title,
                    "description": opp.description,
                    "opportunity_type": opp.opportunity_type,
                    "format": opp.format,
                    "website_url": opp.website_url,
                    "location_city": opp.location_city,
                    "location_country": opp.location_country,
                    "themes": opp.themes,
                    "technologies": opp.technologies,
                    "total_prize_value": opp.total_prize_value,
                    "currency": opp.currency,
                    "application_deadline": opp.application_deadline,
                    "event_start_date": opp.event_start_date,
                    "event_end_date": opp.event_end_date,
                    "team_size_min": opp.team_size_min,
                    "team_size_max": opp.team_size_max,
                })

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if format == "json":
            content = json.dumps(
                _serialize_datetime(opportunities), indent=2, ensure_ascii=False
            )
            filename = f"opportunities_export_{timestamp}.json"
        else:
            output = io.StringIO()
            if opportunities:
                writer = csv.DictWriter(
                    output,
                    fieldnames=list(opportunities[0].keys()),
                    extrasaction="ignore",
                )
                writer.writeheader()
                for opp in opportunities:
                    row = {}
                    for k, v in opp.items():
                        if isinstance(v, list):
                            row[k] = "; ".join(str(item) for item in v)
                        elif isinstance(v, datetime):
                            row[k] = v.isoformat()
                        else:
                            row[k] = v
                    writer.writerow(row)

            content = output.getvalue()
            filename = f"opportunities_export_{timestamp}.csv"

        return content, filename

    async def export_pipeline_opportunities(
        self,
        pipeline_id: PydanticObjectId,
        format: ExportFormat = "json",
    ) -> tuple[str, str]:
        """Export all opportunities in a pipeline."""
        pipeline = await Pipeline.get(pipeline_id)
        if not pipeline:
            raise ValueError("Pipeline not found")

        opportunity_ids = []
        for stage in pipeline.stages:
            opportunity_ids.extend(stage.opportunity_ids)

        return await self.export_opportunities(opportunity_ids, format)


# Singleton instance
_export_service: Optional[ExportService] = None


def get_export_service() -> ExportService:
    """Get or create the export service singleton."""
    global _export_service
    if _export_service is None:
        _export_service = ExportService()
    return _export_service
