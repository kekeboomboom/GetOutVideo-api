#!/usr/bin/env python3
"""
Advanced Usage Examples for GetOutVideo API

This module demonstrates advanced features like two-step processing,
custom configurations, error handling, and transcript-only extraction.
"""

import os
from getoutvideo import (
    GetOutVideoAPI, 
    extract_transcripts_only,
    TranscriptConfig,
    ProcessingConfig,
    GetOutVideoError
)


def two_step_processing_example():
    """
    Example 1: Extract transcripts first, then process separately.
    
    This is useful when you want to:
    - Extract transcripts once and apply different processing styles
    - Analyze transcripts before processing
    - Handle large playlists efficiently
    """
    print("=== Example 1: Two-Step Processing ===")
    
    api = GetOutVideoAPI(openai_api_key="your-openai-api-key-here")
    
    # Step 1: Extract transcripts only
    print("Step 1: Extracting transcripts...")
    transcripts = api.extract_transcripts(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    print(f"Extracted {len(transcripts)} transcripts:")
    for i, transcript in enumerate(transcripts, 1):
        print(f"  {i}. {transcript.title[:50]}... ({len(transcript.transcript_text)} chars)")
    
    # Step 2: Process with AI using different styles
    print("\nStep 2: Processing with AI...")
    
    # Process with educational style
    api.config.processing_config.styles = ["Educational"]
    results_edu = api.process_with_ai(transcripts, "./output/educational")
    
    # Process same transcripts with summary style
    api.config.processing_config.styles = ["Summary"]
    results_sum = api.process_with_ai(transcripts, "./output/summary")
    
    print(f"Generated {len(results_edu)} educational files and {len(results_sum)} summary files")


def custom_configuration_example():
    """
    Example 2: Using custom configurations for fine-grained control.
    """
    print("=== Example 2: Custom Configurations ===")
    
    # Create custom transcript configuration
    transcript_config = TranscriptConfig(
        use_ai_fallback=True,
        cookie_path="./cookies.txt",  # For restricted videos
        cleanup_temp_files=True
    )
    
    # Create custom processing configuration
    processing_config = ProcessingConfig(
        styles=["Summary", "Q&A"],
        chunk_size=30000,  # Smaller chunks for faster processing
        output_language="German",
        max_concurrent_requests=2  # Limit concurrent API calls
    )
    
    api = GetOutVideoAPI(openai_api_key="your-openai-api-key-here")
    
    # Apply custom configurations
    api.config.transcript_config = transcript_config
    api.config.processing_config = processing_config
    
    output_files = api.process_youtube_url(
        url="https://www.youtube.com/watch?v=VIDEO_ID",
        output_dir="./output/custom_config"
    )
    
    print(f"Processed with custom config: {len(output_files)} files")


def error_handling_example():
    """
    Example 3: Proper error handling and recovery.
    """
    print("=== Example 3: Error Handling ===")
    
    api = GetOutVideoAPI(openai_api_key="your-openai-api-key-here")
    
    test_urls = [
        "https://www.youtube.com/watch?v=valid_video_id",
        "https://www.youtube.com/watch?v=invalid_video_id"
    ]
    
    for url in test_urls:
        try:
            print(f"\nTrying to process: {url}")
            output_files = api.process_youtube_url(
                url=url,
                output_dir="./output/error_test"
            )
            print(f"Success: Generated {len(output_files)} files")
            
        except GetOutVideoError as e:
            print(f"GetOutVideo Error: {e}")
            # Handle API-specific errors
            
        except Exception as e:
            print(f"Unexpected Error: {e}")
            # Handle other errors


def transcript_only_extraction():
    """
    Example 4: Extract transcripts without AI processing.
    """
    print("=== Example 4: Transcript-Only Extraction ===")
    
    # Using convenience function for transcript-only extraction
    transcripts = extract_transcripts_only(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        openai_api_key="your-openai-api-key-here",
        use_ai_fallback=True  # Use AI STT if YouTube transcript unavailable
    )
    
    print(f"Extracted {len(transcripts)} transcripts:")
    for transcript in transcripts:
        print(f"\nTitle: {transcript.title}")
        print(f"URL: {transcript.url}")
        print(f"Source: {transcript.source}")
        print(f"Length: {len(transcript.transcript_text)} characters")
        print(f"Preview: {transcript.transcript_text[:200]}...")
        
        # Save transcript to file
        filename = f"transcript_{transcript.title[:30]}.txt"
        filename = filename.replace("/", "_").replace("\\", "_")
        
        with open(f"./output/{filename}", "w", encoding="utf-8") as f:
            f.write(f"Title: {transcript.title}\n")
            f.write(f"URL: {transcript.url}\n")
            f.write(f"Source: {transcript.source}\n\n")
            f.write(transcript.transcript_text)
        
        print(f"Saved to: ./output/{filename}")


def batch_processing_example():
    """
    Example 5: Batch process multiple videos with different configurations.
    """
    print("=== Example 5: Batch Processing ===")
    
    api = GetOutVideoAPI(openai_api_key="your-openai-api-key-here")
    
    # Define different processing jobs
    jobs = [
        {
            "url": "https://www.youtube.com/watch?v=video1",
            "output_dir": "./output/batch/educational",
            "styles": ["Educational", "Technical"],
            "language": "English"
        },
        {
            "url": "https://www.youtube.com/watch?v=video2",
            "output_dir": "./output/batch/summaries",
            "styles": ["Summary"],
            "language": "Spanish"
        },
        {
            "url": "https://www.youtube.com/watch?v=video3",
            "output_dir": "./output/batch/detailed",
            "styles": ["Q&A", "Balanced and Detailed"],
            "language": "French"
        }
    ]
    
    successful_jobs = 0
    total_files = 0
    
    for i, job in enumerate(jobs, 1):
        try:
            print(f"\nProcessing job {i}/{len(jobs)}: {job['url']}")
            
            output_files = api.process_youtube_url(
                url=job["url"],
                output_dir=job["output_dir"],
                styles=job["styles"],
                output_language=job["language"]
            )
            
            successful_jobs += 1
            total_files += len(output_files)
            print(f"Job {i} completed: {len(output_files)} files generated")
            
        except Exception as e:
            print(f"Job {i} failed: {e}")
    
    print(f"\nBatch processing completed:")
    print(f"  Successful jobs: {successful_jobs}/{len(jobs)}")
    print(f"  Total files generated: {total_files}")


if __name__ == "__main__":
    """
    Run advanced examples (commented out to prevent accidental API usage).
    """
    
    print("GetOutVideo API Advanced Examples")
    print("=" * 50)
    print("NOTE: Examples are commented out to prevent accidental API usage.")
    print("Uncomment and modify the examples below with your API key and URLs.")
    print()
    
    # Uncomment to run examples:
    # two_step_processing_example()
    # print()
    # custom_configuration_example()
    # print()
    # error_handling_example()
    # print()
    # transcript_only_extraction()
    # print()
    # batch_processing_example()