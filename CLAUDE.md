# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GetOutVideo is a Python API package that transforms YouTube videos into professional documents using AI. It extracts transcripts from YouTube videos and processes them with OpenAI's GPT models to create structured content like summaries, educational materials, documentation, and study notes.

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

### Core Components
- **`GetOutVideoAPI`** (`getoutvideo/__init__.py`): Main API class providing both simple and advanced interfaces
- **`TranscriptExtractor`** (`getoutvideo/transcript_extractor.py`): Handles YouTube transcript extraction with AI fallback
- **`AIProcessor`** (`getoutvideo/ai_processor.py`): Processes transcripts using OpenAI's GPT models
- **Configuration System** (`getoutvideo/config.py`): Dataclass-based configurations for all aspects

### Data Models (`getoutvideo/models.py`)
- **`VideoTranscript`**: Represents video transcripts with metadata
- **`ProcessingResult`**: Represents AI processing results with cost tracking

### Processing Flow
1. **Extract**: `TranscriptExtractor` downloads transcripts from YouTube (with AI fallback using OpenAI STT)
2. **Process**: `AIProcessor` transforms transcripts using GPT models with various styles
3. **Generate**: Creates professional markdown documents in specified output directory

## Common Development Commands

### Testing
```bash
pytest tests/                    # Run all tests
pytest tests/test_config.py      # Run specific test file
pytest -v                       # Verbose test output
```

### Code Quality
```bash
black getoutvideo/              # Format code (line length: 100)
black --check getoutvideo/      # Check formatting
flake8 getoutvideo/             # Lint code
mypy getoutvideo/               # Type checking
```

### Package Building
```bash
pip install -e ".[dev]"         # Install in development mode with dev dependencies
python -m build                 # Build package for distribution
twine upload dist/*             # Upload to PyPI
```

### Environment Setup
```bash
pip install -r requirements.txt              # Install runtime dependencies
pip install -e ".[dev]"                     # Install with dev dependencies
export OPENAI_API_KEY="your-key-here"       # Required for API functionality
export LANGUAGE="English"                   # Optional language setting
```

## Key Configuration

### Required Dependencies
- Python 3.8+
- FFmpeg (system dependency for audio processing)
- OpenAI API key (required)

### Processing Styles Available
The system supports multiple processing styles defined in `getoutvideo/prompts.py`:
- Summary: Concise main points
- Educational: Structured lessons with examples
- Balanced and Detailed: Full detailed coverage
- Q&A Generation: Question and answer format
- Narrative Rewriting: Story-like format

### Configuration Objects
- **`APIConfig`**: Main configuration with API keys and sub-configs
- **`TranscriptConfig`**: Controls transcript extraction behavior
- **`ProcessingConfig`**: Controls AI processing parameters (chunk_size, model, styles, language)

## Development Notes

### Two-Step Processing Pattern
The API supports both single-call and two-step processing:
1. Extract transcripts with `extract_transcripts()`
2. Process separately with `process_with_ai()`

This pattern allows for transcript analysis before processing and applying different styles to the same content.

### Error Handling
Custom exception hierarchy in `getoutvideo/exceptions.py`:
- `GetOutVideoError`: Base exception
- `TranscriptExtractionError`: YouTube/audio extraction issues
- `AIProcessingError`: OpenAI processing issues
- `ConfigurationError`: Invalid configuration

### Cost Management
The system tracks OpenAI costs for both transcript extraction (STT) and processing (GPT models) in the result objects.

### File Operations
- Output files follow pattern: `{video_title} [{style_name}].md`
- Automatic filename sanitization for cross-platform compatibility
- Directory creation handled automatically

## Testing Structure

Tests are organized in `tests/` directory:
- `test_api_interface.py`: API integration tests
- `test_config.py`: Configuration validation tests
- `test_utils.py`: Utility function tests

## Examples

Comprehensive usage examples are available in `examples/`:
- `basic_usage.py`: Simple API usage patterns
- `advanced_usage.py`: Complex scenarios including batch processing, error handling, and custom configurations