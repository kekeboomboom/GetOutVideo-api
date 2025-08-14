"""
Tests for the main API interface.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from getoutvideo import GetOutVideoAPI, process_youtube_video, extract_transcripts_only
from getoutvideo.config import APIConfig, TranscriptConfig, ProcessingConfig
from getoutvideo.models import VideoTranscript, ProcessingResult
from getoutvideo.exceptions import ConfigurationError
from getoutvideo.config_urls import UNIT_TEST_URL


class TestGetOutVideoAPI:
    """Test the main API interface."""
    
    def test_initialization(self):
        """Test API initialization."""
        api = GetOutVideoAPI("test-key")
        
        assert api.config.openai_api_key == "test-key"
        assert api.transcript_extractor is not None
        assert api.ai_processor is not None
    
    def test_initialization_with_gemini(self):
        """Test API initialization with Gemini key."""
        api = GetOutVideoAPI("openai-key", "gemini-key")
        
        assert api.config.openai_api_key == "openai-key"
        assert api.config.gemini_api_key == "gemini-key"
    
    @patch('getoutvideo.transcript_extractor.TranscriptExtractor.extract_transcripts')
    @patch('getoutvideo.ai_processor.AIProcessor.process_transcripts')
    def test_process_youtube_url(self, mock_ai_process, mock_extract):
        """Test the simple process_youtube_url interface."""
        # Setup mocks
        mock_transcript = VideoTranscript(
            title="Test Video",
            url=UNIT_TEST_URL,
            transcript_text="Test transcript text",
            source="youtube_api"
        )
        mock_extract.return_value = [mock_transcript]
        
        mock_result = ProcessingResult(
            video_transcript=mock_transcript,
            style_name="Summary",
            output_file_path="/output/test_summary.md",
            processing_time=1.0,
            chunk_count=1
        )
        mock_ai_process.return_value = [mock_result]
        
        # Test the API
        api = GetOutVideoAPI("openai-key", "gemini-key")
        result = api.process_youtube_url(
            UNIT_TEST_URL,
            "/output",
            styles=["Summary"]
        )
        
        assert result == ["/output/test_summary.md"]
        mock_extract.assert_called_once()
        mock_ai_process.assert_called_once()
    
    @patch('getoutvideo.transcript_extractor.TranscriptExtractor.extract_transcripts')
    def test_extract_transcripts_only(self, mock_extract):
        """Test transcript extraction only."""
        mock_transcript = VideoTranscript(
            title="Test Video",
            url=UNIT_TEST_URL,
            transcript_text="Test transcript text",
            source="youtube_api"
        )
        mock_extract.return_value = [mock_transcript]
        
        api = GetOutVideoAPI("openai-key", "gemini-key")
        result = api.extract_transcripts(UNIT_TEST_URL)
        
        assert len(result) == 1
        assert result[0].title == "Test Video"
        mock_extract.assert_called_once()
    
    def test_get_available_styles(self):
        """Test getting available styles."""
        api = GetOutVideoAPI("test-key")
        styles = api.get_available_styles()
        
        assert isinstance(styles, list)
        assert len(styles) > 0
        assert "Summary" in styles


class TestConvenienceFunctions:
    """Test the convenience functions."""
    
    @patch('getoutvideo.GetOutVideoAPI.process_youtube_url')
    def test_process_youtube_video(self, mock_process):
        """Test the convenience video processing function."""
        mock_process.return_value = ["/output/file1.md"]
        
        result = process_youtube_video(
            "https://youtube.com/watch?v=test",
            "/output",
            "test-key",
            styles=["Summary"]
        )
        
        assert result == ["/output/file1.md"]
        mock_process.assert_called_once()
    
    @patch('getoutvideo.GetOutVideoAPI.extract_transcripts')
    def test_extract_transcripts_only_function(self, mock_extract):
        """Test the convenience transcript extraction function."""
        mock_transcript = VideoTranscript(
            title="Test Video",
            url=UNIT_TEST_URL,
            transcript_text="Test transcript text",
            source="youtube_api"
        )
        mock_extract.return_value = [mock_transcript]
        
        result = extract_transcripts_only(
            UNIT_TEST_URL,
            "test-key"
        )
        
        assert len(result) == 1
        assert result[0].title == "Test Video"
        mock_extract.assert_called_once()


class TestEnvironmentLoading:
    """Test environment variable loading."""
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-openai-key'})
    @patch('getoutvideo.load_api_from_env')
    def test_load_from_env_success(self, mock_load):
        """Test successful loading from environment."""
        mock_api = MagicMock()
        mock_load.return_value = mock_api
        
        from getoutvideo import load_api_from_env
        result = load_api_from_env()
        
        assert result == mock_api
    
    @patch.dict('os.environ', {}, clear=True)
    def test_load_from_env_missing_keys(self):
        """Test loading from environment with missing keys."""
        from getoutvideo import load_api_from_env
        
        with pytest.raises(ConfigurationError):
            load_api_from_env()