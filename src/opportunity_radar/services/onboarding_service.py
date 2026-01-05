"""Onboarding service for URL scraping and LLM-based profile extraction."""

import ipaddress
import json
import logging
import re
import socket
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI


class SSRFProtectionError(Exception):
    """Raised when a URL fails SSRF validation."""

    pass


def validate_url_for_ssrf(url: str) -> None:
    """
    Validate a URL to prevent Server-Side Request Forgery (SSRF) attacks.

    Raises:
        SSRFProtectionError: If the URL is potentially malicious
    """
    ALLOWED_SCHEMES = {"http", "https"}
    BLOCKED_IP_RANGES = [
        ipaddress.ip_network("127.0.0.0/8"),  # Localhost
        ipaddress.ip_network("10.0.0.0/8"),  # Private network
        ipaddress.ip_network("192.168.0.0/16"),  # Private network
        ipaddress.ip_network("172.16.0.0/12"),  # Private network
        ipaddress.ip_network("169.254.0.0/16"),  # Link-local (AWS metadata)
        ipaddress.ip_network("0.0.0.0/8"),  # Current network
        ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
        ipaddress.ip_network("::1/128"),  # IPv6 localhost
        ipaddress.ip_network("fc00::/7"),  # IPv6 private
        ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
    ]
    BLOCKED_HOSTNAMES = {
        "localhost",
        "metadata.google.internal",
        "metadata",
        "instance-data",
    }

    try:
        parsed = urlparse(url)
    except Exception:
        raise SSRFProtectionError("Invalid URL format")

    # Check scheme
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFProtectionError(f"URL scheme '{parsed.scheme}' not allowed. Use http or https.")

    # Check hostname exists
    hostname = parsed.hostname
    if not hostname:
        raise SSRFProtectionError("URL must have a valid hostname")

    # Check blocked hostnames
    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        raise SSRFProtectionError(f"Hostname '{hostname}' is not allowed")

    # Check for cloud metadata patterns
    if "169.254" in hostname or "metadata" in hostname_lower:
        raise SSRFProtectionError("Access to metadata endpoints is not allowed")

    # Resolve hostname to IP and check against blocked ranges
    try:
        # Get all IP addresses for the hostname
        addr_info = socket.getaddrinfo(hostname, parsed.port or 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
                for blocked_range in BLOCKED_IP_RANGES:
                    if ip in blocked_range:
                        raise SSRFProtectionError(f"Access to internal network ({ip}) is not allowed")
            except ValueError:
                continue  # Not a valid IP, skip
    except socket.gaierror:
        raise SSRFProtectionError(f"Could not resolve hostname: {hostname}")
    except SSRFProtectionError:
        raise
    except Exception as e:
        # Log but don't block on unexpected errors during resolution
        logging.getLogger(__name__).warning(f"URL validation warning for {url}: {e}")

from ..config import get_settings
from ..models.profile import Profile
from ..models.user import User
from ..schemas.onboarding import (
    ExtractedField,
    ExtractedProfile,
    OnboardingConfirmRequest,
    URLType,
)
from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

# Valid goals that map to opportunity types
VALID_GOALS = {"funding", "prizes", "learning", "networking", "exposure", "mentorship", "equity", "building"}

# Mapping for normalizing free-text goals to standard values
GOALS_NORMALIZATION_MAP = {
    # funding related
    "get_funding": "funding",
    "raise_money": "funding",
    "investment": "funding",
    "fundraising": "funding",
    "capital": "funding",
    "grant": "funding",
    "grants": "funding",
    # prizes related
    "win": "prizes",
    "win_hackathons": "prizes",
    "win_prizes": "prizes",
    "awards": "prizes",
    "competition": "prizes",
    "hackathon": "prizes",
    # learning related
    "learn": "learning",
    "learn_skills": "learning",
    "education": "learning",
    "skills": "learning",
    "grow": "learning",
    # networking related
    "network": "networking",
    "build_network": "networking",
    "connections": "networking",
    "community": "networking",
    "meet_people": "networking",
    # exposure related
    "visibility": "exposure",
    "marketing": "exposure",
    "brand": "exposure",
    "users": "exposure",
    "get_users": "exposure",
    "grow_users": "exposure",
    "customers": "exposure",
    # mentorship related
    "mentor": "mentorship",
    "guidance": "mentorship",
    "advice": "mentorship",
    # building related
    "build": "building",
    "create": "building",
    "ship": "building",
    "launch": "building",
    "product": "building",
}


def normalize_goals(goals: list[str]) -> list[str]:
    """Normalize free-text goals to standard values."""
    if not goals:
        return []

    normalized = set()
    for goal in goals:
        goal_lower = goal.lower().strip().replace(" ", "_")

        # Check if already a valid goal
        if goal_lower in VALID_GOALS:
            normalized.add(goal_lower)
        # Check if it maps to a valid goal
        elif goal_lower in GOALS_NORMALIZATION_MAP:
            normalized.add(GOALS_NORMALIZATION_MAP[goal_lower])
        # Try partial matching
        else:
            for key, value in GOALS_NORMALIZATION_MAP.items():
                if key in goal_lower or goal_lower in key:
                    normalized.add(value)
                    break

    return list(normalized)


class OnboardingService:
    """Service for onboarding flow with URL extraction."""

    MAX_REDIRECTS = 5  # Limit redirect hops to prevent loops

    def __init__(self):
        settings = get_settings()
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        # SECURITY: Disable automatic redirects to prevent SSRF bypass
        # Redirects are handled manually with SSRF validation on each hop
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=False,  # Manual redirect handling for SSRF safety
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    async def _safe_get(self, url: str) -> httpx.Response:
        """
        Perform a GET request with SSRF-safe redirect handling.

        Each redirect hop is validated against SSRF protection rules.

        Args:
            url: The URL to fetch

        Returns:
            The final response after following redirects

        Raises:
            SSRFProtectionError: If any URL in the redirect chain fails validation
            httpx.TooManyRedirects: If redirect limit is exceeded
        """
        current_url = url
        for _ in range(self.MAX_REDIRECTS):
            # Validate current URL for SSRF before making request
            validate_url_for_ssrf(current_url)

            response = await self.http_client.get(current_url)

            # Check if this is a redirect
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    return response  # No location header, return as-is

                # Handle relative redirects
                if location.startswith("/"):
                    parsed = urlparse(current_url)
                    current_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                else:
                    current_url = location

                # Validate redirect target (will raise SSRFProtectionError if blocked)
                # This prevents redirect-based SSRF bypasses
                continue

            return response

        raise httpx.TooManyRedirects(
            f"Exceeded maximum redirects ({self.MAX_REDIRECTS})",
            request=httpx.Request("GET", url),
        )

    def detect_url_type(self, url: str) -> URLType:
        """Detect if URL is a website or GitHub repo."""
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if "github.com" in host:
            return URLType.GITHUB_REPO
        return URLType.WEBSITE

    async def extract_profile_from_url(self, url: str) -> ExtractedProfile:
        """
        Extract profile information from a URL.

        Args:
            url: Website or GitHub repo URL

        Returns:
            ExtractedProfile with AI-extracted fields

        Raises:
            SSRFProtectionError: If the URL fails security validation
        """
        # Ensure URL has scheme for validation
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # SSRF protection: validate URL before any network requests
        validate_url_for_ssrf(url)

        url_type = self.detect_url_type(url)
        logger.info(f"Extracting profile from URL: {url}, type: {url_type}")

        if url_type == URLType.GITHUB_REPO:
            content = await self._scrape_github(url)
        else:
            content = await self._scrape_website(url)

        logger.info(f"Scraped content length: {len(content) if content else 0}")
        if content:
            logger.info(f"Content preview: {content[:200]}...")

        # Extract structured data using LLM
        extracted_data = await self._llm_extract(content, url_type)
        logger.info(f"LLM extracted data: {extracted_data}")

        return ExtractedProfile(
            url_type=url_type,
            source_url=url,
            company_name=extracted_data.get("company_name"),
            product_description=extracted_data.get("product_description"),
            tech_stack=extracted_data.get("tech_stack"),
            industries=extracted_data.get("industries"),
            team_size=extracted_data.get("team_size"),
            profile_type=extracted_data.get("profile_type"),
            location=extracted_data.get("location"),
            goals=extracted_data.get("goals"),
            raw_content_preview=content[:500] if content else None,
        )

    async def _scrape_website(self, url: str) -> str:
        """Scrape website content from main page and key subpages."""
        content_parts = []

        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            # Main page
            main_content = await self._fetch_page_text(url)
            if main_content:
                content_parts.append(f"MAIN PAGE:\n{main_content}")

            # Try common subpages
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            subpages = ["/about", "/about-us", "/team", "/product", "/products"]
            for subpage in subpages:
                try:
                    subpage_url = base_url + subpage
                    subpage_content = await self._fetch_page_text(subpage_url)
                    if subpage_content and len(subpage_content) > 100:
                        content_parts.append(f"{subpage.upper()} PAGE:\n{subpage_content}")
                        break  # Found a good subpage
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Error scraping website {url}: {e}")

        return "\n\n".join(content_parts)

    async def _fetch_page_text(self, url: str) -> Optional[str]:
        """Fetch and extract text from a single page."""
        try:
            response = await self._safe_get(url)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract metadata first (always useful)
            meta_parts = []

            # Get title
            title_tag = soup.find("title")
            if title_tag:
                meta_parts.append(f"Title: {title_tag.get_text(strip=True)}")

            # Get meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                meta_parts.append(f"Description: {meta_desc['content']}")

            # Get og:description
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                meta_parts.append(f"OG Description: {og_desc['content']}")

            # Get keywords
            keywords = soup.find("meta", attrs={"name": "keywords"})
            if keywords and keywords.get("content"):
                meta_parts.append(f"Keywords: {keywords['content']}")

            # Remove script and style elements for body text
            for element in soup(["script", "style", "noscript"]):
                element.decompose()

            # Get body text
            body_text = soup.get_text(separator=" ", strip=True)
            body_text = re.sub(r"\s+", " ", body_text)

            # Combine metadata with body text
            combined = "\n".join(meta_parts)
            if body_text:
                combined += f"\n\nPage Content: {body_text[:3000]}"

            # If still too short, try Playwright
            if len(combined) < 200:
                logger.info(f"Content too short ({len(combined)} chars), trying Playwright for {url}")
                playwright_text = await self._fetch_with_playwright(url)
                if playwright_text and len(playwright_text) > len(combined):
                    combined = "\n".join(meta_parts) + f"\n\nPage Content: {playwright_text}"

            return combined[:5000]

        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch page content using Playwright for JS-rendered sites."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait a bit for dynamic content
                await page.wait_for_timeout(3000)

                # Get text content from HTML attributes and visible text
                content = await page.evaluate("""
                    () => {
                        let parts = [];

                        // Get meta description
                        const metaDesc = document.querySelector('meta[name="description"]');
                        if (metaDesc) parts.push('Description: ' + metaDesc.content);

                        // Get all visible text from main content areas
                        const mainContent = document.querySelector('main, [role="main"], #root, .app, body');
                        if (mainContent) {
                            // Get inner text but filter out navigation
                            const clone = mainContent.cloneNode(true);
                            const navs = clone.querySelectorAll('nav, header, footer, script, style');
                            navs.forEach(el => el.remove());
                            parts.push(clone.innerText);
                        }

                        return parts.join('\\n');
                    }
                """)

                await browser.close()

                if content:
                    content = re.sub(r"\s+", " ", content.strip())
                    return content[:4000]

                return None

        except Exception as e:
            logger.warning(f"Playwright fetch failed for {url}: {e}")
            return None

    async def _scrape_github(self, url: str) -> str:
        """Scrape GitHub repo information via API."""
        content_parts = []

        try:
            # Parse owner/repo from URL
            parsed = urlparse(url)
            path_parts = parsed.path.strip("/").split("/")

            if len(path_parts) < 2:
                return "Invalid GitHub URL"

            owner, repo = path_parts[0], path_parts[1]

            # Fetch repo info via API
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = await self.http_client.get(api_url)

            if response.status_code == 200:
                repo_data = response.json()
                content_parts.append(f"REPOSITORY INFO:")
                content_parts.append(f"Name: {repo_data.get('name', '')}")
                content_parts.append(f"Description: {repo_data.get('description', '')}")
                content_parts.append(f"Language: {repo_data.get('language', '')}")
                content_parts.append(f"Stars: {repo_data.get('stargazers_count', 0)}")
                content_parts.append(f"Topics: {', '.join(repo_data.get('topics', []))}")

            # Fetch README
            readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            readme_response = await self.http_client.get(readme_url)

            if readme_response.status_code == 200:
                readme_data = readme_response.json()
                # README is base64 encoded
                import base64
                readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8")
                # Take first 3000 chars of README
                content_parts.append(f"\nREADME:\n{readme_content[:3000]}")

            # Fetch languages
            langs_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
            langs_response = await self.http_client.get(langs_url)

            if langs_response.status_code == 200:
                languages = list(langs_response.json().keys())
                content_parts.append(f"\nLanguages used: {', '.join(languages)}")

            # Try to fetch package.json or requirements.txt for dependencies
            for dep_file in ["package.json", "requirements.txt", "Cargo.toml", "go.mod"]:
                dep_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dep_file}"
                dep_response = await self.http_client.get(dep_url)
                if dep_response.status_code == 200:
                    dep_data = dep_response.json()
                    import base64
                    dep_content = base64.b64decode(dep_data.get("content", "")).decode("utf-8")
                    content_parts.append(f"\n{dep_file}:\n{dep_content[:1000]}")
                    break

        except Exception as e:
            logger.error(f"Error scraping GitHub {url}: {e}")

        return "\n".join(content_parts)

    async def _llm_extract(
        self, content: str, url_type: URLType
    ) -> dict[str, Optional[ExtractedField]]:
        """Use LLM to extract structured profile data from content."""

        if not content or len(content) < 50:
            return {}

        system_prompt = """You are an AI assistant that extracts structured profile information from website or GitHub content.

Extract the following fields if present:
- company_name: The company or project name
- product_description: What the product/project does (1-2 sentences)
- tech_stack: Technologies, frameworks, languages used (as a list)
- industries: Industries or domains (e.g., FinTech, HealthTech, AI/ML)
- team_size: Approximate team size if mentioned
- profile_type: One of: developer, startup, student, researcher, freelancer
- location: Country or region if mentioned
- goals: What they're trying to achieve. MUST be a list containing ONLY these values: funding, prizes, learning, networking, exposure, mentorship, equity, building. Map their goals to these categories.

For each field, provide:
- value: The extracted value (string, list, or number)
- confidence: How confident you are (0.0 to 1.0)
- source: Brief note about where you found this

Respond ONLY with valid JSON in this format:
{
  "company_name": {"value": "...", "confidence": 0.9, "source": "from page title"},
  "tech_stack": {"value": ["Python", "React"], "confidence": 0.8, "source": "from about page"},
  ...
}

If a field cannot be determined, omit it from the response."""

        user_prompt = f"""Extract profile information from this {url_type.value} content:

{content[:4000]}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)

            # Convert to ExtractedField objects
            extracted = {}
            for field_name, field_data in result_data.items():
                if isinstance(field_data, dict) and "value" in field_data:
                    extracted[field_name] = ExtractedField(
                        value=field_data["value"],
                        confidence=field_data.get("confidence", 0.5),
                        source=field_data.get("source", "LLM extraction"),
                    )

            return extracted

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            return {}

    async def confirm_profile(
        self,
        user: User,
        data: OnboardingConfirmRequest,
    ) -> Profile:
        """
        Create profile from confirmed onboarding data.

        Args:
            user: The current user
            data: Confirmed profile data

        Returns:
            Created Profile document
        """
        # Normalize goals to standard values
        normalized_goals = normalize_goals(data.goals) if data.goals else []

        # Check if profile already exists
        existing = await Profile.find_one(Profile.user_id == user.id)
        if existing:
            # Update existing profile
            existing.display_name = data.display_name
            existing.bio = data.bio
            existing.tech_stack = data.tech_stack
            existing.interests = data.interests
            existing.industries = data.industries or []
            existing.goals = normalized_goals
            existing.experience_level = data.experience_level
            existing.preferred_team_size_min = 1
            existing.preferred_team_size_max = data.team_size
            existing.location_country = data.location_country
            existing.location_region = data.location_region

            # Generate embedding
            embedding = self._generate_profile_embedding(data)
            if embedding:
                existing.embedding = embedding

            await existing.save()
            return existing

        # Create new profile
        profile = Profile(
            user_id=user.id,
            display_name=data.display_name,
            bio=data.bio,
            tech_stack=data.tech_stack,
            interests=data.interests,
            industries=data.industries or [],
            goals=normalized_goals,
            experience_level=data.experience_level,
            preferred_team_size_min=1,
            preferred_team_size_max=data.team_size,
            location_country=data.location_country,
            location_region=data.location_region,
        )

        # Generate embedding
        embedding = self._generate_profile_embedding(data)
        if embedding:
            profile.embedding = embedding

        await profile.insert()
        return profile

    def _generate_profile_embedding(
        self, data: OnboardingConfirmRequest
    ) -> Optional[list[float]]:
        """Generate embedding for profile."""
        try:
            embedding_service = get_embedding_service()
            embedding_text = embedding_service.create_profile_embedding_text(
                tech_stack=data.tech_stack,
                industries=data.industries,
                intents=data.goals,
                profile_type=data.profile_type,
            )
            return embedding_service.get_embedding(embedding_text)
        except Exception as e:
            logger.warning(f"Failed to generate profile embedding: {e}")
            return None

    async def get_onboarding_status(self, user: User) -> dict:
        """Check if user has completed onboarding."""
        profile = await Profile.find_one(Profile.user_id == user.id)

        # Check if profile exists and has meaningful data
        onboarding_completed = False
        if profile:
            # Profile is considered complete if it has at least tech_stack or goals filled
            has_tech_stack = profile.tech_stack and len(profile.tech_stack) > 0
            has_goals = profile.goals and len(profile.goals) > 0
            has_bio = profile.bio and len(profile.bio) > 0
            onboarding_completed = has_tech_stack or has_goals or has_bio

        return {
            "has_profile": profile is not None,
            "onboarding_completed": onboarding_completed,
            "profile_id": str(profile.id) if profile else None,
        }


# Singleton instance
_onboarding_service: Optional[OnboardingService] = None


def get_onboarding_service() -> OnboardingService:
    """Get or create the onboarding service singleton."""
    global _onboarding_service
    if _onboarding_service is None:
        _onboarding_service = OnboardingService()
    return _onboarding_service
