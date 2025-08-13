"""
Custom exceptions for the GetOutVideo API.

This module defines API-specific exceptions that provide better error
handling and debugging information compared to generic exceptions.
"""


class GetOutVideoError(Exception):
    """Base exception for all GetOutVideo API errors."""
    pass


class ConfigurationError(GetOutVideoError):
    """Raised when there's an issue with API configuration."""
    pass


class TranscriptExtractionError(GetOutVideoError):
    """Raised when transcript extraction fails."""
    pass


class AIProcessingError(GetOutVideoError):
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


class OpenAIAPIError(AIProcessingError):
    """Raised when OpenAI API calls fail."""
    pass


class FileOperationError(GetOutVideoError):
    """Raised when file operations fail."""
    pass