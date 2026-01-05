"""Unit tests for scrapers."""

import pytest


class TestScraperImports:
    """Test that all scrapers can be imported correctly."""

    def test_import_devpost_scraper(self):
        """Test DevpostScraper import."""
        from src.opportunity_radar.scrapers import DevpostScraper

        assert DevpostScraper is not None

    def test_import_mlh_scraper(self):
        """Test MLHScraper import."""
        from src.opportunity_radar.scrapers import MLHScraper

        assert MLHScraper is not None

    def test_import_ethglobal_scraper(self):
        """Test ETHGlobalScraper import."""
        from src.opportunity_radar.scrapers import ETHGlobalScraper

        assert ETHGlobalScraper is not None

    def test_import_kaggle_scraper(self):
        """Test KaggleScraper import."""
        from src.opportunity_radar.scrapers import KaggleScraper

        assert KaggleScraper is not None

    def test_import_hackerearth_scraper(self):
        """Test HackerEarthScraper import."""
        from src.opportunity_radar.scrapers import HackerEarthScraper

        assert HackerEarthScraper is not None

    def test_import_grants_gov_scraper(self):
        """Test GrantsGovScraper import."""
        from src.opportunity_radar.scrapers import GrantsGovScraper

        assert GrantsGovScraper is not None

    def test_import_sbir_scraper(self):
        """Test SBIRScraper import."""
        from src.opportunity_radar.scrapers import SBIRScraper

        assert SBIRScraper is not None

    def test_import_eu_horizon_scraper(self):
        """Test EUHorizonScraper import."""
        from src.opportunity_radar.scrapers import EUHorizonScraper

        assert EUHorizonScraper is not None

    def test_import_innovate_uk_scraper(self):
        """Test InnovateUKScraper import."""
        from src.opportunity_radar.scrapers import InnovateUKScraper

        assert InnovateUKScraper is not None

    def test_import_hackerone_scraper(self):
        """Test HackerOneScraper import."""
        from src.opportunity_radar.scrapers import HackerOneScraper

        assert HackerOneScraper is not None

    def test_import_ycombinator_scraper(self):
        """Test YCombinatorScraper import."""
        from src.opportunity_radar.scrapers import YCombinatorScraper

        assert YCombinatorScraper is not None

    def test_import_opensource_grants_scraper(self):
        """Test OpenSourceGrantsScraper import."""
        from src.opportunity_radar.scrapers import OpenSourceGrantsScraper

        assert OpenSourceGrantsScraper is not None


class TestScraperInitialization:
    """Test scraper initialization."""

    def test_devpost_scraper_init(self):
        """Test DevpostScraper initialization."""
        from src.opportunity_radar.scrapers import DevpostScraper

        scraper = DevpostScraper()
        assert scraper.source_name == "devpost"

    def test_mlh_scraper_init(self):
        """Test MLHScraper initialization."""
        from src.opportunity_radar.scrapers import MLHScraper

        scraper = MLHScraper()
        assert scraper.source_name == "mlh"

    def test_grants_gov_scraper_init(self):
        """Test GrantsGovScraper initialization."""
        from src.opportunity_radar.scrapers import GrantsGovScraper

        scraper = GrantsGovScraper()
        assert scraper.source_name == "grants_gov"

    def test_hackerone_scraper_init(self):
        """Test HackerOneScraper initialization."""
        from src.opportunity_radar.scrapers import HackerOneScraper

        scraper = HackerOneScraper()
        assert scraper.source_name == "hackerone"
