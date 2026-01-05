"""MongoDB database connection and initialization."""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from ..config import settings

# MongoDB client
client: AsyncIOMotorClient = None


async def init_db():
    """Initialize MongoDB connection and Beanie ODM."""
    global client
    client = AsyncIOMotorClient(settings.mongodb_url)

    # Import all document models
    from ..models.user import User
    from ..models.profile import Profile
    from ..models.opportunity import Opportunity, Host
    from ..models.match import Match
    from ..models.pipeline import Pipeline
    from ..models.material import Material
    from ..models.scraper_run import ScraperRun
    from ..models.notification import Notification, NotificationPreferences
    from ..models.team import Team
    from ..models.submission import OpportunitySubmission
    from ..models.shared_list import SharedList

    await init_beanie(
        database=client[settings.mongodb_database],
        document_models=[
            User,
            Profile,
            Host,
            Opportunity,
            Match,
            Pipeline,
            Material,
            ScraperRun,
            Notification,
            NotificationPreferences,
            Team,
            OpportunitySubmission,
            SharedList,
        ]
    )


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()


def get_database():
    """Get database instance."""
    return client[settings.mongodb_database]
