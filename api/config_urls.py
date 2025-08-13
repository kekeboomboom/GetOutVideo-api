"""
Centralized YouTube URL configuration for WatchYTPL4Me.

This module contains all YouTube URLs used throughout the application
in one place for easy management and updates.
"""

# Main example videos for demonstrations
EXAMPLE_URLS = {
    "main_demo": "https://www.youtube.com/watch?v=7gp7GkPE-tI&feature=youtu.be",
    "rick_roll": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "test_video": "https://youtube.com/watch?v=test"
}

# Aliases for backward compatibility and readability
DEFAULT_EXAMPLE_URL = EXAMPLE_URLS["main_demo"]
FALLBACK_TEST_URL = EXAMPLE_URLS["rick_roll"]
UNIT_TEST_URL = EXAMPLE_URLS["test_video"]