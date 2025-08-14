# GetOutVideo API

**Transform YouTube videos into professional documents with AI**

GetOutVideo is a Python API that converts YouTube videos into structured, readable documents. Simply provide a YouTube URL, and it extracts transcripts and transforms them into professional-quality materials using OpenAI's GPT models.

## What it does

Turn any YouTube video into:
- **Summaries** - Quick overviews and key points
- **Educational materials** - Structured lessons and tutorials  
- **Documentation** - Technical guides and how-tos
- **Study notes** - Q&A format and bullet points
- **Research content** - Comprehensive analysis

Perfect for students, researchers, content creators, and professionals who want to convert video content into text-based learning materials.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/getoutvideo.svg)](https://badge.fury.io/py/getoutvideo)

## Features

- **YouTube Integration**: Extract transcripts from individual videos
- **AI Processing**: Transform raw transcripts using OpenAI's GPT models
- **Multiple Styles**: Generate summaries, educational content, Q&A, key points, and more
- **Flexible Configuration**: Customize processing parameters, languages, and output formats
- **Fallback Transcription**: Uses OpenAI's audio transcription when YouTube transcripts aren't available
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
from getoutvideo import process_youtube_video

# Process a single video
files = process_youtube_video(
    url="https://www.youtube.com/watch?v=7gp7GkPE-tI",
    output_dir="./output",
    openai_api_key="your-openai-api-key"
)

print(f"Generated {len(files)} documents!")
# Creates: video_title [Summary].md, video_title [Educational].md, etc.
```

### Process Specific Styles

```python
from getoutvideo import GetOutVideoAPI

api = GetOutVideoAPI(openai_api_key="your-openai-api-key")

# Generate only summaries and educational content
files = api.process_youtube_url(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir="./summaries",
    styles=["Summary", "Educational"]
)
```


## How It Works

1. **Extract** - Downloads transcripts from YouTube (with AI fallback when needed)
2. **Process** - Uses OpenAI's GPT models to format and structure content  
3. **Generate** - Creates professional markdown documents in multiple styles

## Available Processing Styles

GetOutVideo creates different document types from the same video:

| Style | Best For | Output Format |
|-------|----------|---------------|
| **Summary** | Quick overviews | Concise main points |
| **Educational** | Learning materials | Structured lessons with examples |
| **Balanced and Detailed** | Comprehensive reports | Full detailed coverage with all information |
| **Q&A Generation** | Training materials | Question and answer format |
| **Narrative Rewriting** | Engaging content | Story-like format while maintaining facts |

```python
# Get all available styles
from getoutvideo import GetOutVideoAPI
api = GetOutVideoAPI(openai_api_key="your-key")
print(api.get_available_styles())
```

## Configuration

### Using Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key"
export LANGUAGE="English"
```

```python
from getoutvideo import load_api_from_env
api = load_api_from_env()  # Uses environment variables
```

## API Reference

### Main Functions

#### `process_youtube_video()`
One-line processing for videos:

```python
from getoutvideo import process_youtube_video

files = process_youtube_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir="./output",
    openai_api_key="your-openai-api-key",
    styles=["Summary", "Educational"],  # Optional
    output_language="English"          # Optional
)
```

#### `GetOutVideoAPI` Class
For advanced control:

```python
from getoutvideo import GetOutVideoAPI

api = GetOutVideoAPI(openai_api_key="your-openai-api-key")

# Process videos
files = api.process_youtube_url(url, output_dir, styles=["Summary"])

# Extract transcripts only
transcripts = api.extract_transcripts(url)

# Process existing transcripts
results = api.process_with_ai(transcripts, output_dir, styles=["Educational"])
```

#### `extract_transcripts_only()`
Get raw transcripts without AI processing:

```python
from getoutvideo import extract_transcripts_only

transcripts = extract_transcripts_only(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    openai_api_key="your-openai-api-key"
)
```

## Use Cases

### Course Materials
```python
# Convert lectures to study materials
study_files = process_youtube_video(
    url="https://www.youtube.com/watch?v=LECTURE_VIDEO",
    output_dir="./course_materials",
    openai_api_key="your-key",
    styles=["Educational", "Summary"]
)
```

### Technical Documentation
```python
# Turn tutorial videos into documentation
api = GetOutVideoAPI(openai_api_key="your-key")
transcripts = api.extract_transcripts("https://www.youtube.com/watch?v=TUTORIAL_ID")
docs = api.process_with_ai(transcripts, "./docs", styles=["Educational"])
```

### Research and Analysis
```python
# Process conference talks for research
files = process_youtube_video(
    url="https://www.youtube.com/watch?v=CONFERENCE_TALK",
    output_dir="./research",
    openai_api_key="your-key",
    styles=["Balanced", "Summary"]
)
```

## Output Files

Generated files follow this naming pattern:
```
{video_title} [{style_name}].md
```

Example output for "Python Tutorial":
```
📁 output/
├── Python_Tutorial [Summary].md
├── Python_Tutorial [Educational].md  
├── Python_Tutorial [Balanced and Detailed].md
└── Python_Tutorial [Q&A Generation].md
```

Each file contains:
- Original video URL
- Structured content in markdown format
- Style-specific formatting (bullets, sections, Q&A, etc.)

## Error Handling

```python
from getoutvideo import GetOutVideoAPI, GetOutVideoError

try:
    api = GetOutVideoAPI(openai_api_key="your-key")
    files = api.process_youtube_url(url="...", output_dir="./output")
    print(f"Success: {len(files)} files generated")
except GetOutVideoError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Rate Limits and Costs

- Respects OpenAI rate limits automatically
- Costs depend on transcript length and models used
- Use specific `styles` parameter to reduce processing
- Adjust `chunk_size` for cost optimization

## Development

```bash
git clone https://github.com/yourusername/getoutvideo.git
cd getoutvideo
pip install -e ".[dev]"
pytest tests/          # Run tests
black getoutvideo/     # Format code
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/getoutvideo/issues)
- Documentation: Full API docs and examples available

## Credits

Built with OpenAI GPT models, YouTube Transcript API, and FFmpeg for audio processing.