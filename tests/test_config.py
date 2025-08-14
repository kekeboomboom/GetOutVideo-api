"""
Tests for configuration classes and validation.
"""

import pytest

from getoutvideo import get_available_styles
from getoutvideo.config import APIConfig, TranscriptConfig, ProcessingConfig
from getoutvideo.prompts import text_refinement_prompts


class TestTranscriptConfig:
    """Test TranscriptConfig validation."""

    def test_style(self):
        testmap = text_refinement_prompts
        print(get_available_styles())
    
    def test_default_values(self):
        """Test default configuration values."""
        config = TranscriptConfig()
        assert config.cookie_path is None
        assert config.use_ai_fallback is False
        assert config.cleanup_temp_files is True
    


class TestProcessingConfig:
    """Test ProcessingConfig validation."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ProcessingConfig()
        assert config.chunk_size == 70000
        assert config.model_name == "gpt-4o-mini"
        assert config.output_language == "English"
        assert config.styles == ["Summary"]
    
    def test_invalid_chunk_size(self):
        """Test validation of chunk_size."""
        with pytest.raises(ValueError, match="chunk_size must be > 0"):
            ProcessingConfig(chunk_size=0)
    
    def test_empty_language(self):
        """Test validation of output_language."""
        with pytest.raises(ValueError, match="output_language cannot be empty"):
            ProcessingConfig(output_language="")


class TestAPIConfig:
    """Test APIConfig validation and initialization."""
    
    def test_missing_openai_key(self):
        """Test that missing OpenAI API key raises error."""
        with pytest.raises(ValueError, match="openai_api_key is required"):
            APIConfig(openai_api_key="")
    
    def test_valid_config(self):
        """Test valid configuration creation."""
        config = APIConfig(openai_api_key="test-key")
        assert config.openai_api_key == "test-key"
        assert config.gemini_api_key is None
        assert isinstance(config.transcript_config, TranscriptConfig)
        assert isinstance(config.processing_config, ProcessingConfig)
    
    def test_ai_fallback_without_openai_key(self):
        """Test that AI fallback requires OpenAI key."""
        with pytest.raises(ValueError, match="openai_api_key is required"):
            APIConfig(
                openai_api_key="",
                transcript_config=TranscriptConfig(use_ai_fallback=True)
            )
    
    def test_ai_fallback_with_openai_key(self):
        """Test valid AI fallback configuration."""
        config = APIConfig(
            openai_api_key="openai-key",
            gemini_api_key="gemini-key",
            transcript_config=TranscriptConfig(use_ai_fallback=True)
        )
        assert config.openai_api_key == "openai-key"
        assert config.gemini_api_key == "gemini-key"