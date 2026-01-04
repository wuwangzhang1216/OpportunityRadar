#!/usr/bin/env python
"""Create or promote a user to admin (superuser)."""

import asyncio
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from src.opportunity_radar.models.user import User
from src.opportunity_radar.core.security import get_password_hash


async def create_admin(email: str, password: str = None):
    """Create a new admin user or promote an existing user to admin."""
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database = os.getenv("MONGODB_DATABASE", "opportunity_radar")

    client = AsyncIOMotorClient(mongodb_url)
    await init_beanie(database=client[mongodb_database], document_models=[User])

    try:
        # Check if user exists
        user = await User.find_one(User.email == email)

        if user:
            if user.is_superuser:
                print(f"User {email} is already an admin")
            else:
                user.is_superuser = True
                await user.save()
                print(f"Promoted {email} to admin")
        else:
            if not password:
                print("Error: Password is required when creating a new user")
                sys.exit(1)

            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                is_superuser=True,
                is_active=True,
            )
            await user.insert()
            print(f"Created admin user: {email}")

    finally:
        client.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_admin.py <email> [password]")
        print("")
        print("Examples:")
        print("  Create new admin:     python scripts/create_admin.py admin@example.com secretpass")
        print("  Promote existing:     python scripts/create_admin.py existing@example.com")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(create_admin(email, password))


if __name__ == "__main__":
    main()
