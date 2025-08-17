#!/usr/bin/env python3
"""
Basic Usage Examples for GetOutVideo API

This module demonstrates simple ways to use the API for extracting and 
processing YouTube video transcripts.
"""

import os
from dotenv import load_dotenv
from getoutvideo import GetOutVideoAPI, process_youtube_video

# Load environment variables from .env file
load_dotenv()

def basic_single_video_example():
    """
    Example 1: Process a single YouTube video with default settings.
    """
    print("=== Example 1: Basic Single Video Processing ===")
    
    # Initialize the API with OpenAI API key from environment
    api = GetOutVideoAPI(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    # Configure transcript extraction for Chinese language
    # This video is in Chinese, so we need to specify language preferences
    from getoutvideo import TranscriptConfig
    api.config.transcript_config = TranscriptConfig(
        transcript_languages=['zh', 'zh-CN', 'zh-TW', 'en'],  # Try Chinese variants first, then English
        use_ai_fallback=True  # Use AI transcription if no transcript available
    )
    
    # Use two-step processing to get detailed results including cost information
    print("Extracting transcripts...")
    transcripts = api.extract_transcripts("https://www.youtube.com/watch?v=ugqVaSOfR5g&ab_channel=ChrisWilliamson")
    
    if not transcripts:
        print("No transcripts extracted.")
        return
    
    print(f"Processing {len(transcripts)} transcripts with AI...")
    # Configure processing settings
    from getoutvideo import ProcessingConfig
    processing_config = ProcessingConfig(
        styles=["Summary"],
        output_language="Chinese"
    )
    
    # Process with AI and get detailed results
    results = api.process_with_ai(transcripts, "./output", processing_config)
    
    print(f"Generated {len(results)} files:")
    for result in results:
        print(f"  - {result.output_file_path}")
    
    # Display cost information
    print("\n=== AI API Usage Cost Information ===")
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0
    
    for result in results:
        print(f"\nStyle: {result.style_name}")
        print(f"  Input tokens: {result.openai_input_tokens:,}")
        print(f"  Output tokens: {result.openai_output_tokens:,}")
        print(f"  Processing cost: ${result.openai_cost:.6f}")
        
        total_input_tokens += result.openai_input_tokens or 0
        total_output_tokens += result.openai_output_tokens or 0
        total_cost += result.openai_cost or 0.0
    
    # Include transcript extraction cost if available
    transcript_cost = 0.0
    for transcript in transcripts:
        if transcript.openai_cost:
            transcript_cost += transcript.openai_cost
    
    if transcript_cost > 0:
        print(f"\nTranscript extraction cost: ${transcript_cost:.6f}")
        total_cost += transcript_cost
    
    print(f"\nTotal tokens used: {total_input_tokens + total_output_tokens:,}")
    print(f"Total cost: ${total_cost:.6f}")


def convenience_function_example():
    """
    Example 2: Using the convenience function for quick processing.
    """
    print("=== Example 2: Using Convenience Function ===")
    
    # One-line processing with convenience function
    output_files = process_youtube_video(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_dir="./output",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        styles=["Summary", "Educational"],  # Only specific styles
        output_language="English"
    )
    
    print(f"Generated {len(output_files)} files:")
    for file_path in output_files:
        print(f"  - {file_path}")


def custom_processing_example():
    """
    Example 3: Process a YouTube video with custom settings.
    """
    print("=== Example 3: Custom Processing Settings ===")
    
    api = GetOutVideoAPI(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    # Process video with custom settings
    output_files = api.process_youtube_url(
        url="https://www.youtube.com/watch?v=VIDEO_ID",
        output_dir="./output/custom",
        styles=["Summary"],
        chunk_size=50000,  # Smaller chunks for faster processing
        output_language="Spanish"
    )
    
    print(f"Generated {len(output_files)} files with custom settings")


def environment_config_example():
    """
    Example 4: Load configuration from environment variables.
    """
    print("=== Example 4: Environment Configuration ===")
    
    # Set environment variables first:
    # export OPENAI_API_KEY="your-key-here"
    # export LANGUAGE="French"
    
    from getoutvideo import load_api_from_env
    
    try:
        api = load_api_from_env()
        
        output_files = api.process_youtube_url(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            output_dir="./output"
        )
        
        print(f"Generated {len(output_files)} files using environment config")
        
    except Exception as e:
        print(f"Error loading from environment: {e}")
        print("Make sure OPENAI_API_KEY is set in your environment")


if __name__ == "__main__":
    """
    Run examples (commented out to prevent accidental API usage).
    
    Uncomment the examples you want to run and make sure to:
    1. Create a .env file with OPENAI_API_KEY=your-actual-api-key
    2. Set up proper output directories
    3. Use valid YouTube URLs
    """
    
    print("GetOutVideo API Examples")
    print("=" * 50)
    print("NOTE: Examples are commented out to prevent accidental API usage.")
    print("Uncomment the examples below and create a .env file with your API key.")
    print()
    
    # Uncomment to run examples:
    basic_single_video_example()
    # print()
    # convenience_function_example()
    # print()
    # custom_processing_example()
    # print()
    # environment_config_example()