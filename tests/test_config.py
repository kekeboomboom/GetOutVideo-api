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
        assert config.start_index == 1
        assert config.end_index == 0
        assert config.cookie_path is None
        assert config.use_ai_fallback is False
        assert config.cleanup_temp_files is True
    
    def test_invalid_start_index(self):
        """Test validation of start_index."""
        with pytest.raises(ValueError, match="start_index must be >= 1"):
            TranscriptConfig(start_index=0)
    
    def test_invalid_end_index(self):
        """Test validation of end_index."""
        with pytest.raises(ValueError, match="end_index must be >= 0"):
            TranscriptConfig(end_index=-1)
    
    def test_invalid_range(self):
        """Test validation of start/end range."""
        with pytest.raises(ValueError, match="end_index must be >= start_index"):
            TranscriptConfig(start_index=5, end_index=3)
    
    def test_valid_range(self):
        """Test valid range configuration."""
        config = TranscriptConfig(start_index=2, end_index=10)
        assert config.start_index == 2
        assert config.end_index == 10


class TestProcessingConfig:
    """Test ProcessingConfig validation."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ProcessingConfig()
        assert config.chunk_size == 70000
        assert config.model_name == "gemini-1.5-flash"
        assert config.output_language == "English"
        assert config.styles is None
    
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
    
    def test_missing_gemini_key(self):
        """Test that missing Gemini API key raises error."""
        with pytest.raises(ValueError, match="gemini_api_key is required"):
            APIConfig(gemini_api_key="")
    
    def test_valid_config(self):
        """Test valid configuration creation."""
        config = APIConfig(gemini_api_key="test-key")
        assert config.gemini_api_key == "test-key"
        assert config.openai_api_key is None
        assert isinstance(config.transcript_config, TranscriptConfig)
        assert isinstance(config.processing_config, ProcessingConfig)
    
    def test_ai_fallback_without_openai_key(self):
        """Test that AI fallback requires OpenAI key."""
        with pytest.raises(ValueError, match="openai_api_key is required when use_ai_fallback is True"):
            APIConfig(
                gemini_api_key="test-key",
                transcript_config=TranscriptConfig(use_ai_fallback=True)
            )
    
    def test_ai_fallback_with_openai_key(self):
        """Test valid AI fallback configuration."""
        config = APIConfig(
            gemini_api_key="test-key",
            openai_api_key="openai-key",
            transcript_config=TranscriptConfig(use_ai_fallback=True)
        )
        assert config.gemini_api_key == "test-key"
        assert config.openai_api_key == "openai-key"