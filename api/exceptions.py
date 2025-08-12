"""
Custom exceptions for the WatchYTPL4Me API.

This module defines API-specific exceptions that provide better error
handling and debugging information compared to generic exceptions.
"""


class WatchYTPLError(Exception):
    """Base exception for all WatchYTPL4Me API errors."""
    pass


class ConfigurationError(WatchYTPLError):
    """Raised when there's an issue with API configuration."""
    pass


class TranscriptExtractionError(WatchYTPLError):
    """Raised when transcript extraction fails."""
    pass


class AIProcessingError(WatchYTPLError):
    """Raised when AI processing fails."""
    pass


class YouTubeAccessError(TranscriptExtractionError):
    """Raised when YouTube content cannot be accessed."""
    pass


class AudioProcessingError(TranscriptExtractionError):
    """Raised when audio download or transcription fails."""
    pass


class GeminiAPIError(AIProcessingError):
    """Raised when Gemini API calls fail."""
    pass


class OpenAIAPIError(TranscriptExtractionError):
    """Raised when OpenAI API calls fail."""
    pass


class FileOperationError(WatchYTPLError):
    """Raised when file operations fail."""
    pass