# WatchYTPL4Me API Extraction Plan

## Executive Summary

This plan outlines the extraction of core functionality from WatchYTPL4Me to create a reusable API library alongside the existing PyQt5 GUI application. The original GUI code will remain untouched, while the new API will be created in the `api/` directory, providing clean interfaces for programmatic use in other projects.

## Current Architecture Analysis

### Identified Components
Based on codebase analysis, the following core components were identified:

1. **TranscriptExtractionThread** (`main.pyw:1007-1259`)
   - Handles YouTube playlist/video URL parsing
   - Extracts transcripts using YouTube Transcript API
   - Implements fallback to AI STT via OpenAI
   - Manages video range processing (start/end indices)
   - Supports cookie-based authentication for restricted content

2. **GeminiProcessingThread** (`main.pyw:1261-1522`)
   - Processes transcript text using Google Gemini API
   - Implements text chunking for large transcripts
   - Applies multiple refinement styles simultaneously
   - Handles markdown output generation with proper formatting

3. **Audio Transcription Module** (`ytvideo2txt.py`)
   - Downloads audio from YouTube videos
   - Segments audio based on silence detection
   - Uses OpenAI's transcription service as fallback
   - Manages temporary file cleanup

4. **Prompt Templates** (`prompts.py`)
   - Defines refinement styles and their prompts
   - Supports language localization via placeholders

### Key Dependencies
- **Core Processing**: `pytubefix`, `youtube-transcript-api`, `google-generativeai`, `openai`
- **Audio Processing**: `yt-dlp`, `pydub`, `ffmpeg-python` 
- **GUI (preserved in original)**: `PyQt5`
- **Utilities**: `python-dotenv`

## Proposed API Architecture

### 1. Configuration Management

**File: `api/config.py`**

```python
@dataclass
class TranscriptConfig:
    start_index: int = 1
    end_index: int = 0
    cookie_path: Optional[str] = None
    use_ai_fallback: bool = True
    cleanup_temp_files: bool = True

@dataclass  
class ProcessingConfig:
    chunk_size: int = 70000
    model_name: str = "gemini-1.5-flash"
    output_language: str = "English"
    styles: List[str] = None  # Uses all by default

@dataclass
class APIConfig:
    gemini_api_key: str
    openai_api_key: Optional[str] = None
    transcript_config: TranscriptConfig = field(default_factory=TranscriptConfig)
    processing_config: ProcessingConfig = field(default_factory=ProcessingConfig)
```

### 2. Core Processing Classes

**File: `api/transcript_extractor.py`**

```python
class TranscriptExtractor:
    def __init__(self, config: APIConfig):
        pass
    
    def extract_transcripts(self, url: str, progress_callback: Optional[Callable] = None) -> List[VideoTranscript]:
        """Extract transcripts from YouTube URL (playlist or single video)"""
        pass
    
    def _extract_single_video(self, video_url: str) -> VideoTranscript:
        """Extract transcript from a single video with fallback"""
        pass
```

**File: `api/ai_processor.py`**

```python  
class AIProcessor:
    def __init__(self, config: APIConfig):
        pass
        
    def process_transcripts(self, transcripts: List[VideoTranscript], 
                          output_dir: str, progress_callback: Optional[Callable] = None) -> List[str]:
        """Process transcripts with AI refinement styles"""
        pass
        
    def _process_single_transcript(self, transcript: VideoTranscript, 
                                 style_name: str, style_prompt: str) -> str:
        """Process a single transcript with one style"""
        pass
```

### 3. High-Level API Interface

**File: `api/__init__.py`**

```python
class WatchYTPL4MeAPI:
    """Main API class providing simple and advanced interfaces"""
    
    def __init__(self, gemini_api_key: str, openai_api_key: Optional[str] = None):
        pass
    
    # Simple interface
    def process_youtube_url(self, url: str, output_dir: str, 
                           styles: Optional[List[str]] = None) -> List[str]:
        """One-line processing for most use cases"""
        pass
    
    # Advanced interface  
    def extract_transcripts(self, url: str, config: Optional[TranscriptConfig] = None) -> List[VideoTranscript]:
        """Extract transcripts only"""
        pass
        
    def process_with_ai(self, transcripts: List[VideoTranscript], 
                       output_dir: str, config: Optional[ProcessingConfig] = None) -> List[str]:
        """Process existing transcripts with AI"""
        pass

# Convenience functions
def process_youtube_playlist(url: str, output_dir: str, gemini_api_key: str, 
                           styles: Optional[List[str]] = None) -> List[str]:
    """Quick function for simple use cases"""
    pass
```

### 4. Data Models

**File: `api/models.py`**

```python
@dataclass
class VideoTranscript:
    title: str
    url: str
    transcript_text: str
    source: str  # "youtube_api" or "ai_stt"
    duration: Optional[int] = None
    word_count: Optional[int] = None

@dataclass
class ProcessingResult:
    video_transcript: VideoTranscript
    style_name: str
    output_file_path: str
    processing_time: float
    chunk_count: int
```

## Implementation Strategy

### Phase 1: Core Extraction (Estimated: 2-3 days)

1. **Extract Business Logic**
   - Copy and adapt transcript extraction code without PyQt5 dependencies
   - Convert thread signals to callback functions or return values
   - Extract text processing logic from Gemini thread to standalone classes

2. **Create Base Classes**
   - Implement `TranscriptExtractor` class
   - Implement `AIProcessor` class  
   - Add proper error handling with custom exceptions

3. **Configuration System**
   - Create dataclass-based configuration
   - Support both programmatic and file-based configuration
   - Add validation for API keys and parameters

### Phase 2: API Interface Design (Estimated: 1-2 days)

1. **Simple API Interface**
   - Create one-function interface for common use cases
   - Implement sensible defaults
   - Add comprehensive error messages

2. **Advanced API Interface**
   - Separate transcript extraction from AI processing
   - Allow custom prompts and styles
   - Support batch processing

3. **Progress Reporting**
   - Replace Qt signals with callback functions
   - Add optional progress bars for CLI usage
   - Implement async versions of main functions

### Phase 3: Testing & Documentation (Estimated: 2-3 days)

1. **Test Suite**
   - Unit tests for each core component
   - Integration tests with real YouTube URLs
   - Mock tests for API interactions
   - Performance tests with large playlists

2. **Documentation**
   - API reference documentation
   - Usage examples and tutorials
   - Migration guide from GUI version

3. **Packaging**
   - Setup.py configuration
   - Requirements management
   - CI/CD pipeline setup

## Migration Path

### For Current GUI Users
- GUI application continues to work unchanged and untouched
- Future enhancement: GUI could optionally use new API internally for better maintainability

### For New API Users
```python
# Simple usage
from api import process_youtube_playlist

files = process_youtube_playlist(
    "https://www.youtube.com/playlist?list=...", 
    "/output/dir",
    gemini_api_key="your-key"
)

# Advanced usage  
from api import WatchYTPL4MeAPI, TranscriptConfig

api = WatchYTPL4MeAPI(gemini_api_key="your-key")
config = TranscriptConfig(start_index=1, end_index=5)
transcripts = api.extract_transcripts(url, config)
processed_files = api.process_with_ai(transcripts, "/output/dir")
```

## Risk Mitigation

### Technical Risks
- **Hidden GUI Dependencies**: Thorough testing will identify any missed PyQt5 coupling
- **API Rate Limits**: Implement retry logic and rate limiting
- **Memory Usage**: Add streaming support for very large playlists

### Compatibility Risks
- **YouTube API Changes**: Maintain fallback mechanisms
- **Model Changes**: Support multiple Gemini models
- **File System Issues**: Add robust path handling across platforms

## Success Metrics

1. **Functional Parity**: All GUI features available via API
2. **Performance**: Processing speed within 10% of GUI version
3. **Usability**: One-line usage for common scenarios
4. **Reliability**: <1% failure rate on standard YouTube content
5. **Adoption**: Clean integration examples for common frameworks

## Directory Structure

```
api/
├── __init__.py          # Main API exports
├── config.py           # Configuration dataclasses  
├── models.py           # Data models
├── transcript_extractor.py  # YouTube transcript extraction
├── ai_processor.py     # AI processing logic
├── prompts.py          # Refinement style prompts (copied from root)
├── exceptions.py       # Custom exception classes
├── utils.py           # Utility functions
└── tests/
    ├── test_transcript_extraction.py
    ├── test_ai_processing.py  
    ├── test_api_interface.py
    └── fixtures/       # Test data
```

This plan provides a comprehensive roadmap for extracting the core functionality while preserving the original GUI application and expanding usability for integration into other projects.

## Implementation Notes

### Code Preservation
- **Original GUI**: All existing code in `main.pyw`, `prompts.py`, and `ytvideo2txt.py` remains completely untouched
- **API Extraction**: New code in `api/` directory contains adapted versions of the core logic
- **Shared Dependencies**: Both GUI and API can use the same `requirements.txt`

### Key Adaptations
- **Thread Removal**: PyQt5 QThread classes converted to regular Python classes
- **Signal Replacement**: Qt signals replaced with callback functions or return values
- **Configuration**: GUI controls replaced with dataclass configuration objects
- **Error Handling**: Qt error dialogs replaced with standard Python exceptions