"""
Transcript extraction functionality for the WatchYTPL4Me API.

This module provides the core transcript extraction logic adapted from
the original GUI application's TranscriptExtractionThread class.
"""

import os
from typing import List, Optional, Callable
from pytubefix import Playlist, YouTube
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnplayable

from .config import APIConfig
from .models import VideoTranscript
from .exceptions import TranscriptExtractionError, YouTubeAccessError, AudioProcessingError
from .utils import safe_progress_callback, safe_status_callback

# Import the AI STT fallback function from the root module
import sys
from . import audio_transcriber


class TranscriptExtractor:
    """
    Extracts transcripts from YouTube videos and playlists.
    
    This class provides the core transcript extraction functionality,
    supporting both individual videos and playlists with range selection.
    """
    
    # OpenAI Whisper pricing (as of current rates)
    WHISPER_COST_PER_MINUTE = 0.006  # $0.006 per minute
    
    def __init__(self, config: APIConfig):
        """
        Initialize the transcript extractor.
        
        Args:
            config: API configuration containing transcript settings
        """
        self.config = config
        self._cancelled = False
    
    def cancel(self) -> None:
        """Cancel the current extraction operation."""
        self._cancelled = True
    
    def extract_transcripts(self, 
                          url: str, 
                          progress_callback: Optional[Callable[[int], None]] = None,
                          status_callback: Optional[Callable[[str], None]] = None) -> List[VideoTranscript]:
        """
        Extract transcripts from a YouTube URL (playlist or single video).
        
        Args:
            url: YouTube URL (playlist or single video)
            progress_callback: Optional callback for progress updates (0-100)
            status_callback: Optional callback for status messages
            
        Returns:
            List[VideoTranscript]: List of extracted transcripts
            
        Raises:
            TranscriptExtractionError: If extraction fails
        """
        self._cancelled = False
        
        print(f"DEBUG: extract_transcripts called with URL: {url}")
        
        try:
            safe_status_callback(status_callback, f"Starting transcript extraction for: {url}")
            print(f"DEBUG: Starting transcript extraction...")
            
            # Parse URL and get video URLs
            print(f"DEBUG: Parsing URL...")
            all_video_urls, playlist_name = self._parse_url(url, status_callback)
            print(f"DEBUG: Parsed URL - found {len(all_video_urls)} video URLs, playlist name: {playlist_name}")
            
            # Apply range filtering
            config = self.config.transcript_config
            slice_start = max(0, config.start_index - 1)
            slice_end = None if config.end_index == 0 else config.end_index
            
            print(f"DEBUG: Range filtering - start_index: {config.start_index}, end_index: {config.end_index}")
            print(f"DEBUG: Slice parameters - slice_start: {slice_start}, slice_end: {slice_end}")
            
            video_urls_to_process = all_video_urls[slice_start:slice_end]
            total_videos = len(video_urls_to_process)
            
            print(f"DEBUG: After range filtering - {total_videos} videos to process")
            for i, video_url in enumerate(video_urls_to_process):
                print(f"DEBUG: Video {i+1}: {video_url}")
            
            if total_videos == 0:
                print(f"DEBUG: No videos to process, returning empty list")
                safe_status_callback(status_callback, "No videos found in the specified range.")
                return []
            
            safe_status_callback(status_callback, 
                               f"Processing {total_videos} videos (range {config.start_index} "
                               f"to {config.end_index if config.end_index != 0 else 'End'} "
                               f"of {len(all_video_urls)}).")
            
            # Extract transcripts
            transcripts = []
            for index, video_url in enumerate(video_urls_to_process, 1):
                if self._cancelled:
                    safe_status_callback(status_callback, "Extraction cancelled by user.")
                    break
                
                print(f"DEBUG: Processing video {index}/{total_videos}: {video_url}")
                
                original_index = slice_start + index
                transcript = self._extract_single_video(video_url, original_index, index, 
                                                       total_videos, status_callback)
                
                if transcript:
                    print(f"DEBUG: Successfully extracted transcript for video {index}: {transcript.title[:50]}...")
                    transcripts.append(transcript)
                else:
                    print(f"DEBUG: Failed to extract transcript for video {index}")
                
                # Update progress
                progress_percent = int((index / total_videos) * 100)
                safe_progress_callback(progress_callback, progress_percent)
            
            print(f"DEBUG: Extraction completed - {len(transcripts)} total transcripts extracted")
            safe_status_callback(status_callback, f"Extraction completed. {len(transcripts)} transcripts extracted.")
            return transcripts
            
        except Exception as e:
            error_msg = f"Failed to extract transcripts: {str(e)}"
            print(f"DEBUG: Exception in extract_transcripts: {error_msg}")
            print(f"DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"DEBUG: Exception traceback:")
            traceback.print_exc()
            safe_status_callback(status_callback, error_msg)
            raise TranscriptExtractionError(error_msg) from e
    
    def _parse_url(self, url: str, status_callback: Optional[Callable[[str], None]] = None) -> tuple[List[str], str]:
        """
        Parse YouTube URL and extract video URLs and playlist name.
        
        Args:
            url: YouTube URL
            status_callback: Optional callback for status messages
            
        Returns:
            tuple: (list of video URLs, playlist/video name)
            
        Raises:
            YouTubeAccessError: If URL parsing fails
        """
        try:
            if "playlist?list=" in url:
                # Handle playlist
                playlist = Playlist(url)
                try:
                    all_video_urls = list(playlist.video_urls)
                    playlist_name = playlist.title
                    safe_status_callback(status_callback, 
                                       f"Found playlist: {playlist_name} with {len(all_video_urls)} videos.")
                    return all_video_urls, playlist_name
                    
                except KeyError as ke:
                    error_msg = (f"Extraction error (Accessing Playlist Details): {str(ke)}. "
                               "YouTube structure likely changed. Update pytubefix or check issues.")
                    raise YouTubeAccessError(error_msg) from ke
                except Exception as e:
                    error_msg = f"Extraction error (Accessing Playlist Properties): {str(e)}. URL: {url}"
                    raise YouTubeAccessError(error_msg) from e
                    
            elif "watch?v=" in url:
                # Handle single video
                try:
                    yt = YouTube(url)
                    playlist_name = yt.title
                    safe_status_callback(status_callback, f"Processing single video: {playlist_name}")
                    return [url], playlist_name
                except Exception as e:
                    safe_status_callback(status_callback, 
                                       f"Processing single video (Could not get title: {str(e)}). URL: {url}")
                    return [url], "Single Video"
            else:
                raise YouTubeAccessError(f"Invalid URL format: {url}")
                
        except YouTubeAccessError:
            raise
        except Exception as e:
            raise YouTubeAccessError(f"Failed to parse URL {url}: {str(e)}") from e
    
    def _extract_single_video(self, video_url: str, original_index: int, 
                            current_index: int, total_videos: int,
                            status_callback: Optional[Callable[[str], None]] = None) -> Optional[VideoTranscript]:
        """
        Extract transcript from a single video.
        
        Args:
            video_url: YouTube video URL
            original_index: Original index in the playlist
            current_index: Current processing index (1-based)
            total_videos: Total number of videos being processed
            status_callback: Optional callback for status messages
            
        Returns:
            VideoTranscript: Extracted transcript or None if extraction failed
        """
        print(f"DEBUG: _extract_single_video called for {video_url}")
        
        video_title = f"Video_{original_index}"
        transcript_text = None
        transcript_source = "Unknown"
        audio_duration_minutes = 0.0
        openai_cost = 0.0
        
        try:
            # Get video title
            try:
                print(f"DEBUG: Getting video title...")
                yt = YouTube(video_url)
                video_title = yt.title
                print(f"DEBUG: Got video title: {video_title}")
            except Exception as e:
                print(f"DEBUG: Failed to get video title: {str(e)}")
                safe_status_callback(status_callback,
                                   f"Warning: Could not get title for video {original_index} ({video_url}): {str(e)}")
            
            # Extract video ID
            print(f"DEBUG: Extracting video ID from URL...")
            video_id = video_url.split("?v=")[1].split("&")[0]
            print(f"DEBUG: Video ID: {video_id}")
            
            # Attempt standard transcript extraction
            try:
                print(f"DEBUG: Attempting standard transcript extraction...")
                safe_status_callback(status_callback,
                                   f"Attempting standard transcript extraction for video {current_index}/{total_videos} "
                                   f"(Original Index: {original_index}) - Title: {video_title[:50]}...")
                
                fetched_transcript = YouTubeTranscriptApi().fetch(video_id)
                transcript_text = ' '.join([t.text for t in fetched_transcript])
                transcript_source = "youtube_api"
                
                print(f"DEBUG: Successfully extracted transcript via YouTube API, length: {len(transcript_text)}")
                safe_status_callback(status_callback,
                                   f"Successfully extracted transcript via YouTube API for video {current_index}/{total_videos}.")
                
            except (TranscriptsDisabled, NoTranscriptFound, VideoUnplayable) as e:
                print(f"DEBUG: Standard transcript failed with {type(e).__name__}: {str(e)}")
                print(f"DEBUG: AI fallback enabled: {self.config.transcript_config.use_ai_fallback}")
                print(f"DEBUG: OpenAI key available: {'Yes' if self.config.openai_api_key else 'No'}")
                
                # Fallback to AI STT if enabled and OpenAI key available
                if self.config.transcript_config.use_ai_fallback and self.config.openai_api_key:
                    safe_status_callback(status_callback,
                                       f"Standard transcript unavailable for video {current_index}/{total_videos} "
                                       f"({type(e).__name__}). Attempting AI STT fallback...")
                    
                    try:
                        print(f"DEBUG: Attempting AI STT fallback...")
                        # Use the AI STT fallback
                        result = audio_transcriber.get_transcript_with_ai_stt(
                            video_url, video_title, self.config.transcript_config.cookie_path, 
                            None,  # We don't need transcript_file_path for API usage
                            self.config.transcript_config.cleanup_temp_files
                        )
                        
                        if result and result[0]:  # Check if we got a tuple with transcript
                            transcript_text, audio_duration_minutes = result
                            transcript_source = "ai_stt"
                            openai_cost = audio_duration_minutes * self.WHISPER_COST_PER_MINUTE
                            print(f"DEBUG: AI STT fallback successful, length: {len(transcript_text)}")
                            print(f"DEBUG: Audio duration: {audio_duration_minutes:.2f} min, Cost: ${openai_cost:.4f}")
                            safe_status_callback(status_callback,
                                               f"Successfully obtained transcript via AI STT for video {current_index}/{total_videos}. "
                                               f"Duration: {audio_duration_minutes:.2f} min, Cost: ${openai_cost:.4f}")
                        else:
                            print(f"DEBUG: AI STT fallback returned no transcript")
                            safe_status_callback(status_callback,
                                               f"AI STT fallback failed or returned no transcript for video {current_index}/{total_videos}.")
                            
                    except Exception as ai_e:
                        print(f"DEBUG: AI STT fallback failed with exception: {str(ai_e)}")
                        safe_status_callback(status_callback,
                                           f"Error during AI STT fallback for video {current_index}/{total_videos}: {str(ai_e)}")
                        raise AudioProcessingError(f"AI STT fallback failed: {str(ai_e)}") from ai_e
                else:
                    print(f"DEBUG: AI fallback not attempted (disabled or no OpenAI key)")
                    safe_status_callback(status_callback,
                                       f"Standard transcript unavailable for video {current_index}/{total_videos} "
                                       f"and AI fallback is disabled or OpenAI key not provided.")
                    
            except Exception as e:
                print(f"DEBUG: Unexpected error during transcript extraction: {type(e).__name__}: {str(e)}")
                safe_status_callback(status_callback,
                                   f"Error getting transcript via Standard API for video {current_index}/{total_videos} "
                                   f"({type(e).__name__}): {str(e)}")
                
            # Create VideoTranscript object if we got transcript text
            if transcript_text:
                print(f"DEBUG: Creating VideoTranscript object with transcript of length {len(transcript_text)}")
                safe_status_callback(status_callback,
                                   f"Processed video {current_index}/{total_videos} "
                                   f"(Original Index: {original_index}) - Source: {transcript_source}")
                
                return VideoTranscript(
                    title=video_title,
                    url=video_url,
                    transcript_text=transcript_text,
                    source=transcript_source,
                    audio_duration_minutes=audio_duration_minutes,
                    openai_cost=openai_cost
                )
            else:
                print(f"DEBUG: No transcript text obtained, returning None")
                safe_status_callback(status_callback,
                                   f"Skipping video {current_index}/{total_videos} "
                                   f"(Original Index: {original_index}) - Could not obtain transcript from any source.")
                return None
                
        except Exception as e:
            print(f"DEBUG: Exception in _extract_single_video: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"DEBUG: Exception traceback:")
            traceback.print_exc()
            safe_status_callback(status_callback,
                               f"Error processing video {current_index}/{total_videos} "
                               f"(Original Index: {original_index}, URL: {video_url}): {str(e)}")
            return None