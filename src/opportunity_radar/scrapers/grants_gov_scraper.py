"""Grants.gov scraper for US federal funding opportunities."""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional

from .base import BaseScraper, RawOpportunity, ScraperResult, ScraperStatus, with_retry

logger = logging.getLogger(__name__)


class GrantsGovScraper(BaseScraper):
    """
    Scraper for Grants.gov - US federal grant opportunities.

    Grants.gov is the central portal for federal grant funding in the United States.
    Uses the public search API for data retrieval.
    """

    # Funding categories relevant to tech/innovation
    TECH_CATEGORIES = [
        "ST",  # Science and Technology
        "RD",  # Research and Development
        "ED",  # Education
        "BC",  # Business and Commerce
        "O",   # Other
    ]

    def __init__(self, categories: Optional[List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.categories = categories or self.TECH_CATEGORIES
        # New Grants.gov REST API (launched 2025)
        self._api_base = "https://api.grants.gov/v1/api/search2"

    @property
    def source_name(self) -> str:
        return "grants_gov"

    @property
    def base_url(self) -> str:
        return "https://www.grants.gov"

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape grant opportunities from Grants.gov API."""
        client = await self.get_client()
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            # New Grants.gov search2 API (2025) - POST with JSON body
            # API docs: https://grants.gov/api/api-guide
            search_params = {
                "keyword": "research",  # Simple keyword - API doesn't support OR syntax
                "oppStatuses": "posted",  # Only posted opportunities
                "rows": 50,
                "startRecordNum": (page - 1) * 50,
            }

            response = await client.post(
                self._api_base,
                json=search_params,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                logger.warning(f"Grants.gov API returned {response.status_code}, trying alternative endpoint")
                # Try alternative fetch endpoint
                return await self._scrape_alternative(page)

            data = response.json()

            # API returns: { "errorcode": 0, "msg": "...", "data": { "oppHits": [...] } }
            if data.get("errorcode") != 0:
                logger.warning(f"Grants.gov API error: {data.get('msg')}")
                return await self._scrape_alternative(page)

            # Extract oppHits from nested data structure
            inner_data = data.get("data", {})
            grants = inner_data.get("oppHits", [])

            logger.info(f"Grants.gov returned {len(grants)} opportunities (total: {inner_data.get('hitCount', 0)})")

            for grant in grants:
                try:
                    opp = self._parse_grant(grant)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse grant: {e}")
                    logger.warning(f"Failed to parse grant: {e}")

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page, "total_hits": data.get("hitCount", 0)},
            )

        except Exception as e:
            logger.error(f"Grants.gov scraping failed: {e}")
            return await self._scrape_alternative(page)

    async def _scrape_alternative(self, page: int = 1) -> ScraperResult:
        """Alternative scraping using fetchOpportunity or direct HTML."""
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            client = await self.get_client()

            # Try the grants.gov search page with query params
            search_url = f"https://www.grants.gov/search-grants.html?fundingCategories=ST,RD&oppStatuses=posted,forecasted"

            response = await client.get(search_url)

            if response.status_code == 200:
                # Parse HTML for grant listings
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "lxml")

                # Look for grant cards/rows
                grant_elements = soup.select("[class*='opportunity'], [class*='grant'], tr[data-opportunity]")

                for elem in grant_elements[:50]:
                    try:
                        opp = self._parse_html_grant(elem)
                        if opp:
                            opportunities.append(opp)
                    except Exception as e:
                        errors.append(str(e))

            # If still no results, return known tech/innovation grants
            if not opportunities and page == 1:
                opportunities = self._get_known_grants()

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.PARTIAL if opportunities else ScraperStatus.FAILED,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page, "fallback": True},
            )

        except Exception as e:
            logger.error(f"Grants.gov alternative scraping failed: {e}")
            if page == 1:
                return ScraperResult(
                    opportunities=self._get_known_grants(),
                    status=ScraperStatus.PARTIAL,
                    source=self.source_name,
                    total_found=len(self._get_known_grants()),
                    error_message=str(e),
                )
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.FAILED,
                source=self.source_name,
                error_message=str(e),
            )

    def _parse_html_grant(self, element) -> Optional[RawOpportunity]:
        """Parse grant from HTML element."""
        try:
            title_elem = element.select_one("a, h3, h4, .title")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")
            url = href if href.startswith("http") else f"https://www.grants.gov{href}"

            # Extract ID
            external_id = url.split("/")[-1] if "/" in url else title[:30].replace(" ", "-")

            return RawOpportunity(
                source=self.source_name,
                external_id=f"grants-gov-{external_id}",
                title=title,
                url=url,
                description=f"Federal grant: {title}",
                location="United States",
                is_online=True,
                regions=["US"],
                tags=["grants.gov", "federal-grant"],
                themes=["government-funding"],
                host_name="US Federal Government",
                host_url="https://www.grants.gov",
            )
        except Exception:
            return None

    def _get_known_grants(self) -> List[RawOpportunity]:
        """Return known federal grant programs for tech/innovation."""
        known_grants = [
            {
                "id": "nsf-career",
                "title": "NSF CAREER Award",
                "agency": "National Science Foundation",
                "description": "Faculty Early Career Development Program supporting early-career faculty. Awards ~$500K-$800K over 5 years.",
                "amount": 600000,
            },
            {
                "id": "nsf-sbir",
                "title": "NSF SBIR/STTR Program",
                "agency": "National Science Foundation",
                "description": "Small business innovation research funding. Phase I up to $275K, Phase II up to $1M.",
                "amount": 275000,
            },
            {
                "id": "doe-arpa-e",
                "title": "ARPA-E Funding Opportunities",
                "agency": "Department of Energy",
                "description": "Advanced Research Projects Agency-Energy supports high-risk, high-reward energy research.",
                "amount": 3000000,
            },
            {
                "id": "nih-r01",
                "title": "NIH R01 Research Project Grant",
                "agency": "National Institutes of Health",
                "description": "Primary NIH mechanism for health-related research. Typically $250K-$500K per year.",
                "amount": 500000,
            },
            {
                "id": "darpa-young-faculty",
                "title": "DARPA Young Faculty Award",
                "agency": "Defense Advanced Research Projects Agency",
                "description": "Supporting rising research stars in defense-related science. Up to $500K over 2 years.",
                "amount": 500000,
            },
            {
                "id": "nasa-roses",
                "title": "NASA ROSES Research Opportunities",
                "agency": "NASA",
                "description": "Research Opportunities in Space and Earth Sciences. Various funding levels.",
                "amount": 300000,
            },
            {
                "id": "usda-nifa",
                "title": "USDA NIFA Competitive Grants",
                "agency": "USDA National Institute of Food and Agriculture",
                "description": "Agricultural research, education, and extension grants.",
                "amount": 500000,
            },
            {
                "id": "noaa-research",
                "title": "NOAA Research Grants",
                "agency": "National Oceanic and Atmospheric Administration",
                "description": "Climate, weather, ocean, and coastal research funding.",
                "amount": 200000,
            },
            {
                "id": "ed-ies",
                "title": "IES Research Grants",
                "agency": "Institute of Education Sciences",
                "description": "Education research, development, and evaluation grants.",
                "amount": 400000,
            },
            {
                "id": "dhs-science",
                "title": "DHS Science and Technology Grants",
                "agency": "Department of Homeland Security",
                "description": "Homeland security research and development funding.",
                "amount": 500000,
            },
        ]

        return [
            RawOpportunity(
                source=self.source_name,
                external_id=f"grants-gov-{g['id']}",
                title=g["title"],
                url=f"https://www.grants.gov/search-grants.html?agencyCode={g['agency'].split()[0].upper()}",
                description=g["description"],
                location="United States",
                is_online=True,
                regions=["US", "United States"],
                total_prize_amount=g["amount"],
                prize_currency="USD",
                tags=["grants.gov", "federal-grant", "us-government", "research"],
                themes=["government-funding", "federal-grants", "research"],
                host_name=g["agency"],
                host_url="https://www.grants.gov",
            )
            for g in known_grants
        ]

    def _parse_grant(self, data: dict) -> Optional[RawOpportunity]:
        """Parse a grant opportunity from API response."""
        try:
            # New API fields: id, number, title, agencyCode, agency, openDate, closeDate, oppStatus, docType, cfdaList
            opp_id = data.get("id") or data.get("number") or data.get("oppNum")
            if not opp_id:
                return None

            title = data.get("title", "Untitled Grant")

            # Build URL - new format uses opportunity ID
            url = f"https://www.grants.gov/search-results-detail/{opp_id}"

            # Parse dates (format: MM/DD/YYYY)
            close_date = data.get("closeDate")
            open_date = data.get("openDate")

            # Parse award info (may not be in list view)
            award_ceiling = data.get("awardCeiling")
            award_floor = data.get("awardFloor")
            total_funding = data.get("estimatedTotalProgramFunding")

            # Determine prize amount (use ceiling or total funding)
            prize_amount = None
            if award_ceiling:
                try:
                    prize_amount = float(str(award_ceiling).replace(",", "").replace("$", ""))
                except ValueError:
                    pass
            elif total_funding:
                try:
                    prize_amount = float(str(total_funding).replace(",", "").replace("$", ""))
                except ValueError:
                    pass

            # Get agency name (new API uses 'agency', old used 'agencyName')
            agency_name = data.get("agency") or data.get("agencyName", "US Federal Government")

            # Build description
            description_parts = []
            if data.get("synopsis"):
                description_parts.append(data["synopsis"])
            description_parts.append(f"Agency: {agency_name}")
            opp_number = data.get("number", "")
            if opp_number:
                description_parts.append(f"Opportunity Number: {opp_number}")
            if award_ceiling and award_floor:
                description_parts.append(f"Award Range: ${award_floor:,} - ${award_ceiling:,}")

            description = "\n".join(description_parts) if description_parts else f"Federal grant opportunity: {title}"

            # Parse eligibility
            eligibility = data.get("eligibilities", "")
            eligibility_rules = []
            if eligibility:
                eligibility_rules.append({"type": "eligibility", "value": eligibility})

            # Tags based on category
            tags = ["grants.gov", "federal-grant", "us-government"]
            category = data.get("fundingCategory", "")
            if category:
                tags.append(category.lower().replace(" ", "-"))

            cfda = data.get("cfdaList", [])
            if cfda:
                tags.append("cfda")

            # Themes
            themes = ["government-funding", "federal-grants"]
            agency = data.get("agencyCode", "").lower()
            if "nsf" in agency:
                themes.append("research")
                themes.append("science")
            elif "doe" in agency:
                themes.append("energy")
            elif "nih" in agency:
                themes.append("health")
                themes.append("research")
            elif "darpa" in agency or "dod" in agency:
                themes.append("defense")
                themes.append("innovation")

            return RawOpportunity(
                source=self.source_name,
                external_id=f"grants-gov-{opp_id}",
                title=title,
                url=url,
                description=description[:3000] if description else None,
                start_date=open_date,
                end_date=close_date,
                submission_deadline=close_date,
                location="United States",
                is_online=True,
                regions=["US", "United States"],
                total_prize_amount=prize_amount,
                prize_currency="USD",
                tags=tags,
                themes=themes,
                host_name=agency_name,
                host_url="https://www.grants.gov",
                eligibility_rules=eligibility_rules,
                raw_data=data,
            )

        except Exception as e:
            logger.warning(f"Failed to parse Grants.gov opportunity: {e}")
            return None

    @with_retry(max_attempts=3)
    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed grant information using fetchOpportunity API."""
        # Extract grant ID from external_id (format: grants-gov-{id})
        grant_id = external_id.replace("grants-gov-", "")

        try:
            # Try to convert to numeric ID for API
            try:
                opp_id = int(grant_id)
            except ValueError:
                logger.warning(f"Invalid grant ID format: {grant_id}")
                return None

            client = await self.get_client()

            # New Grants.gov fetchOpportunity API (2025)
            fetch_url = "https://api.grants.gov/v1/api/fetchOpportunity"

            response = await client.post(
                fetch_url,
                json={"opportunityId": opp_id},
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.warning(f"Grants.gov fetchOpportunity returned {response.status_code}")
                return None

            result = response.json()

            # Check for API errors
            if result.get("errorcode") != 0:
                logger.warning(f"Grants.gov API error: {result.get('msg')}")
                return None

            data = result.get("data", {})
            if not data:
                return None

            return self._parse_detailed_grant(data, url)

        except Exception as e:
            logger.error(f"Failed to scrape Grants.gov detail for {grant_id}: {e}")
            return None

    def _parse_detailed_grant(self, data: dict, url: str) -> Optional[RawOpportunity]:
        """Parse detailed grant data from fetchOpportunity API response."""
        try:
            opp_id = data.get("id") or data.get("opportunityNumber")
            if not opp_id:
                return None

            title = data.get("opportunityTitle", "Untitled Grant")
            opp_number = data.get("opportunityNumber", "")

            # Get synopsis data (contains most details)
            synopsis = data.get("synopsis", {}) or {}

            # Build comprehensive description
            description_parts = []

            # Synopsis description
            if synopsis.get("synopsisDesc"):
                description_parts.append(synopsis["synopsisDesc"])

            # Agency info
            agency_name = synopsis.get("agencyName") or data.get("owningAgencyCode", "US Federal Government")
            if agency_name:
                description_parts.append(f"\n\n**Agency:** {agency_name}")

            # Opportunity number
            if opp_number:
                description_parts.append(f"**Opportunity Number:** {opp_number}")

            # Funding details
            award_ceiling = data.get("awardCeiling") or synopsis.get("awardCeiling")
            award_floor = data.get("awardFloor") or synopsis.get("awardFloor")
            estimated_funding = synopsis.get("estimatedTotalProgramFunding")
            expected_awards = synopsis.get("expectedNumberOfAwards")

            if award_ceiling or award_floor:
                funding_range = []
                if award_floor:
                    funding_range.append(f"${award_floor:,.0f}" if isinstance(award_floor, (int, float)) else f"${award_floor}")
                if award_ceiling:
                    funding_range.append(f"${award_ceiling:,.0f}" if isinstance(award_ceiling, (int, float)) else f"${award_ceiling}")
                description_parts.append(f"**Award Range:** {' - '.join(funding_range)}")

            if estimated_funding:
                try:
                    est = float(str(estimated_funding).replace(",", "").replace("$", ""))
                    description_parts.append(f"**Estimated Total Funding:** ${est:,.0f}")
                except ValueError:
                    description_parts.append(f"**Estimated Total Funding:** {estimated_funding}")

            if expected_awards:
                description_parts.append(f"**Expected Awards:** {expected_awards}")

            # Cost sharing requirement
            cost_sharing = data.get("costSharing") or synopsis.get("costSharingOrMatchingRequirement")
            if cost_sharing:
                description_parts.append(f"**Cost Sharing Required:** {'Yes' if cost_sharing else 'No'}")

            # Eligibility
            applicant_types = data.get("applicantTypes", [])
            if applicant_types:
                eligible = [at.get("description", at.get("id", "")) for at in applicant_types if at]
                if eligible:
                    description_parts.append(f"\n\n**Eligible Applicants:**\n" + "\n".join(f"• {e}" for e in eligible[:10]))

            # Funding instruments
            funding_instruments = data.get("fundingInstruments", [])
            if funding_instruments:
                instruments = [fi.get("description", "") for fi in funding_instruments if fi]
                if instruments:
                    description_parts.append(f"\n\n**Funding Type:** {', '.join(instruments)}")

            # Contact info
            contact_name = synopsis.get("agencyContactName")
            contact_email = synopsis.get("agencyContactEmail")
            contact_phone = synopsis.get("agencyContactPhone")
            if contact_name or contact_email:
                contact_parts = []
                if contact_name:
                    contact_parts.append(contact_name)
                if contact_email:
                    contact_parts.append(contact_email)
                if contact_phone:
                    contact_parts.append(contact_phone)
                description_parts.append(f"\n\n**Contact:** {' | '.join(contact_parts)}")

            description = "\n".join(description_parts) if description_parts else f"Federal grant opportunity: {title}"

            # Parse dates
            close_date = synopsis.get("responseDate") or synopsis.get("applicationsDueDate")
            open_date = data.get("postingDate") or synopsis.get("postingDate")

            # Parse award amount for prize field
            prize_amount = None
            if award_ceiling:
                try:
                    prize_amount = float(str(award_ceiling).replace(",", "").replace("$", ""))
                except ValueError:
                    pass
            elif estimated_funding:
                try:
                    prize_amount = float(str(estimated_funding).replace(",", "").replace("$", ""))
                except ValueError:
                    pass

            # Tags
            tags = ["grants.gov", "federal-grant", "us-government"]
            category = data.get("opportunityCategory", {})
            if isinstance(category, dict) and category.get("description"):
                tags.append(category["description"].lower().replace(" ", "-"))

            # Funding categories
            funding_categories = data.get("fundingActivityCategories", [])
            for fc in funding_categories:
                if fc and fc.get("description"):
                    tags.append(fc["description"].lower().replace(" ", "-"))

            # Themes based on agency
            themes = ["government-funding", "federal-grants"]
            agency_code = data.get("owningAgencyCode", "").lower()
            if "nsf" in agency_code:
                themes.extend(["research", "science"])
            elif "doe" in agency_code:
                themes.append("energy")
            elif "nih" in agency_code or "hhs" in agency_code:
                themes.extend(["health", "research"])
            elif "darpa" in agency_code or "dod" in agency_code:
                themes.extend(["defense", "innovation"])
            elif "nasa" in agency_code:
                themes.extend(["space", "research"])
            elif "usda" in agency_code:
                themes.append("agriculture")

            # Eligibility rules
            eligibility_rules = []
            for at in applicant_types:
                if at and at.get("description"):
                    eligibility_rules.append({"type": "applicant_type", "value": at["description"]})

            # ALNs (Assistance Listing Numbers)
            alns = data.get("alns", [])
            if alns:
                for aln in alns[:5]:
                    if aln and aln.get("programTitle"):
                        eligibility_rules.append({"type": "program", "value": aln["programTitle"]})

            return RawOpportunity(
                source=self.source_name,
                external_id=f"grants-gov-{opp_id}",
                title=title,
                url=url,
                description=description[:5000],
                start_date=open_date,
                end_date=close_date,
                submission_deadline=close_date,
                location="United States",
                is_online=True,
                regions=["US", "United States"],
                total_prize_amount=prize_amount,
                prize_currency="USD",
                tags=tags,
                themes=themes,
                host_name=agency_name,
                host_url="https://www.grants.gov",
                eligibility_rules=eligibility_rules,
                raw_data=data,
            )

        except Exception as e:
            logger.warning(f"Failed to parse Grants.gov detailed opportunity: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Grants.gov API is accessible."""
        try:
            client = await self.get_client()
            response = await client.get("https://www.grants.gov")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Grants.gov health check failed: {e}")
            return False


def create_grants_gov_scraper(**kwargs) -> GrantsGovScraper:
    """Create a Grants.gov scraper instance."""
    return GrantsGovScraper(**kwargs)
