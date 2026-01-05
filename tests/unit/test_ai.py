"""Unit tests for AI module."""

import pytest


class TestAIImports:
    """Test that AI modules can be imported correctly."""

    def test_import_material_generator(self):
        """Test MaterialGenerator import."""
        from src.opportunity_radar.ai import MaterialGenerator

        assert MaterialGenerator is not None

    def test_import_openai_client(self):
        """Test OpenAIClient import."""
        from src.opportunity_radar.ai import OpenAIClient

        assert OpenAIClient is not None


class TestPromptTemplates:
    """Test AI prompt template generation."""

    def test_readme_prompt(self):
        """Test README prompt generation."""
        from src.opportunity_radar.ai.prompts.templates import build_readme_prompt

        prompt = build_readme_prompt(
            project_name="TestApp",
            problem="Users can't do X",
            solution="Our app does Y",
            tech_stack=["Python", "FastAPI"],
            opportunity_title="Hackathon 2024",
            opportunity_themes=["AI", "Cloud"],
        )

        assert "TestApp" in prompt
        assert len(prompt) > 100

    def test_pitch_prompt(self):
        """Test Pitch prompt generation."""
        from src.opportunity_radar.ai.prompts.templates import build_pitch_prompt

        prompt = build_pitch_prompt(
            project_name="TestApp",
            problem="Users can't do X",
            solution="Our app does Y",
            tech_stack=["Python"],
            opportunity_title="Hackathon 2024",
            time_limit_min=3,
        )

        assert "TestApp" in prompt
        assert "3" in prompt
        assert len(prompt) > 100

    def test_demo_script_prompt(self):
        """Test Demo Script prompt generation."""
        from src.opportunity_radar.ai.prompts.templates import build_demo_script_prompt

        prompt = build_demo_script_prompt(
            project_name="TestApp",
            solution="Our app does Y",
            tech_stack=["Python"],
            features=["Feature A", "Feature B"],
            time_limit_min=2,
        )

        assert "TestApp" in prompt
        assert len(prompt) > 100

    def test_qa_prompt(self):
        """Test Q&A prompt generation."""
        from src.opportunity_radar.ai.prompts.templates import build_qa_prompt

        prompt = build_qa_prompt(
            project_name="TestApp",
            problem="Users can't do X",
            solution="Our app does Y",
            tech_stack=["Python"],
            opportunity_title="Hackathon 2024",
            opportunity_themes=["AI"],
        )

        assert "TestApp" in prompt
        assert len(prompt) > 100
