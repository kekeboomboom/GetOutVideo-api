"""
Usage examples for the WatchYTPL4Me API.

This module demonstrates various ways to use the API for different use cases,
from simple one-line processing to advanced configuration scenarios.
"""

import os
from dotenv import load_dotenv

# Import the main API components
from api import (
    WatchYTPL4MeAPI, 
    process_youtube_playlist, 
    extract_transcripts_only,
    APIConfig, 
    TranscriptConfig, 
    ProcessingConfig,
    load_api_from_env
)

# Load environment variables from .env file
load_dotenv()


def example_1_simple_usage():
    """
    Example 1: Simple one-line usage for most common scenarios.
    
    This is the fastest way to get started - just provide a URL, output directory,
    and your Gemini API key. Uses default settings for everything else.
    """
    print("=== Example 1: Simple Usage ===")
    
    # Process an entire playlist with default settings
    output_files = process_youtube_playlist(
        url="https://www.youtube.com/playlist?list=PLrAXtmRdnEQy5GKLFVRLt17vTrZNyMLVa",
        output_dir="./output/simple_example",
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")  # Optional, for AI fallback
    )
    
    print(f"Generated {len(output_files)} files:")
    for file_path in output_files:
        print(f"  - {file_path}")


def example_2_single_video():
    """
    Example 2: Processing a single YouTube video with specific styles.
    """
    print("\n=== Example 2: Single Video with Specific Styles ===")
    
    # Process just one video with only summary and Q&A styles
    output_files = process_youtube_playlist(
        url="https://www.youtube.com/watch?v=7gp7GkPE-tI&feature=youtu.be",
        output_dir="./output/single_video",
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),  # Enable AI fallback
        styles=["Summary", "Q&A Generation"],  # Only these two styles
        output_language="English"
    )
    
    print(f"Generated {len(output_files)} files:")
    for file_path in output_files:
        print(f"  - {file_path}")


def example_3_advanced_configuration():
    """
    Example 3: Advanced usage with custom configuration.
    """
    print("\n=== Example 3: Advanced Configuration ===")
    
    # Create custom configurations
    transcript_config = TranscriptConfig(
        start_index=2,      # Start from 2nd video
        end_index=5,        # Process only up to 5th video
        use_ai_fallback=True,  # Use AI STT when transcripts unavailable
        cleanup_temp_files=True  # Clean up temporary audio files
    )
    
    processing_config = ProcessingConfig(
        chunk_size=50000,   # Smaller chunks for faster processing
        model_name="gemini-1.5-flash",
        output_language="Spanish",
        styles=["Educational", "Narrative Rewriting"]
    )
    
    # Initialize API with custom config
    api = WatchYTPL4MeAPI(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Process with custom settings
    output_files = api.process_youtube_url(
        url="https://www.youtube.com/playlist?list=PLrAXtmRdnEQy5GKLFVRLt17vTrZNyMLVa",
        output_dir="./output/advanced_example",
        start_index=transcript_config.start_index,
        end_index=transcript_config.end_index,
        chunk_size=processing_config.chunk_size,
        output_language=processing_config.output_language
    )
    
    print(f"Generated {len(output_files)} files (videos 2-5 only):")
    for file_path in output_files:
        print(f"  - {file_path}")


def example_4_two_step_process():
    """
    Example 4: Two-step process - extract transcripts first, then process.
    
    This approach is useful when you want to examine transcripts before processing,
    or when you want to apply different processing styles at different times.
    """
    print("\n=== Example 4: Two-Step Process ===")
    
    # Step 1: Extract transcripts only
    transcripts = extract_transcripts_only(
        url="https://www.youtube.com/watch?v=7gp7GkPE-tI&feature=youtu.be",
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    print(f"Extracted {len(transcripts)} transcripts:")
    
    # Save transcripts to file
    transcript_output_file = "./output/two_step_example/extracted_transcripts.txt"
    os.makedirs(os.path.dirname(transcript_output_file), exist_ok=True)
    
    with open(transcript_output_file, 'w', encoding='utf-8') as f:
        f.write("Extracted Transcripts\n")
        f.write("=" * 50 + "\n\n")
        
        for transcript in transcripts:
            print(f"  - {transcript.title} ({len(transcript.transcript_text)} chars)")
            print(f"    Source: {transcript.source}")
            print(f"    Word count: {transcript.word_count}")
            
            # Write to file
            f.write(f"Title: {transcript.title}\n")
            f.write(f"Source: {transcript.source}\n")
            f.write(f"Word count: {transcript.word_count}\n")
            f.write(f"Character count: {len(transcript.transcript_text)}\n")
            f.write("-" * 50 + "\n")
            f.write(transcript.transcript_text)
            f.write("\n" + "=" * 50 + "\n\n")
    
    print(f"Transcripts saved to: {transcript_output_file}")
    
    # Step 2: Process with AI (could be done later, with different settings)
    api = WatchYTPL4MeAPI(
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    print(f"Using Gemini model: {api.config.processing_config.model_name}")
    
    results = api.process_with_ai(
        transcripts=transcripts,
        output_dir="./output/two_step_example"
    )
    
    print(f"\nGenerated {len(results)} processed files:")
    
    # Calculate total costs
    total_openai_cost = sum(transcript.openai_cost or 0.0 for transcript in transcripts)
    total_gemini_cost = sum(result.gemini_cost or 0.0 for result in results)
    total_cost = total_openai_cost + total_gemini_cost
    
    print(f"\n=== TOKEN COSTS SUMMARY ===")
    print(f"OpenAI (Whisper STT): ${total_openai_cost:.6f}")
    print(f"Gemini Processing: ${total_gemini_cost:.6f}")
    print(f"Total Cost: ${total_cost:.6f}")
    
    print(f"\n=== DETAILED BREAKDOWN ===")
    for transcript in transcripts:
        if transcript.openai_cost and transcript.openai_cost > 0:
            print(f"\nTranscript: {transcript.title[:50]}...")
            print(f"  OpenAI STT Cost: ${transcript.openai_cost:.6f} ({transcript.audio_duration_minutes:.2f} minutes)")
    
    for result in results:
        print(f"\nProcessed File: {result.output_file_path}")
        print(f"  Style: {result.style_name}")
        print(f"  Processing time: {result.processing_time:.2f}s")
        if result.gemini_cost and result.gemini_cost > 0:
            print(f"  Gemini Tokens - Input: {result.gemini_input_tokens}, Output: {result.gemini_output_tokens}")
            print(f"  Gemini Cost: ${result.gemini_cost:.6f}")
        else:
            print(f"  Gemini Cost: $0.000000 (no token data available)")


def example_5_error_handling():
    """
    Example 5: Proper error handling.
    """
    print("\n=== Example 5: Error Handling ===")
    
    try:
        # This will fail due to invalid URL
        output_files = process_youtube_playlist(
            url="https://invalid-url.com",
            output_dir="./output/error_example",
            gemini_api_key=os.getenv("GEMINI_API_KEY")
        )
    except Exception as e:
        print(f"Expected error caught: {type(e).__name__}: {e}")
    
    try:
        # This will fail due to missing API key
        output_files = process_youtube_playlist(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            output_dir="./output/error_example",
            gemini_api_key=""  # Empty API key
        )
    except Exception as e:
        print(f"Expected error caught: {type(e).__name__}: {e}")


def example_6_environment_config():
    """
    Example 6: Loading configuration from environment variables.
    
    This is useful for production deployments where you don't want to
    hardcode API keys in your source code.
    """
    print("\n=== Example 6: Environment Configuration ===")
    
    try:
        # Load API with settings from environment variables
        # Expects GEMINI_API_KEY, OPENAI_API_KEY, and LANGUAGE env vars
        api = load_api_from_env()
        
        print(f"Loaded API with language: {api.config.processing_config.output_language}")
        
        # Use the API normally
        output_files = api.process_youtube_url(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            output_dir="./output/env_example",
            styles=["Summary"]
        )
        
        print(f"Generated {len(output_files)} files using environment config")
        
    except Exception as e:
        print(f"Error loading from environment: {e}")
        print("Make sure GEMINI_API_KEY is set in your .env file")


def example_7_progress_callbacks():
    """
    Example 7: Using progress callbacks for monitoring.
    
    This example shows how to monitor progress during processing,
    which is useful for long-running operations on large playlists.
    """
    print("\n=== Example 7: Progress Monitoring ===")
    
    def progress_callback(percent):
        """Callback function to monitor progress."""
        print(f"Progress: {percent}%")
    
    def status_callback(message):
        """Callback function to monitor status messages."""
        print(f"Status: {message}")
    
    # Note: Progress callbacks are used internally by the extractor and processor
    # This is a conceptual example - the actual implementation may vary
    api = WatchYTPL4MeAPI(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    try:
        # Extract with monitoring
        transcripts = api.extract_transcripts(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        print(f"Extracted {len(transcripts)} transcripts")
        
        # Process with monitoring
        results = api.process_with_ai(
            transcripts, 
            "./output/progress_example"
        )
        print(f"Processing completed: {len(results)} files generated")
        
    except Exception as e:
        print(f"Error during processing: {e}")


def main():
    """
    Run all examples (with proper error handling).
    
    Note: Some examples may fail if you don't have valid API keys
    or if the YouTube URLs become unavailable.
    """
    print("WatchYTPL4Me API Examples")
    print("=" * 50)
    
    # Check if required environment variables are set
    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not set. Some examples may fail.")
        print("Please set your API keys in a .env file:")
        print("  GEMINI_API_KEY=your_gemini_key_here")
        print("  OPENAI_API_KEY=your_openai_key_here")
        print()

    # Run examples with error handling
    examples = [
        # example_1_simple_usage,
        # example_2_single_video,
        # example_3_advanced_configuration,
        example_4_two_step_process,
        # example_5_error_handling,
        # example_6_environment_config,
        # example_7_progress_callbacks
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {e}")
            continue


if __name__ == "__main__":
    main()