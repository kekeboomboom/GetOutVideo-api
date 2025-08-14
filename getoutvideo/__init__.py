"""
GetOutVideo API - YouTube Video to Text Transformation

This module provides a clean, programmatic interface to extract and process 
YouTube video transcripts with AI, allowing you to integrate this functionality
into other projects without GUI dependencies.

Main Classes:
- GetOutVideoAPI: High-level API interface
- TranscriptExtractor: Direct transcript extraction
- AIProcessor: AI-powered text processing

Quick Usage:
    from getoutvideo import process_youtube_video
    
    files = process_youtube_video(
        "https://www.youtube.com/watch?v=VIDEO_ID",
        "/output/dir",
        "your-openai-api-key"
    )
"""

from typing import List, Optional
import os

from .config import APIConfig, TranscriptConfig, ProcessingConfig, load_config_from_env
from .models import VideoTranscript, ProcessingResult
from .transcript_extractor import TranscriptExtractor
from .ai_processor import AIProcessor
from .prompts import get_available_styles
from .exceptions import GetOutVideoError, ConfigurationError, TranscriptExtractionError, AIProcessingError
from . import config_urls

# Version info
__version__ = "1.0.0"
__author__ = "GetOutVideo API"


class GetOutVideoAPI:
    """
    Main API class providing both simple and advanced interfaces.
    
    This class orchestrates the transcript extraction and AI processing
    workflows, providing a clean interface for programmatic use.
    """
    
    def __init__(self, openai_api_key: str, gemini_api_key: Optional[str] = None):
        """
        Initialize the API with required credentials.
        
        Args:
            openai_api_key: OpenAI API key for text processing
            gemini_api_key: Optional Gemini API key for backward compatibility
        """
        self.config = APIConfig(
            openai_api_key=openai_api_key,
            gemini_api_key=gemini_api_key
        )
        
        self.transcript_extractor = TranscriptExtractor(self.config)
        self.ai_processor = AIProcessor(self.config)
    
    def process_youtube_url(self,
                          url: str,
                          output_dir: str,
                          styles: Optional[List[str]] = None,
                          chunk_size: int = 70000,
                          output_language: str = "English") -> List[str]:
        """
        Process a YouTube URL with AI refinement in one call.
        
        This is the simple interface for most use cases - extracts transcripts
        and processes them with AI in a single operation.
        
        Args:
            url: YouTube video URL
            output_dir: Directory where processed files will be saved
            styles: List of processing styles to use (None = all styles)
            chunk_size: Maximum words per API call
            output_language: Target language for the output
            
        Returns:
            List[str]: Paths to generated output files
            
        Raises:
            GetOutVideoError: If processing fails
        """
        print(f"DEBUG: process_youtube_url called with:")
        print(f"  URL: {url}")
        print(f"  Output dir: {output_dir}")
        print(f"  Styles: {styles}")
        print(f"  Chunk size: {chunk_size}")
        print(f"  Output language: {output_language}")
        
        # Update configuration
        self.config.processing_config.chunk_size = chunk_size
        self.config.processing_config.output_language = output_language
        self.config.processing_config.styles = styles
        
        print(f"DEBUG: Configuration updated")
        
        # Extract transcripts
        print(f"DEBUG: Starting transcript extraction...")
        transcripts = self.extract_transcripts(url)
        print(f"DEBUG: Extracted {len(transcripts)} transcripts")
        
        if not transcripts:
            print(f"DEBUG: No transcripts extracted, returning empty list")
            return []
        
        for i, transcript in enumerate(transcripts):
            print(f"DEBUG: Transcript {i+1}: title='{transcript.title[:50]}...', "
                  f"text_length={len(transcript.transcript_text)}, source={transcript.source}")
        
        # Process with AI
        print(f"DEBUG: Starting AI processing...")
        results = self.process_with_ai(transcripts, output_dir)
        print(f"DEBUG: AI processing completed with {len(results)} results")
        
        output_files = [result.output_file_path for result in results]
        print(f"DEBUG: Returning {len(output_files)} output file paths")
        
        return output_files
    
    def extract_transcripts(self,
                          url: str,
                          config: Optional[TranscriptConfig] = None) -> List[VideoTranscript]:
        """
        Extract transcripts from YouTube URL only.
        
        This method only extracts transcripts without AI processing,
        useful when you want to handle the AI processing separately
        or analyze transcripts before processing.
        
        Args:
            url: YouTube video URL
            config: Optional transcript configuration (uses API default if None)
            
        Returns:
            List[VideoTranscript]: Extracted video transcripts
            
        Raises:
            TranscriptExtractionError: If extraction fails
        """
        if config:
            self.config.transcript_config = config
            # Recreate extractor with updated config
            self.transcript_extractor = TranscriptExtractor(self.config)
        
        return self.transcript_extractor.extract_transcripts(url)
    
    def process_with_ai(self,
                       transcripts: List[VideoTranscript],
                       output_dir: str,
                       config: Optional[ProcessingConfig] = None) -> List[ProcessingResult]:
        """
        Process existing transcripts with AI.
        
        This method processes already-extracted transcripts with AI,
        useful when you want to apply different processing styles
        or parameters to the same transcripts.
        
        Args:
            transcripts: List of video transcripts to process
            output_dir: Directory where processed files will be saved
            config: Optional processing configuration (uses API default if None)
            
        Returns:
            List[ProcessingResult]: Processing results with metadata
            
        Raises:
            AIProcessingError: If processing fails
        """
        if config:
            self.config.processing_config = config
            # Recreate processor with updated config
            self.ai_processor = AIProcessor(self.config)
        
        return self.ai_processor.process_transcripts(transcripts, output_dir)
    
    def get_available_styles(self) -> List[str]:
        """Get list of available processing styles."""
        return get_available_styles()
    
    def cancel_operations(self) -> None:
        """Cancel any ongoing operations."""
        self.transcript_extractor.cancel()
        self.ai_processor.cancel()


# Convenience Functions



def extract_transcripts_only(url: str,
                           openai_api_key: str,
                           gemini_api_key: Optional[str] = None,
                           use_ai_fallback: bool = True) -> List[VideoTranscript]:
    """
    Extract transcripts only without AI processing.
    
    Args:
        url: YouTube video URL
        openai_api_key: OpenAI API key (required for API initialization)
        gemini_api_key: Optional Gemini API key for backward compatibility
        use_ai_fallback: Whether to use AI STT when YouTube transcripts unavailable
        
    Returns:
        List[VideoTranscript]: Extracted video transcripts
        
    Raises:
        TranscriptExtractionError: If extraction fails
    """
    config = TranscriptConfig(
        use_ai_fallback=use_ai_fallback
    )
    
    api = GetOutVideoAPI(openai_api_key, gemini_api_key)
    return api.extract_transcripts(url, config)


def process_youtube_video(url: str,
                         output_dir: str,
                         openai_api_key: str,
                         styles: Optional[List[str]] = None,
                         gemini_api_key: Optional[str] = None,
                         output_language: str = "English",
                         use_ai_fallback: bool = True) -> List[str]:
    """
    Process a single YouTube video with AI refinement.
    
    This is the main function for processing single YouTube videos
    with sensible defaults.
    
    Args:
        url: YouTube video URL
        output_dir: Directory where processed files will be saved
        openai_api_key: OpenAI API key for text processing
        styles: List of processing styles (None = all styles)
        gemini_api_key: Optional Gemini API key for backward compatibility
        output_language: Target language for the output
        use_ai_fallback: Whether to use AI STT when YouTube transcripts unavailable
        
    Returns:
        List[str]: Paths to generated output files
        
    Raises:
        GetOutVideoError: If processing fails
    """
    print(f"DEBUG: process_youtube_video called with:")
    print(f"  URL: {url}")
    print(f"  OpenAI API key: {'SET' if openai_api_key else 'NOT SET'}")
    print(f"  Gemini API key: {'SET' if gemini_api_key else 'NOT SET'}")
    print(f"  Styles: {styles}")
    print(f"  Use AI fallback: {use_ai_fallback}")
    
    print(f"DEBUG: Creating GetOutVideoAPI instance...")
    api = GetOutVideoAPI(openai_api_key, gemini_api_key)
    
    # Enable AI fallback if requested and OpenAI key is available
    if use_ai_fallback and openai_api_key:
        api.config.transcript_config.use_ai_fallback = True
        print(f"DEBUG: AI fallback enabled")
    else:
        print(f"DEBUG: AI fallback disabled (use_ai_fallback={use_ai_fallback}, openai_key={'SET' if openai_api_key else 'NOT SET'})")
    
    print(f"DEBUG: API instance created, calling process_youtube_url...")
    
    result = api.process_youtube_url(
        url, output_dir, styles,
        output_language=output_language
    )
    
    print(f"DEBUG: process_youtube_video returning {len(result)} files")
    return result


def load_api_from_env() -> GetOutVideoAPI:
    """
    Load API configuration from environment variables.
    
    Expects OPENAI_API_KEY and optionally GEMINI_API_KEY and LANGUAGE
    environment variables.
    
    Returns:
        GetOutVideoAPI: Configured API instance
        
    Raises:
        ConfigurationError: If required environment variables are missing
    """
    try:
        config = load_config_from_env()
        api = GetOutVideoAPI(config.openai_api_key, config.gemini_api_key)
        api.config = config  # Use the full config with language settings
        return api
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from environment: {str(e)}") from e


# Export main classes and functions
__all__ = [
    # Main classes
    'GetOutVideoAPI',
    'TranscriptExtractor',
    'AIProcessor',
    
    # Configuration
    'APIConfig',
    'TranscriptConfig', 
    'ProcessingConfig',
    'load_config_from_env',
    
    # Data models
    'VideoTranscript',
    'ProcessingResult',
    
    # Convenience functions
    'process_youtube_video',
    'extract_transcripts_only',
    'load_api_from_env',
    'get_available_styles',
    
    # Exceptions
    'GetOutVideoError',
    'ConfigurationError',
    'TranscriptExtractionError',
    'AIProcessingError'
]