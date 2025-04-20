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
- ffmpeg: Required by pydub and yt-dlp for audio processing. Must be installed
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


# Placeholder function for AI-based Speech-to-Text
def get_transcript_with_ai_stt(video_url, video_title, transcript_file_path, cleanup_intermediate_files=False):
    """
    Downloads audio from a YouTube video, segments it, transcribes the segments (placeholder),
    and combines the transcripts. Optionally cleans up intermediate audio files.

    Args:
        video_url (str): The URL of the YouTube video.
        video_title (str): A clean title for the video, used for naming files.
        transcript_file_path (str): The desired path for the final transcript text file.
                                    The audio and chunks will be placed in its parent directory.
        cleanup_intermediate_files (bool): If True, delete the downloaded audio and chunks
                                           after processing. Defaults to False.

    Returns:
        str or None: The combined transcript text if successful, otherwise None.
    """
    print(f"--- Starting transcription process for: {video_title} ---")
    
    # 1. Determine paths
    output_dir = Path(transcript_file_path).parent
    # Sanitize video_title for use in filename (replace invalid chars)
    safe_video_title = re.sub(r'[\\/*?:"<>|]', "_", video_title) # Basic sanitization
    audio_filename = f"{safe_video_title}.m4a"
    audio_path = output_dir / audio_filename
    chunk_paths = [] # Initialize chunk_paths in case segmentation fails

    print(f"Output directory: {output_dir}")
    print(f"Target audio path: {audio_path}")

    # Use a try...finally block to ensure cleanup happens even if errors occur *after* file creation
    try:
        # 2. Download audio
        if not download_youtube_audio(video_url, str(audio_path)):
            print(f"Failed to download audio for {video_url}. Aborting.")
            return None # No files to clean up if download fails

        # 3. Segment audio
        print(f"Segmenting audio file: {audio_path}")
        chunk_paths = audio_segmentation(str(audio_path), str(output_dir))
        if not chunk_paths:
            print("Audio segmentation failed or produced no chunks.")
            return None # No files to clean up if segmentation fails
        else:
            print(f"Created {len(chunk_paths)} audio chunks.")

        # 4. Transcribe each chunk (using OpenAI)
        all_transcripts = []
        print("Transcribing chunks using OpenAI gpt-4o-transcribe...")
        for i, chunk_path in enumerate(chunk_paths):
            print(f"Processing chunk {i+1}/{len(chunk_paths)}: {chunk_path}")
            transcript_text = transcribe_audio_chunk_openai(chunk_path)
            if transcript_text:
                all_transcripts.append(transcript_text)
            else:
                print(f"Warning: Transcription failed for chunk {chunk_path}")
                all_transcripts.append(f"[Transcription failed for {os.path.basename(chunk_path)}]\n")

        # 5. Combine transcripts
        full_transcript = "".join(all_transcripts)
        print("--- Transcription process finished ---")

        # 7. Return combined transcript
        return full_transcript

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


def detect_silence(audio_path, noise_thresh='-30dB', min_silence_len=0.5):
    """
    Detects silence segments in an audio file using ffmpeg's silence detection filter.
    
    This function uses ffmpeg's silencedetect filter to identify periods of silence
    in the audio file based on specified noise threshold and minimum silence duration.
    
    Args:
        audio_path (str): Path to the audio file to analyze
        noise_thresh (str): Noise threshold in dB for silence detection (default: '-30dB')
        min_silence_len (float): Minimum duration in seconds for a segment to be considered silence (default: 0.5)
        
    Returns:
        list: A list of tuples containing (start_time, end_time) for each detected silence segment
        
    The function:
    1. Runs ffmpeg with silencedetect filter to analyze the audio
    2. Parses the output to extract silence start and end times
    3. Returns a list of silence segments as (start, end) time tuples
    """
    cmd = [
        'ffmpeg', '-i', audio_path,
        '-af', f'silencedetect=noise={noise_thresh}:d={min_silence_len}',
        '-f', 'null', '-']

    # Set creation flags to hide console window on Windows
    creation_flags = 0
    if os.name == 'nt': # Check if running on Windows
        creation_flags = subprocess.CREATE_NO_WINDOW

    # Explicitly set encoding to utf-8 and handle errors
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               text=True, encoding='utf-8', errors='ignore',
                               creationflags=creation_flags) # Add creationflags here
    stderr = process.stderr.read()
    process.wait()

    pattern = r'silence_start: ([\d.]+)|silence_end: ([\d.]+)'
    events = re.findall(pattern, stderr)

    silences = []
    current_start = None
    for start, end in events:
        if start:
            current_start = float(start)
        elif end and current_start is not None:
            silences.append((current_start, float(end)))
            current_start = None
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
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load audio file
    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        print(f"Error loading audio file {audio_path}: {e}")
        return []

    # Detect silence and get timestamps
    silences = detect_silence(audio_path)

    # Create initial segments between silence points
    chunks = []
    last_end = 0.0
    for silence_start, silence_end in silences:
        # Convert to seconds if needed (pydub uses ms)
        start_sec = silence_start
        end_sec = silence_end
        duration = start_sec - last_end
        if duration >= 5.0:  # Skip segments shorter than 5 seconds
            chunks.append((last_end, start_sec))
        last_end = end_sec # Use the end of the silence as the start for the next potential chunk

    # Add final segment if needed
    if last_end < audio.duration_seconds:
         # Ensure the final segment isn't too short either, though this might clip the very end if it follows a silence closely.
         # Consider if a minimum length check is needed here too.
        final_segment_start = last_end
        final_segment_end = audio.duration_seconds
        if (final_segment_end - final_segment_start) >= 5.0: # Apply min duration here too?
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
            segment.export(chunk_output_path, format="ipod") # ipod corresponds to m4a/aac
            chunk_paths.append(chunk_output_path)
            print(f"Exported chunk: {chunk_output_path}")
        except Exception as e:
            print(f"Error exporting chunk {chunk_output_path}: {e}")

    return chunk_paths

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

def download_youtube_audio(video_url, output_path):
    """
    Downloads the audio track from a YouTube video URL as an M4A file.

    Args:
        video_url (str): The URL of the YouTube video.
        output_path (str): The full path (including filename and .m4a extension)
                           where the audio will be saved.

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
        return False
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        return False

# Example Usage (updated)
if __name__ == "__main__":
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Example URL
    test_title = "Rick Astley - Never Gonna Give You Up (Official Music Video)"
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