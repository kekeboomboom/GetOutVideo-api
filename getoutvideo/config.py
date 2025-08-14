"""
Configuration classes for the WatchYTPL4Me API.

This module provides dataclass-based configuration objects that replace
the GUI controls from the original application with programmatic configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import os


@dataclass
class TranscriptConfig:
    """Configuration for transcript extraction."""
    
    start_index: int = 1
    end_index: int = 0  # 0 means process all videos
    cookie_path: Optional[str] = None
    use_ai_fallback: bool = False
    cleanup_temp_files: bool = True
    transcript_languages: Optional[List[str]] = None  # Language codes to request (e.g., ['zh', 'en'])
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.start_index < 1:
            raise ValueError("start_index must be >= 1")
        if self.end_index < 0:
            raise ValueError("end_index must be >= 0")
        if self.end_index > 0 and self.end_index < self.start_index:
            raise ValueError("end_index must be >= start_index")


@dataclass
class ProcessingConfig:
    """Configuration for AI processing."""
    
    chunk_size: int = 70000
    model_name: str = "gpt-4o-mini"
    output_language: str = "English"
    styles: Optional[List[str]] = field(default_factory=lambda: ["Summary"])  # Default to Summary style only
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if not self.output_language:
            raise ValueError("output_language cannot be empty")


@dataclass
class APIConfig:
    """Main configuration object containing all API settings."""
    
    openai_api_key: str
    gemini_api_key: Optional[str] = None
    transcript_config: TranscriptConfig = field(default_factory=TranscriptConfig)
    processing_config: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    def __post_init__(self):
        """Validate API keys and load from environment if needed."""
        # Load from environment variables if not provided
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            
        # Validate required keys
        if not self.openai_api_key:
            raise ValueError("openai_api_key is required (set directly or via OPENAI_API_KEY env var)")
        
        # OpenAI key is now required as primary API


def load_config_from_env() -> APIConfig:
    """
    Load configuration from environment variables.
    
    Expected environment variables:
    - OPENAI_API_KEY (required)
    - GEMINI_API_KEY (optional, for backward compatibility)
    - LANGUAGE (optional, defaults to "English")
    
    Returns:
        APIConfig: Configured API settings
    """
    return APIConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        processing_config=ProcessingConfig(
            output_language=os.getenv("LANGUAGE", "English")
        )
    )