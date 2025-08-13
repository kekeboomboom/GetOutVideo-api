#!/usr/bin/env python3
"""
Basic Usage Examples for GetOutVideo API

This module demonstrates simple ways to use the API for extracting and 
processing YouTube video transcripts.
"""

import os
from getoutvideo import GetOutVideoAPI, process_youtube_playlist

def basic_single_video_example():
    """
    Example 1: Process a single YouTube video with default settings.
    """
    print("=== Example 1: Basic Single Video Processing ===")
    
    # Initialize the API with your OpenAI API key
    api = GetOutVideoAPI(openai_api_key="your-openai-api-key-here")
    
    # Process a single video with default settings (all styles)
    output_files = api.process_youtube_url(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_dir="./output"
    )
    
    print(f"Generated {len(output_files)} files:")
    for file_path in output_files:
        print(f"  - {file_path}")


def convenience_function_example():
    """
    Example 2: Using the convenience function for quick processing.
    """
    print("=== Example 2: Using Convenience Function ===")
    
    # One-line processing with convenience function
    output_files = process_youtube_playlist(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_dir="./output",
        openai_api_key="your-openai-api-key-here",
        styles=["Summary", "Educational"],  # Only specific styles
        output_language="English"
    )
    
    print(f"Generated {len(output_files)} files:")
    for file_path in output_files:
        print(f"  - {file_path}")


def playlist_example():
    """
    Example 3: Process a YouTube playlist with specific video range.
    """
    print("=== Example 3: Playlist Processing with Range ===")
    
    api = GetOutVideoAPI(openai_api_key="your-openai-api-key-here")
    
    # Process videos 2-5 from a playlist
    output_files = api.process_youtube_url(
        url="https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMw6luKi_8LlH4b1vD",
        output_dir="./output/playlist",
        start_index=2,
        end_index=5,
        styles=["Summary"],
        chunk_size=50000,  # Smaller chunks for faster processing
        output_language="Spanish"
    )
    
    print(f"Generated {len(output_files)} files from playlist videos 2-5")


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
    1. Replace 'your-openai-api-key-here' with your actual API key
    2. Set up proper output directories
    3. Use valid YouTube URLs
    """
    
    print("GetOutVideo API Examples")
    print("=" * 50)
    print("NOTE: Examples are commented out to prevent accidental API usage.")
    print("Uncomment and modify the examples below with your API key and URLs.")
    print()
    
    # Uncomment to run examples:
    # basic_single_video_example()
    # print()
    # convenience_function_example()
    # print()
    # playlist_example()
    # print()
    # environment_config_example()