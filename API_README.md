# WatchYTPL4Me API

A Python API for extracting YouTube video transcripts and transforming them into professional-quality documents using AI processing.

## Overview

The WatchYTPL4Me API provides programmatic access to the core functionality of the WatchYTPL4Me desktop application. It allows you to:

- Extract transcripts from YouTube videos and playlists
- Process transcripts using Google's Gemini API with various refinement styles
- Handle both individual videos and entire playlists with range selection
- Use AI STT fallback when YouTube transcripts are unavailable
- Integrate the functionality into other Python projects

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure `ffmpeg` is installed and available in your system PATH for audio processing.

3. Set up your API keys in a `.env` file:
```env
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional, for AI STT fallback
LANGUAGE=English  # Optional, defaults to English
```

## Quick Start

### Simple Usage

The fastest way to process a YouTube playlist:

```python
from api import process_youtube_playlist

# Process entire playlist with default settings
output_files = process_youtube_playlist(
    url="https://www.youtube.com/playlist?list=PLrAXtmRdnEQy5GKLFVRLt17vTrZNyMLVa",
    output_dir="./output",
    gemini_api_key="your-api-key"
)

print(f"Generated {len(output_files)} files")
```

### Single Video Processing

```python
from api import process_youtube_playlist

# Process single video with specific styles
output_files = process_youtube_playlist(
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_dir="./output",
    gemini_api_key="your-api-key",
    styles=["Summary", "Q&A Generation"]
)
```

## Advanced Usage

### Custom Configuration

```python
from api import WatchYTPL4MeAPI, TranscriptConfig, ProcessingConfig

# Create custom configurations
transcript_config = TranscriptConfig(
    start_index=2,          # Start from 2nd video
    end_index=5,           # Process up to 5th video
    use_ai_fallback=True,  # Use AI STT when needed
    cleanup_temp_files=True
)

processing_config = ProcessingConfig(
    chunk_size=50000,       # Smaller chunks
    model_name="gemini-1.5-flash",
    output_language="Spanish",
    styles=["Educational", "Summary"]
)

# Initialize API
api = WatchYTPL4MeAPI(
    gemini_api_key="your-key",
    openai_api_key="your-openai-key"
)

# Process with custom settings
output_files = api.process_youtube_url(
    url="https://www.youtube.com/playlist?list=...",
    output_dir="./output",
    start_index=2,
    end_index=5,
    chunk_size=50000,
    output_language="Spanish"
)
```

### Two-Step Process

Extract transcripts first, then process them separately:

```python
from api import extract_transcripts_only, WatchYTPL4MeAPI

# Step 1: Extract transcripts
transcripts = extract_transcripts_only(
    url="https://www.youtube.com/playlist?list=...",
    gemini_api_key="your-key"
)

# Examine transcripts
for transcript in transcripts:
    print(f"{transcript.title}: {transcript.word_count} words")

# Step 2: Process with AI
api = WatchYTPL4MeAPI("your-key")
results = api.process_with_ai(transcripts, "./output")
```

### Environment Configuration

Load settings from environment variables:

```python
from api import load_api_from_env

# Loads from GEMINI_API_KEY, OPENAI_API_KEY, LANGUAGE env vars
api = load_api_from_env()

output_files = api.process_youtube_url(
    url="https://www.youtube.com/watch?v=...",
    output_dir="./output"
)
```

## Processing Styles

The API supports the same refinement styles as the desktop application:

- **Balanced and Detailed**: Well-structured format retaining all details
- **Summary**: Concise summary of main points
- **Educational**: Textbook-style format with definitions
- **Narrative Rewriting**: Engaging story-like format
- **Q&A Generation**: Question and answer format for self-assessment

## API Reference

### Main Classes

#### `WatchYTPL4MeAPI`
The main API interface providing both simple and advanced processing methods.

```python
api = WatchYTPL4MeAPI(gemini_api_key, openai_api_key=None)

# Simple interface
files = api.process_youtube_url(url, output_dir, **options)

# Advanced interface
transcripts = api.extract_transcripts(url, config=None)
results = api.process_with_ai(transcripts, output_dir, config=None)

# Utility methods
styles = api.get_available_styles()
api.cancel_operations()
```

#### Configuration Classes

```python
from api import APIConfig, TranscriptConfig, ProcessingConfig

# Main configuration
config = APIConfig(
    gemini_api_key="key",
    openai_api_key="key",
    transcript_config=TranscriptConfig(),
    processing_config=ProcessingConfig()
)

# Transcript extraction settings
transcript_config = TranscriptConfig(
    start_index=1,
    end_index=0,  # 0 = all videos
    cookie_path=None,
    use_ai_fallback=True,
    cleanup_temp_files=True
)

# AI processing settings
processing_config = ProcessingConfig(
    chunk_size=70000,
    model_name="gemini-1.5-flash",
    output_language="English",
    styles=None  # None = all styles
)
```

#### Data Models

```python
from api import VideoTranscript, ProcessingResult

# Transcript data
transcript = VideoTranscript(
    title="Video Title",
    url="https://youtube.com/watch?v=...",
    transcript_text="...",
    source="youtube_api",  # or "ai_stt"
    word_count=1000
)

# Processing result
result = ProcessingResult(
    video_transcript=transcript,
    style_name="Summary",
    output_file_path="/path/to/output.md",
    processing_time=5.2,
    chunk_count=3
)
```

### Convenience Functions

```python
from api import (
    process_youtube_playlist,
    extract_transcripts_only,
    load_api_from_env
)

# Quick processing
files = process_youtube_playlist(url, output_dir, gemini_key, **options)

# Extract only
transcripts = extract_transcripts_only(url, gemini_key, **options)

# Load from environment
api = load_api_from_env()
```

## Error Handling

The API uses custom exceptions for better error handling:

```python
from api import (
    WatchYTPLError,
    ConfigurationError,
    TranscriptExtractionError,
    AIProcessingError
)

try:
    output_files = process_youtube_playlist(...)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except TranscriptExtractionError as e:
    print(f"Failed to extract transcripts: {e}")
except AIProcessingError as e:
    print(f"AI processing failed: {e}")
except WatchYTPLError as e:
    print(f"General API error: {e}")
```

## Examples

See `api/examples.py` for comprehensive usage examples covering:

1. Simple one-line usage
2. Single video processing
3. Advanced configuration
4. Two-step processing
5. Error handling
6. Environment configuration
7. Progress monitoring

Run the examples:
```bash
python -m api.examples
```

## Testing

Run the test suite:
```bash
pytest api/tests/
```

The tests include:
- Configuration validation
- Utility function testing
- API interface testing
- Mock-based integration tests

## Relationship to GUI Application

The API is designed to coexist with the original PyQt5 GUI application:

- **GUI Application**: All original code remains unchanged in `main.pyw`
- **API**: New code in the `api/` directory provides programmatic access
- **Shared Dependencies**: Both use the same `requirements.txt` and core modules like `ytvideo2txt.py` and `prompts.py`

You can use both the GUI and API in the same project without conflicts.

## Performance Considerations

- **Chunking**: Large transcripts are automatically split into chunks for efficient API processing
- **Fallback**: AI STT is used only when YouTube transcripts are unavailable
- **Cleanup**: Temporary audio files can be automatically cleaned up to save disk space
- **Rate Limiting**: The API respects Gemini API rate limits through proper error handling

## Contributing

When contributing to the API:

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation and examples
4. Ensure compatibility with the GUI application
5. Test with various YouTube content types

## License

Same license as the main WatchYTPL4Me project.