"""Service for handling user-submitted opportunities."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import re

from beanie import PydanticObjectId
from openai import OpenAI

from ..config import get_settings
from ..models.submission import OpportunitySubmission, SubmissionStatus
from ..models.opportunity import Opportunity, Host
from ..models.user import User

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class SubmissionService:
    """Service for managing user-submitted opportunities."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)

    async def create_submission(
        self,
        user: User,
        data: Dict[str, Any],
    ) -> OpportunitySubmission:
        """Create a new opportunity submission."""
        submission = OpportunitySubmission(
            submitted_by=user.id,
            submitter_email=user.email,
            **data,
        )
        await submission.insert()
        logger.info(f"New submission created: {submission.id} by {user.email}")
        return submission

    async def get_submission(
        self,
        submission_id: PydanticObjectId,
    ) -> Optional[OpportunitySubmission]:
        """Get a submission by ID."""
        return await OpportunitySubmission.get(submission_id)

    async def get_user_submissions(
        self,
        user_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[OpportunitySubmission], int]:
        """Get all submissions by a user."""
        query = OpportunitySubmission.find({"submitted_by": user_id})
        total = await query.count()
        submissions = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        return submissions, total

    async def get_pending_submissions(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[OpportunitySubmission], int]:
        """Get all pending submissions for admin review."""
        query = OpportunitySubmission.find({"status": "pending"})
        total = await query.count()
        submissions = await query.sort("created_at").skip(skip).limit(limit).to_list()
        return submissions, total

    async def get_all_submissions(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[OpportunitySubmission], int]:
        """Get all submissions with optional status filter."""
        query_filter = {}
        if status:
            query_filter["status"] = status

        query = OpportunitySubmission.find(query_filter)
        total = await query.count()
        submissions = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        return submissions, total

    async def update_submission(
        self,
        submission: OpportunitySubmission,
        data: Dict[str, Any],
    ) -> OpportunitySubmission:
        """Update a submission (by the submitter)."""
        # Only allow updates if pending or needs_info
        if submission.status not in ["pending", "needs_info"]:
            raise ValueError("Cannot update submission after it has been reviewed")

        for key, value in data.items():
            if value is not None and hasattr(submission, key):
                setattr(submission, key, value)

        submission.updated_at = _utc_now()
        await submission.save()
        return submission

    async def review_submission(
        self,
        submission: OpportunitySubmission,
        reviewer: User,
        status: SubmissionStatus,
        note: str,
    ) -> OpportunitySubmission:
        """Review a submission (admin action)."""
        submission.add_review_note(
            reviewer_id=reviewer.id,
            note=note,
            status_change=status,
        )
        submission.status = status
        submission.reviewed_by = reviewer.id
        submission.reviewed_at = _utc_now()
        submission.updated_at = _utc_now()

        await submission.save()
        logger.info(
            f"Submission {submission.id} reviewed by {reviewer.email}: {status}"
        )

        # If approved, create the opportunity
        if status == "approved":
            opportunity = await self._create_opportunity_from_submission(submission)
            submission.opportunity_id = opportunity.id
            await submission.save()

        return submission

    async def _create_opportunity_from_submission(
        self,
        submission: OpportunitySubmission,
    ) -> Opportunity:
        """Create an Opportunity from an approved submission."""
        # Find or create host
        host = await Host.find_one({"name": submission.host_name})
        if not host:
            slug = self._create_slug(submission.host_name)
            host = Host(
                name=submission.host_name,
                slug=slug,
                website_url=submission.host_website,
            )
            await host.insert()

        # Create unique external ID
        external_id = f"user_submitted_{submission.id}"
        slug = self._create_slug(submission.title)

        opportunity = Opportunity(
            host_id=host.id,
            external_id=external_id,
            title=submission.title,
            slug=slug,
            description=submission.description,
            opportunity_type=submission.opportunity_type,
            format=submission.format,
            location_type=submission.location_type,
            location_city=submission.location_city,
            location_country=submission.location_country,
            website_url=submission.website_url,
            logo_url=submission.logo_url,
            themes=submission.themes,
            technologies=submission.technologies,
            total_prize_value=submission.total_prize_value,
            currency=submission.currency,
            team_size_min=submission.team_size_min,
            team_size_max=submission.team_size_max,
            application_deadline=submission.application_deadline,
            event_start_date=submission.event_start_date,
            event_end_date=submission.event_end_date,
            social_links=submission.social_links,
            is_active=True,
            source_url=submission.website_url,
        )

        await opportunity.insert()
        logger.info(f"Created opportunity {opportunity.id} from submission {submission.id}")

        return opportunity

    def _create_slug(self, name: str) -> str:
        """Create a URL-friendly slug from a name."""
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")

    async def enhance_submission_with_ai(
        self,
        submission: OpportunitySubmission,
    ) -> Dict[str, Any]:
        """Use AI to suggest enhancements for a submission."""
        prompt = f"""Analyze this hackathon/opportunity submission and suggest improvements:

Title: {submission.title}
Description: {submission.description}
Type: {submission.opportunity_type}
Themes: {', '.join(submission.themes) if submission.themes else 'None specified'}
Technologies: {', '.join(submission.technologies) if submission.technologies else 'None specified'}

Please provide:
1. Suggested additional themes (comma-separated)
2. Suggested additional technologies (comma-separated)
3. A more compelling short description (max 200 chars)
4. Any missing information that should be added

Format your response as JSON with keys: suggested_themes, suggested_technologies, short_description, missing_info"""

        try:
            response = self.client.responses.create(
                model="gpt-5.2",
                input=prompt,
            )

            # Parse the response
            import json
            content = response.output_text or ""
            # Try to extract JSON from the response
            try:
                # Find JSON in the response
                json_match = re.search(r"\{[\s\S]*\}", content)
                if json_match:
                    suggestions = json.loads(json_match.group())
                else:
                    suggestions = {"raw_response": content}
            except json.JSONDecodeError:
                suggestions = {"raw_response": content}

            return suggestions

        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return {"error": str(e)}

    async def get_submission_stats(self) -> Dict[str, int]:
        """Get submission statistics."""
        total = await OpportunitySubmission.count()
        pending = await OpportunitySubmission.find({"status": "pending"}).count()
        approved = await OpportunitySubmission.find({"status": "approved"}).count()
        rejected = await OpportunitySubmission.find({"status": "rejected"}).count()
        needs_info = await OpportunitySubmission.find({"status": "needs_info"}).count()

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "needs_info": needs_info,
        }

    async def delete_submission(
        self,
        submission: OpportunitySubmission,
    ) -> None:
        """Delete a submission (only if pending)."""
        if submission.status != "pending":
            raise ValueError("Cannot delete a reviewed submission")

        await submission.delete()
        logger.info(f"Deleted submission {submission.id}")


# Singleton instance
_submission_service: Optional[SubmissionService] = None


def get_submission_service() -> SubmissionService:
    """Get or create the submission service singleton."""
    global _submission_service
    if _submission_service is None:
        _submission_service = SubmissionService()
    return _submission_service
