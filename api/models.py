"""
Data models for the WatchYTPL4Me API.

This module defines the core data structures used throughout the API for
representing video transcripts, processing results, and related metadata.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class VideoTranscript:
    """Represents a video transcript with metadata."""
    
    title: str
    url: str
    transcript_text: str
    source: str  # "youtube_api" or "ai_stt"
    duration: Optional[int] = None
    word_count: Optional[int] = None
    
    def __post_init__(self):
        """Calculate word count if not provided."""
        if self.word_count is None and self.transcript_text:
            self.word_count = len(self.transcript_text.split())


@dataclass
class ProcessingResult:
    """Represents the result of AI processing on a video transcript."""
    
    video_transcript: VideoTranscript
    style_name: str
    output_file_path: str
    processing_time: float
    chunk_count: int
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set creation timestamp if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()