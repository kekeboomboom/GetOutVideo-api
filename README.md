# GetOutVideo API

**Extract and process YouTube video transcripts with AI**

GetOutVideo is a Python library that makes it easy to extract transcripts from YouTube videos and playlists, then process them using OpenAI's GPT models to create well-formatted, readable documents in various styles.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/getoutvideo.svg)](https://badge.fury.io/py/getoutvideo)

## Features

- **YouTube Integration**: Extract transcripts from individual videos or entire playlists
- **AI Processing**: Transform raw transcripts using OpenAI's GPT models
- **Multiple Styles**: Generate summaries, educational content, Q&A, key points, and more
- **Flexible Configuration**: Customize processing parameters, languages, and output formats
- **Fallback Transcription**: Uses OpenAI's audio transcription when YouTube transcripts aren't available
- **Batch Processing**: Handle multiple videos efficiently
- **Clean API**: Simple interface for both basic and advanced use cases

## Installation

```bash
pip install getoutvideo
```

### System Requirements

- Python 3.8 or higher
- FFmpeg (required for audio processing fallback)

#### Installing FFmpeg

**Windows:**
```bash
# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
# Using homebrew
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

## Quick Start

### Basic Usage

```python
from getoutvideo import process_youtube_playlist

# Process a single video
files = process_youtube_playlist(
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_dir="./output",
    openai_api_key="your-openai-api-key"
)

print(f"Generated {len(files)} files!")
```

### Advanced Usage

```python
from getoutvideo import GetOutVideoAPI

# Initialize the API
api = GetOutVideoAPI(openai_api_key="your-openai-api-key")

# Process with specific options
output_files = api.process_youtube_url(
    url="https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMw6luKi_8LlH4b1vD",
    output_dir="./summaries",
    styles=["Summary", "Key Points"],
    start_index=1,
    end_index=5,
    output_language="Spanish",
    chunk_size=50000
)
```

### Two-Step Processing

```python
from getoutvideo import GetOutVideoAPI

api = GetOutVideoAPI(openai_api_key="your-openai-api-key")

# Step 1: Extract transcripts
transcripts = api.extract_transcripts("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# Step 2: Process with different styles
educational_files = api.process_with_ai(transcripts, "./educational", 
                                      styles=["Educational"])
summary_files = api.process_with_ai(transcripts, "./summaries", 
                                   styles=["Summary"])
```

## Configuration

### Environment Variables

You can set up environment variables for easier configuration:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export LANGUAGE="English"  # Default output language
```

Then use:

```python
from getoutvideo import load_api_from_env

api = load_api_from_env()
# API is configured from environment variables
```

### Processing Styles

GetOutVideo includes several built-in processing styles:

- **Summary**: Concise overview of main points
- **Educational**: Structured learning material
- **Key Points**: Bullet-pointed highlights
- **Q&A**: Question and answer format
- **Technical**: Detailed technical documentation
- **Balanced**: Comprehensive balanced overview

## API Reference

### Main Classes

#### `GetOutVideoAPI`

The main API class for processing YouTube content.

```python
api = GetOutVideoAPI(
    openai_api_key="your-key",
    gemini_api_key="optional-gemini-key"  # For backward compatibility
)
```

**Methods:**

- `process_youtube_url(url, output_dir, **options)` - Process URL with AI in one call
- `extract_transcripts(url, config=None)` - Extract transcripts only
- `process_with_ai(transcripts, output_dir, config=None)` - Process existing transcripts
- `get_available_styles()` - List available processing styles
- `cancel_operations()` - Cancel ongoing operations

### Convenience Functions

#### `process_youtube_playlist()`

Quick function for simple processing:

```python
files = process_youtube_playlist(
    url="youtube_url",
    output_dir="output_directory",
    openai_api_key="your_key",
    styles=["Summary"],  # Optional
    start_index=1,       # Optional
    end_index=0,         # Optional (0 = all)
    output_language="English"  # Optional
)
```

#### `extract_transcripts_only()`

Extract transcripts without AI processing:

```python
transcripts = extract_transcripts_only(
    url="youtube_url",
    openai_api_key="your_key",
    use_ai_fallback=True
)
```

## Error Handling

```python
from getoutvideo import GetOutVideoAPI, GetOutVideoError

try:
    api = GetOutVideoAPI(openai_api_key="your-key")
    files = api.process_youtube_url(url, output_dir)
except GetOutVideoError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Examples

Check out the `examples/` directory for comprehensive usage examples:

- `examples/basic_usage.py` - Simple examples for getting started
- `examples/advanced_usage.py` - Advanced features and configurations

## Configuration Options

### Transcript Configuration

- `start_index`: Starting video index for playlists (1-based)
- `end_index`: Ending video index (0 = process all)
- `use_ai_fallback`: Use OpenAI transcription when YouTube transcripts unavailable
- `cookie_path`: Path to browser cookies for restricted content
- `cleanup_temp_files`: Remove temporary audio files after processing

### Processing Configuration

- `styles`: List of processing styles to apply
- `chunk_size`: Maximum words per API call (default: 70,000)
- `output_language`: Target language for output
- `max_concurrent_requests`: Limit concurrent API calls

## Output Formats

GetOutVideo generates markdown files with the following naming pattern:
```
{video_title} [{style_name}].md
```

Each file includes:
- Video title as H1 header
- Original video URL
- AI-processed content in the specified style

## Rate Limiting and Costs

- The library respects OpenAI's rate limits
- Processing costs depend on transcript length and selected models
- Use smaller `chunk_size` values to reduce per-request costs
- Consider using specific `styles` instead of processing all styles

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Submit a pull request

## Development

### Setting up the development environment

```bash
git clone https://github.com/yourusername/getoutvideo.git
cd getoutvideo
pip install -e ".[dev]"
```

### Running tests

```bash
pytest tests/
```

### Code formatting

```bash
black getoutvideo/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.0

- Initial release
- YouTube transcript extraction
- OpenAI GPT processing
- Multiple processing styles
- Playlist support
- Audio transcription fallback
- Comprehensive API interface

## Support

- **Documentation**: [https://getoutvideo.readthedocs.io](https://getoutvideo.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/yourusername/getoutvideo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/getoutvideo/discussions)

## Acknowledgments

- OpenAI for GPT models and transcription services
- YouTube Transcript API contributors
- PyTube and related YouTube access libraries
- FFmpeg for audio processing capabilities