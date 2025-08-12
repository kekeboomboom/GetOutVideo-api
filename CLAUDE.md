# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WatchYTPL4Me** is a YouTube playlist to text transformation tool that converts video content into professional-quality documents. It extracts transcripts from YouTube videos/playlists and uses AI (Gemini API) to refine them into various formatted styles.

### Core Architecture

The application follows a multi-threaded PyQt5 GUI architecture:

1. **Main Application** (`main.pyw`): PyQt5 GUI with user controls and progress tracking
2. **Transcript Extraction Thread** (`main.pyw:1007-1259`): Downloads and extracts video transcripts  
3. **Gemini Processing Thread** (`main.pyw:1261-1522`): Processes transcripts using Gemini API
4. **Audio Transcription Module** (`ytvideo2txt.py`): Fallback AI STT using OpenAI's gpt-4o-transcribe
5. **Prompt Templates** (`prompts.py`): Defines refinement styles and prompts

### Key Processing Flow

1. **Input Validation**: URL format, API keys, output directories, refinement styles
2. **Transcript Extraction**: 
   - Primary: YouTube Transcript API via `youtube_transcript_api`
   - Fallback: Audio download → segmentation → OpenAI STT transcription
3. **Text Refinement**: Gemini API processes transcript chunks with style-specific prompts
4. **Output Generation**: Creates markdown files for each video × style combination

## Common Commands

### Running the Application
```bash
# Method 1: Direct execution (recommended)
python main.py

# Method 2: Using .pyw file (Windows GUI mode)
# Double-click main.pyw or create shortcut
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

**Note**: Requires `ffmpeg` to be installed and accessible in system PATH for audio processing.

### Environment Setup
Create a `.env` file with:
```
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
LANGUAGE=English
```

### Testing Audio Transcription Standalone
```bash
python ytvideo2txt.py
```

## Development Guidelines

### Thread Safety
- UI updates must use Qt signals (`pyqtSignal`) from worker threads
- Both `TranscriptExtractionThread` and `GeminiProcessingThread` include `stop()` methods
- Always check `self._is_running` in thread loops for graceful cancellation

### File Naming and Sanitization
- Video titles are sanitized using `_sanitize_filename()` in `main.pyw:1490-1521`
- Output files follow pattern: `{sanitized_title} [{style_name}].md`
- Invalid filename characters are removed/replaced

### API Integration
- **Gemini API**: Uses `google-generativeai` library, configurable model selection
- **OpenAI API**: Uses official `openai` client for audio transcription
- **YouTube API**: Uses `youtube_transcript_api` and `pytubefix` for video access

### Error Handling Patterns
- Each thread emits `error_occurred` signals with descriptive messages
- File operations include try-catch with user-friendly error reporting
- API failures trigger fallback mechanisms (e.g., AI STT when transcript unavailable)

### Configuration and Customization
- **Chunk Size**: Configurable via slider (default 70,000 words)
- **Refinement Styles**: Defined in `prompts.py`, easily customizable
- **Output Language**: User-configurable, injected into prompts via `[Language]` placeholder
- **Cookie Support**: Optional browser cookie file for accessing restricted content

### Key Dependencies
- `PyQt5`: GUI framework
- `pytubefix`: YouTube video access (preferred over pytube)
- `youtube-transcript-api`: Transcript extraction
- `google-generativeai`: Gemini API integration
- `openai`: Audio transcription fallback
- `yt-dlp`: Audio downloading
- `pydub`: Audio processing and segmentation
- `ffmpeg-python`: Audio manipulation

### File Structure Notes
- No additional subdirectories - all core files in root
- `Images/` contains UI screenshots for README
- `.env` file for API keys (not tracked in git)
- Output files generated in user-specified directories