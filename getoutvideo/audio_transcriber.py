"""
Downloads audio from a YouTube video, segments it based on silence, transcribes
each segment using OpenAI's transcription service (gpt-4o-transcribe model),
combines the transcripts, and saves the result to a text file.

This script orchestrates the entire process, from fetching the audio to generating
the final transcript. It handles intermediate file management and offers an option
to clean up temporary audio files.

Dependencies:
- Python 3.x
- yt-dlp: For downloading YouTube audio (`pip install yt-dlp`)
- pydub: For audio manipulation and segmentation (`pip install pydub`)
- openai: Official OpenAI Python client (`pip install openai`)
- ffmpeg-python: Python bindings for FFmpeg (`pip install ffmpeg-python`)
- ffmpeg: Required by pydub, yt-dlp, and ffmpeg-python for audio processing. Must be installed
  and accessible in the system's PATH. (Download from https://ffmpeg.org/)

Environment Variables:
- OPENAI_API_KEY: Your OpenAI API key must be set as an environment variable
  for the transcription step to work.

Usage:
1. Ensure all dependencies are installed and ffmpeg is in the PATH.
2. Set the OPENAI_API_KEY environment variable.
3. Modify the example URL and title in the `if __name__ == "__main__":` block
   at the end of the script, or integrate the `get_transcript_with_ai_stt`
   function into your own workflow.
4. Run the script: `python ytvideo2txt.py`

The script will create an 'output_transcripts' subdirectory in the same
directory as the script, where the final transcript file and intermediate
audio files (if not cleaned up) will be stored.
"""

from pydub import AudioSegment
import re, os, subprocess
from pathlib import Path
import yt_dlp
from openai import OpenAI
import ffmpeg
import sys

# Import centralized URLs
try:
    from .config_urls import FALLBACK_TEST_URL
except ImportError:
    # Fallback if not available
    FALLBACK_TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


# Placeholder function for AI-based Speech-to-Text
def get_transcript_with_ai_stt(video_url, video_title, cookie_path, transcript_file_path, cleanup_intermediate_files=False):
    """
    Downloads audio from a YouTube video, segments it, transcribes the segments (placeholder),
    and combines the transcripts. Optionally cleans up intermediate audio files.

    Args:
        video_url (str): The URL of the YouTube video.
        video_title (str): A clean title for the video, used for naming files.
        cookie_path (str or None): Path to the cookie file for yt-dlp authentication.
        transcript_file_path (str): The desired path for the final transcript text file.
                                    The audio and chunks will be placed in its parent directory.
        cleanup_intermediate_files (bool): If True, delete the downloaded audio and chunks
                                           after processing. Defaults to False.

    Returns:
        tuple: (combined_transcript_text, duration_in_minutes) if successful, 
               (None, None) if failed.
    """
    print(f"--- Starting transcription process for: {video_title} ---")
    
    # 1. Determine paths
    # Ensure transcript_file_path is a string before using Path
    if not isinstance(transcript_file_path, str):
        print(f"Error: transcript_file_path must be a string, got {type(transcript_file_path)}")
        return None
    try:
        output_dir = Path(transcript_file_path).parent
    except TypeError as e:
         print(f"Error creating Path object from transcript_file_path: {e}. Value was: {transcript_file_path}")
         return None

    # Sanitize video_title for use in filename (replace invalid chars)
    safe_video_title = re.sub(r'[\\/*?:"<>|]', "_", video_title) # Basic sanitization
    audio_filename = f"{safe_video_title}.m4a"
    audio_path = output_dir / audio_filename
    chunk_paths = [] # Initialize chunk_paths in case segmentation fails
    audio_duration_minutes = 0.0

    print(f"Output directory: {output_dir}")
    print(f"Target audio path: {audio_path}")

    # Use a try...finally block to ensure cleanup happens even if errors occur *after* file creation
    try:
        # 2. Download audio - Pass cookie_path here
        if not download_youtube_audio(video_url, str(audio_path), cookie_path=cookie_path):
            print(f"Failed to download audio for {video_url}. Aborting.")
            return None, None # No files to clean up if download fails

        # Get audio duration for cost calculation
        try:
            audio = AudioSegment.from_file(str(audio_path))
            audio_duration_minutes = len(audio) / 1000 / 60  # Convert ms to minutes
            print(f"Audio duration: {audio_duration_minutes:.2f} minutes")
        except Exception as e:
            print(f"Warning: Could not get audio duration: {e}")

        # 3. Segment audio
        print(f"Segmenting audio file: {audio_path}")
        chunk_paths = audio_segmentation(str(audio_path), str(output_dir))
        if not chunk_paths:
            print("Audio segmentation failed or produced no chunks.")
            # Don't return immediately, allow cleanup
        else:
            print(f"Created {len(chunk_paths)} audio chunks.")

        # 4. Transcribe each chunk (using OpenAI) - Only if chunks were created
        all_transcripts = []
        if chunk_paths:
            print("Transcribing chunks using OpenAI gpt-4o-transcribe...")
            for i, chunk_path in enumerate(chunk_paths):
                print(f"Processing chunk {i+1}/{len(chunk_paths)}: {chunk_path}")
                transcript_text = transcribe_audio_chunk_openai(chunk_path)
                if transcript_text:
                    all_transcripts.append(transcript_text)
                else:
                    print(f"Warning: Transcription failed for chunk {chunk_path}")
                    all_transcripts.append(f"[Transcription failed for {os.path.basename(chunk_path)}]\n")
        else:
            print("Skipping transcription as no audio chunks were created.")
            return None, None # If no chunks, no transcript can be generated

        # 5. Combine transcripts
        full_transcript = "".join(all_transcripts)
        print("--- Transcription process finished ---")

        # 7. Return combined transcript and duration
        return full_transcript, audio_duration_minutes

    finally:
        # 6. Optional: Clean up intermediate files (original audio and chunks)
        if cleanup_intermediate_files:
            print("\n--- Cleaning up intermediate files ---")
            # Clean up original audio
            if os.path.exists(audio_path):
                try:
                    print(f"Deleting original audio: {audio_path}")
                    os.remove(audio_path)
                except OSError as e:
                    print(f"Error deleting original audio {audio_path}: {e}")
            else:
                 # This might happen if download failed but we still entered the finally block
                 print(f"Original audio not found for cleanup: {audio_path}")


            # Clean up chunks
            if chunk_paths:
                print(f"Deleting {len(chunk_paths)} chunks...")
                deleted_count = 0
                for chunk_path in chunk_paths:
                    if os.path.exists(chunk_path):
                        try:
                            os.remove(chunk_path)
                            deleted_count += 1
                        except OSError as e:
                            print(f"Error deleting chunk {chunk_path}: {e}")
                    else:
                        print(f"Chunk not found for cleanup: {chunk_path}")
                print(f"Deleted {deleted_count} chunk files.")
            else:
                print("No chunk paths recorded for cleanup.")
            print("--- Cleanup finished ---")
        else:
            print("\n--- Skipping cleanup of intermediate files ---")


def detect_silence(audio_path, noise_thresh='-30dB', min_silence_len=1.5):
    """
    Detects silence segments in an audio file using ffmpeg's silence detection filter
    via the ffmpeg-python library.

    Args:
        audio_path (str): Path to the audio file to analyze.
        noise_thresh (str): Noise threshold in dB for silence detection (default: '-30dB').
        min_silence_len (float): Minimum duration in seconds for a segment to be considered silence (default: 1.5).

    Returns:
        list: A list of tuples containing (start_time, end_time) for each detected silence segment.
    """
    # Set creation flags to hide console window only on Windows
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW

    try:
        # Use ffmpeg-python to build and run the command
        # quiet=True suppresses ffmpeg's own logs but not silencedetect output to stderr
        out, err = (
            ffmpeg
            .input(audio_path)
            .filter('silencedetect', noise=noise_thresh, d=min_silence_len)
            .output('-', format='null') # Output to null device
            # Pass the creationflags if on Windows
            .run(capture_stdout=True, capture_stderr=True, quiet=True, creationflags=creation_flags)
        )
        # silencedetect logs to stderr
        stderr = err.decode('utf-8', errors='ignore')

    except ffmpeg.Error as e:
        # Log the error output from ffmpeg if it fails
        print(f"ffmpeg-python error during silence detection:")
        # Try decoding stderr for more detailed error info
        try:
            print(e.stderr.decode('utf-8', errors='ignore'))
        except Exception: # If decoding stderr itself fails
             print("Could not decode ffmpeg stderr.")
        return []
    except FileNotFoundError:
        # Handle case where ffmpeg executable is not found
        print("Error: ffmpeg executable not found. Make sure ffmpeg is installed and in your PATH.")
        return []
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred during silence detection: {e}")
        return []

    # Parse the stderr output for silence markers (same logic as before)
    pattern = r'silence_start: ([\d.]+)|silence_end: ([\d.]+)'
    events = re.findall(pattern, stderr)

    silences = []
    current_start = None
    for start, end in events:
        if start:
            current_start = float(start)
        elif end and current_start is not None:
            # Handle potential edge case where end time might be slightly before start time due to precision
            end_time = float(end)
            if end_time > current_start:
                 silences.append((current_start, end_time))
            else:
                 print(f"Warning: Detected silence end time ({end_time}) not after start time ({current_start}). Skipping this interval.")
            current_start = None # Reset regardless of whether it was added

    # Handle case where audio might end during a silence detection
    if current_start is not None:
        # We don't have an explicit end, maybe log or decide if this needs handling
        print(f"Warning: Silence started at {current_start} but no end detected before file end.")
        # Option: Add it assuming it ends at audio duration? Requires getting audio duration.
        # For now, we'll just ignore silences that don't have an end marker.


    return silences


def audio_segmentation(audio_path, output_dir):
    """
    Segments an audio file into chunks based on silence detection and duration limits.
    
    Args:
        audio_path (str): Path to the input audio file to be segmented.
        output_dir (str): Directory where the audio chunks will be saved.
        
    Returns:
        list: A list of file paths for the created audio chunks.
        
    Output:
        Creates numbered m4a files ({base_name}_chunk_XX.m4a) in the specified output_dir.
    """
    # --- Start Monkey Patch to suppress ffmpeg console window ---
    original_popen = subprocess.Popen
    if sys.platform == "win32":
        # Define a wrapper for Popen that adds CREATE_NO_WINDOW
        def patched_popen(*args, **kwargs):
            creationflags = kwargs.get('creationflags', 0)
            # Add the flag to prevent console window
            kwargs['creationflags'] = creationflags | subprocess.CREATE_NO_WINDOW
            # Call the original Popen with modified kwargs
            return original_popen(*args, **kwargs)
        # Replace the global Popen with our patched version
        subprocess.Popen = patched_popen
    # --- End Monkey Patch Setup ---

    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Load audio file (pydub uses ffmpeg here)
        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            print(f"Error loading audio file {audio_path}: {e}")
            return [] # Exit early if loading fails

        # Detect silence and get timestamps
        # Note: detect_silence already has its own suppression logic
        silences = detect_silence(audio_path, min_silence_len=1.5) 

        # Create initial segments between silence points
        chunks = []
        last_end = 0.0
        MIN_CHUNK_DURATION_SEC = 2.5 # Define the minimum duration threshold
        for silence_start, silence_end in silences:
            # Convert to seconds if needed (pydub uses ms)
            start_sec = silence_start
            end_sec = silence_end
            duration = start_sec - last_end
            if duration >= MIN_CHUNK_DURATION_SEC:  # Use the threshold variable
                chunks.append((last_end, start_sec))
            last_end = end_sec # Use the end of the silence as the start for the next potential chunk

        # Add final segment if needed
        if last_end < audio.duration_seconds:
            # Ensure the final segment isn't too short either
            final_segment_start = last_end
            final_segment_end = audio.duration_seconds
            if (final_segment_end - final_segment_start) >= MIN_CHUNK_DURATION_SEC: # Use the threshold variable here too
                chunks.append((final_segment_start, final_segment_end))
            # else: # Optional: handle very short final segments if needed
            #     print(f"Skipping very short final segment: {final_segment_end - final_segment_start:.2f}s")


        # Second pass: Split segments longer than 10 minutes
        final_chunks_times = []
        MAX_LEN_SEC = 600  # 10 minutes in seconds
        for start_sec, end_sec in chunks:
            current_start = start_sec
            while (end_sec - current_start) > MAX_LEN_SEC:
                final_chunks_times.append((current_start, current_start + MAX_LEN_SEC))
                current_start += MAX_LEN_SEC
            # Add the remaining part of the chunk (or the whole chunk if it was shorter than MAX_LEN_SEC)
            if end_sec > current_start: # Ensure there's actually a remaining part
                final_chunks_times.append((current_start, end_sec))


        # Export each segment as m4a file and collect paths
        chunk_paths = []
        audio_base_name = Path(audio_path).stem # Get filename without extension
        for i, (start_sec, end_sec) in enumerate(final_chunks_times):
            segment = audio[start_sec * 1000:end_sec * 1000] # pydub uses milliseconds
            chunk_filename = f"{audio_base_name}_chunk_{i+1:02d}.m4a"
            chunk_output_path = os.path.join(output_dir, chunk_filename)
            try:
                # pydub uses ffmpeg here for exporting
                segment.export(chunk_output_path, format="ipod") # ipod corresponds to m4a/aac
                chunk_paths.append(chunk_output_path)
                print(f"Exported chunk: {chunk_output_path}")
            except Exception as e:
                print(f"Error exporting chunk {chunk_output_path}: {e}")

        return chunk_paths # Return the paths list

    finally:
        # --- Restore original Popen ---
        # Crucial to restore the original function to avoid affecting other parts of the script
        # or other libraries unexpectedly.
        subprocess.Popen = original_popen
        # --- End Restore ---

def transcribe_audio_chunk_openai(audio_chunk_path):
    """
    Transcribes an audio chunk using OpenAI's GPT-4o-transcribe model via the official SDK.

    Args:
        audio_chunk_path (str): Path to the audio chunk file (.m4a).

    Returns:
        str: Transcribed text or None if transcription failed.
    """
    # OpenAI client will automatically use the OPENAI_API_KEY environment variable
    try:
        client = OpenAI()
        
        # Open the audio file
        with open(audio_chunk_path, "rb") as audio_file:
            # Use the OpenAI SDK to transcribe the audio
            response = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file,
            )
            
            # The response is already the text content when using response_format="text"
            transcript = response.text
            print(f"Transcription successful: {len(transcript)} characters")
            return transcript
            
    except Exception as e:
        print(f"Exception during transcription: {e}")
        return None

def download_youtube_audio(video_url, output_path, cookie_path=None):
    """
    Downloads the audio track from a YouTube video URL as an M4A file.

    Args:
        video_url (str): The URL of the YouTube video.
        output_path (str): The full path (including filename and .m4a extension)
                           where the audio will be saved.
        cookie_path (str, optional): Path to the cookie file to use for authentication. Defaults to None.

    Returns:
        bool: True if download was successful, False otherwise.
    """
    output_dir = os.path.dirname(output_path)
    output_filename_no_ext = Path(output_path).stem
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # yt-dlp options
    # We specify the output directory and filename template separately
    # We request the best audio format and convert it to m4a
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, f'{output_filename_no_ext}.%(ext)s'), # Template for yt-dlp
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a', # Specify m4a codec
            'preferredquality': '128', # Lowered bitrate to 128kbps for smaller files while retaining good quality
        }],
        'quiet': False, # Set to True for less output
        'no_warnings': True,
        'noprogress': False, # Set to True to disable progress bar
        'noplaylist': True, # Ensure only single video is downloaded if URL points to playlist item
    }

    # Conditionally add the cookie file option if the path is provided and exists
    if cookie_path and os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path
        print(f"Using cookie file: {cookie_path}")
    elif cookie_path:
        print(f"Warning: Cookie file specified but not found at {cookie_path}. Proceeding without cookies.")

    print(f"Attempting to download audio from: {video_url}")
    print(f"Saving to: {output_path}") # The final path after conversion

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Check if the target file already exists (after potential conversion)
            if os.path.exists(output_path):
                 print(f"Audio file already exists: {output_path}")
                 return True
            
            # yt-dlp handles the renaming based on postprocessor settings
            error_code = ydl.download([video_url]) 
            if error_code == 0:
                 # Verify the final expected file exists after postprocessing
                 if os.path.exists(output_path):
                     print(f"Audio downloaded and converted successfully: {output_path}")
                     return True
                 else:
                     # This might happen if the downloaded extension wasn't correctly handled or conversion failed
                     print(f"Download seemed successful, but expected output file not found: {output_path}")
                     # Optional: Look for intermediate files if needed for debugging
                     return False
            else:
                print(f"yt-dlp download failed with error code: {error_code}")
                return False
                
    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading audio: {e}")
        # Check if the error message indicates an authentication issue
        if 'Authentication required' in str(e) or 'sign in' in str(e).lower():
             print("Authentication error. If this is a private or age-restricted video, try providing a valid cookie file.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        return False

# Example Usage (updated)
if __name__ == "__main__":
    test_url = FALLBACK_TEST_URL  # Example URL from centralized config
    test_title = "Rick Astley - Never Gonna Give You Up (Official Music Video)"
    # Example cookie file path (replace with your actual path if testing)
    test_cookie_path = "cookie.txt" # Assumes cookie.txt is in the same directory

    # Create a subdirectory for output in the script's location
    script_dir = Path(__file__).parent
    output_subdir = script_dir / "output_transcripts"
    output_subdir.mkdir(parents=True, exist_ok=True)

    # Sanitize the title first
    safe_file_title = re.sub(r'[\\/*?:"<>|]', '_', test_title) # Corrected regex and sanitization

    # Define the path for the final transcript file using the sanitized title
    final_transcript_path = output_subdir / f"{safe_file_title}_transcript.txt"

    print(f"Running test transcription for: {test_title}")
    print(f"Transcript will be attempted at: {final_transcript_path}")

    # Call the main function - set cleanup_intermediate_files=True to enable cleanup
    # Set it to False or omit it to keep the files (default)
    PERFORM_CLEANUP = False # Set to True to test cleanup
    
    result_transcript = get_transcript_with_ai_stt(
        test_url, 
        test_title, 
        test_cookie_path, # Pass the cookie path here
        str(final_transcript_path), 
        cleanup_intermediate_files=PERFORM_CLEANUP 
    )

    if result_transcript:
        print("\n--- Combined Placeholder Transcript ---")
        print(result_transcript)
        # Save the result to the file
        try:
            with open(final_transcript_path, 'w', encoding='utf-8') as f:
                 f.write(result_transcript)
            print(f"\nPlaceholder transcript saved to: {final_transcript_path}")
        except IOError as e:
            print(f"\nError saving transcript file: {e}")
    else:
        print("\nTranscription process failed.")