# Local MP4 File Support Implementation Plan

## Feature Analysis
- **What**: Add support for processing local MP4 video files in addition to YouTube URLs
- **Scope**: Enable transcription extraction from local MP4 files using OpenAI Whisper API, then process with existing AI pipeline

## Current Architecture Analysis

### Existing Components
1. **Audio Processing Infrastructure**
   - `audio_transcriber.py` already has complete audio extraction and transcription capabilities
   - Uses FFmpeg for audio extraction (via pydub and ffmpeg-python)
   - Implements audio segmentation based on silence detection
   - Has OpenAI Whisper integration for Speech-to-Text (STT)
   - Handles cleanup of temporary files

2. **Data Flow**
   - Current: YouTube URL → Transcript (API/AI fallback) → AI Processing → Markdown
   - Proposed: MP4 File → Audio Extraction → AI Transcription → AI Processing → Markdown

3. **Dependencies Already Available**
   - FFmpeg (system dependency)
   - pydub (audio manipulation)
   - ffmpeg-python (FFmpeg bindings)
   - OpenAI SDK with Whisper support
   - File handling utilities

## Code Analysis

### Existing Patterns to Leverage
- **Audio Extraction**: `audio_transcriber.py` has `audio_segmentation()` that can process any audio file
- **Transcription**: `transcribe_audio_chunk_openai()` already implements Whisper API calls
- **Configuration**: `TranscriptConfig` can be extended with local file options
- **Models**: `VideoTranscript` model with `source` field can use "local_mp4" as source type
- **Error Handling**: Existing exception hierarchy can be extended

### Files to Modify
1. **`getoutvideo/config.py`**
   - Add local file configuration options to `TranscriptConfig`

2. **`getoutvideo/transcript_extractor.py`**
   - Add logic to detect local file vs URL input
   - Implement `_extract_local_video()` method

3. **`getoutvideo/audio_transcriber.py`**
   - Refactor existing functions to be reusable for local files
   - Extract audio directly from MP4 without downloading

4. **`getoutvideo/__init__.py`**
   - Update `GetOutVideoAPI` methods to handle file paths
   - Add new convenience functions for local files

5. **`getoutvideo/models.py`**
   - Potentially add fields for local file metadata

## Implementation Approaches

### Option 1: Minimal Changes - URL/Path Detection (Recommended)
**Approach**: Detect if input is a file path or URL, route accordingly
- **Pros**: 
  - Maintains backward compatibility
  - Simple API - same methods work for both
  - Minimal code changes
- **Cons**: 
  - Slightly magical behavior
  - Path detection could have edge cases

### Option 2: Separate Methods for Local Files
**Approach**: Add new methods like `process_local_video()` 
- **Pros**: 
  - Explicit and clear API
  - No ambiguity between URLs and paths
- **Cons**: 
  - More API surface area
  - Code duplication

### Option 3: Unified Input Object
**Approach**: Create `VideoSource` class that wraps URL or file path
- **Pros**: 
  - Type-safe and extensible
  - Could add more sources later (cloud storage, etc.)
- **Cons**: 
  - Breaking API change
  - More complex for simple use cases

## Recommended Implementation (Option 1)

### Backend Changes

#### **File**: `getoutvideo/config.py`
- **Changes**: Add local file support flags to TranscriptConfig
- **Pattern**: Follow existing dataclass pattern
```python
@dataclass
class TranscriptConfig:
    # ... existing fields ...
    local_file_cleanup: bool = True  # Clean up extracted audio from MP4
    max_file_size_mb: int = 500  # Maximum MP4 file size to process
```

#### **File**: `getoutvideo/transcript_extractor.py`
- **Changes**: 
  - Add `_is_local_file()` method to detect file paths
  - Add `_extract_local_video()` method for MP4 processing
  - Modify `extract_transcripts()` to route based on input type
- **Pattern**: Follow existing `_extract_single_video()` structure

#### **File**: `getoutvideo/audio_transcriber.py`
- **Changes**:
  - Refactor `get_transcript_with_ai_stt()` to accept local files
  - Add `extract_audio_from_mp4()` function
  - Reuse existing segmentation and transcription logic
- **Pattern**: Follow existing audio processing pipeline

#### **File**: `getoutvideo/__init__.py`
- **Changes**:
  - Update `process_youtube_url()` to accept file paths (rename or alias)
  - Update docstrings to mention local file support
- **Pattern**: Maintain existing API signatures

### Implementation Details

1. **File Path Detection Logic**
```python
def _is_local_file(self, input_path: str) -> bool:
    """Detect if input is a local file path or URL."""
    # Check if it's a URL
    if input_path.startswith(('http://', 'https://', 'www.')):
        return False
    # Check if file exists and has video extension
    if os.path.exists(input_path):
        ext = os.path.splitext(input_path)[1].lower()
        return ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    return False
```

2. **Audio Extraction from MP4**
```python
def extract_audio_from_mp4(video_path: str, output_audio_path: str) -> bool:
    """Extract audio track from local video file."""
    try:
        # Use existing FFmpeg infrastructure
        audio = AudioSegment.from_file(video_path)
        audio.export(output_audio_path, format="m4a")
        return True
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False
```

3. **Local Video Processing Flow**
```python
def _extract_local_video(self, video_path: str, ...) -> VideoTranscript:
    """Extract transcript from local video file."""
    # 1. Get video metadata (title from filename)
    video_title = Path(video_path).stem
    
    # 2. Extract audio to temp file
    temp_audio = extract_audio_from_mp4(video_path)
    
    # 3. Use existing transcription pipeline
    transcript_text, duration = get_transcript_with_ai_stt(
        video_url=None,  # No URL for local files
        video_title=video_title,
        audio_path=temp_audio,  # Pass extracted audio
        cleanup_intermediate_files=self.config.transcript_config.local_file_cleanup
    )
    
    # 4. Create VideoTranscript object
    return VideoTranscript(
        title=video_title,
        url=f"file://{os.path.abspath(video_path)}",
        transcript_text=transcript_text,
        source="local_mp4",
        audio_duration_minutes=duration
    )
```

## Performance Considerations

*Ask user about these optimizations:*
- Do you want to limit maximum file size for local MP4s?
- Should we implement progress callbacks for large file processing?
- Do you want parallel processing for multiple local files?
- Should temporary audio files be cached for repeated processing?

## Testing Strategy
- Add unit tests for file path detection
- Test various video formats (MP4, AVI, MOV)
- Test error handling for corrupted/invalid files
- Test cleanup of temporary files
- Integration tests with actual video files

## Migration Path
1. The changes are backward compatible - existing YouTube URL processing remains unchanged
2. Users can start using file paths immediately after update
3. Documentation should clearly show both use cases

## Task List for Fullstack Developer

1. **Backend** - Modify `getoutvideo/config.py` to add local file configuration options
   - **Files**: `getoutvideo/config.py`
   - **Pattern**: Follow existing TranscriptConfig dataclass pattern
   - **Success**: New config options for local file handling are available

2. **Backend** - Update `getoutvideo/transcript_extractor.py` to detect and handle local files
   - **Files**: `getoutvideo/transcript_extractor.py`
   - **Pattern**: Follow existing `_parse_url()` and `_extract_single_video()` patterns
   - **Success**: Extractor can differentiate between URLs and file paths and process both

3. **Backend** - Refactor `getoutvideo/audio_transcriber.py` to support local MP4 extraction
   - **Files**: `getoutvideo/audio_transcriber.py`
   - **Pattern**: Reuse existing audio segmentation and transcription functions
   - **Success**: Can extract audio from local MP4 and transcribe it

4. **Backend** - Update `getoutvideo/__init__.py` API methods to accept file paths
   - **Files**: `getoutvideo/__init__.py`
   - **Pattern**: Maintain existing method signatures while extending functionality
   - **Success**: API transparently handles both URLs and local files

5. **Backend** - Update `getoutvideo/models.py` if additional metadata needed
   - **Files**: `getoutvideo/models.py`
   - **Pattern**: Follow existing VideoTranscript dataclass structure
   - **Success**: Model can represent local file transcripts with appropriate metadata

6. **Testing** - Add comprehensive tests for local file support
   - **Files**: `tests/test_local_files.py` (new), update existing test files
   - **Pattern**: Follow existing test patterns in test_api_interface.py
   - **Success**: All tests pass for both URL and local file scenarios

7. **Documentation** - Update examples to show local file usage
   - **Files**: `examples/local_file_usage.py` (new), update `examples/basic_usage.py`
   - **Pattern**: Follow existing example structure
   - **Success**: Clear examples demonstrate local MP4 processing

8. **Verification** - Run full test suite and linting
   - **Command**: `pytest tests/ && black --check getoutvideo/ && flake8 getoutvideo/`
   - **Success**: All tests pass, code is formatted, and linting is clean