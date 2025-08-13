"""
Usage examples for the WatchYTPL4Me API - Single Video Processing.

This module demonstrates various ways to use the API for single video processing,
from simple one-line processing to advanced configuration scenarios.
"""

import os
from dotenv import load_dotenv

# Import the main API components
from api import (
    WatchYTPL4MeAPI, 
    extract_transcripts_only,
    ProcessingConfig,
    load_api_from_env
)
from api.config_urls import DEFAULT_EXAMPLE_URL, FALLBACK_TEST_URL

# Load environment variables from .env file
load_dotenv()



def example_1_single_video():
    """
    Example 1: Processing a single YouTube video with specific styles.
    """
    print("=== Example 1: Single Video with Specific Styles ===")
    
    # Process just one video with only summary and Q&A styles
    api = WatchYTPL4MeAPI(
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    output_files = api.process_youtube_url(
        url=DEFAULT_EXAMPLE_URL,
        output_dir="./output/single_video",
        styles=["Summary"],
        output_language="Chinese"
    )
    
    print(f"Generated {len(output_files)} files:")
    for file_path in output_files:
        print(f"  - {file_path}")



def example_2_two_step_process():
    """
    Example 2: Two-step process - extract transcripts first, then process.
    
    This approach is useful when you want to examine transcripts before processing,
    or when you want to apply different processing styles at different times.
    """
    print("\n=== Example 2: Two-Step Process ===")
    
    # Step 1: Extract transcripts only
    transcripts = extract_transcripts_only(
        url=DEFAULT_EXAMPLE_URL,
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
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    print(f"Using OpenAI model: {api.config.processing_config.model_name}")
    
    results = api.process_with_ai(
        transcripts=transcripts,
        output_dir="./output/two_step_example"
    )
    
    print(f"\nGenerated {len(results)} processed files:")
    
    # Calculate total costs
    total_openai_cost = sum(transcript.openai_cost or 0.0 for transcript in transcripts)
    total_openai_processing_cost = sum(result.openai_cost or 0.0 for result in results)
    total_cost = total_openai_cost + total_openai_processing_cost
    
    print(f"\n=== TOKEN COSTS SUMMARY ===")
    print(f"OpenAI (Whisper STT): ${total_openai_cost:.6f}")
    print(f"OpenAI Processing: ${total_openai_processing_cost:.6f}")
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
        if result.openai_cost and result.openai_cost > 0:
            print(f"  OpenAI Tokens - Input: {result.openai_input_tokens}, Output: {result.openai_output_tokens}")
            print(f"  OpenAI Cost: ${result.openai_cost:.6f}")
        else:
            print(f"  OpenAI Cost: $0.000000 (no token data available)")


def example_3_error_handling():
    """
    Example 3: Proper error handling.
    """
    print("\n=== Example 3: Error Handling ===")
    
    try:
        # This will fail due to invalid URL
        api = WatchYTPL4MeAPI(openai_api_key=os.getenv("OPENAI_API_KEY"))
        output_files = api.process_youtube_url(
            url="https://invalid-url.com",
            output_dir="./output/error_example"
        )
    except Exception as e:
        print(f"Expected error caught: {type(e).__name__}: {e}")
    
    try:
        # This will fail due to missing API key
        api = WatchYTPL4MeAPI(openai_api_key="")  # Empty API key
        output_files = api.process_youtube_url(
            url=FALLBACK_TEST_URL,
            output_dir="./output/error_example"
        )
    except Exception as e:
        print(f"Expected error caught: {type(e).__name__}: {e}")


def example_4_environment_config():
    """
    Example 4: Loading configuration from environment variables.

    This is useful for production deployments where you don't want to
    hardcode API keys in your source code.
    """
    print("\n=== Example 4: Environment Configuration ===")

    try:
        # Load API with settings from environment variables
        # Expects OPENAI_API_KEY and LANGUAGE env vars
        api = load_api_from_env()

        print(f"Loaded API with language: {api.config.processing_config.output_language}")

        # Use the API normally
        output_files = api.process_youtube_url(
            url=FALLBACK_TEST_URL,
            output_dir="./output/env_example",
            styles=["Summary"]
        )

        print(f"Generated {len(output_files)} files using environment config")

    except Exception as e:
        print(f"Error loading from environment: {e}")
        print("Make sure OPENAI_API_KEY is set in your .env file")


def example_5_progress_callbacks():
    """
    Example 5: Using progress callbacks for monitoring.

    This example shows how to monitor progress during processing,
    which is useful for monitoring single video processing.
    """
    print("\n=== Example 5: Progress Monitoring ===")

    def progress_callback(percent):
        """Callback function to monitor progress."""
        print(f"Progress: {percent}%")

    def status_callback(message):
        """Callback function to monitor status messages."""
        print(f"Status: {message}")

    # Note: Progress callbacks are used internally by the extractor and processor
    # This is a conceptual example - the actual implementation may vary
    api = WatchYTPL4MeAPI(
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    try:
        # Extract with monitoring
        transcripts = api.extract_transcripts(
            FALLBACK_TEST_URL
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


def example_6_transcripts_only():
    """
    Example 6: Extract transcripts only and save to file.

    This example shows how to simply extract transcripts from a YouTube video
    and save them to a file without any AI processing.
    """
    print("\n=== Example 6: Transcripts Only ===")

    # Extract transcripts only
    transcripts = extract_transcripts_only(
        url=DEFAULT_EXAMPLE_URL,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    print(f"Extracted {len(transcripts)} transcripts")

    # Save to file
    output_file = "./output/transcripts_only/transcripts.txt"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for transcript in transcripts:
            f.write(f"Title: {transcript.title}\n")
            f.write(f"Word count: {transcript.word_count}\n")
            f.write("-" * 50 + "\n")
            f.write(transcript.transcript_text)
            f.write("\n" + "=" * 80 + "\n\n")

    print(f"Transcripts saved to: {output_file}")


def example_7_direct_chinese_translation():
    """
    Example 7: Extract transcripts and directly translate to Chinese using AI.

    This example shows how to extract transcripts and use AI to translate
    them directly to Chinese without using the standard processing styles.
    """
    print("\n=== Example 7: Direct Chinese Translation ===")

    # Extract transcripts first
    transcripts = extract_transcripts_only(
        url=DEFAULT_EXAMPLE_URL,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    print(f"Extracted {len(transcripts)} transcripts")

    # Set up OpenAI client for direct translation
    import openai
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create output directory
    output_dir = "./output/chinese_translation"
    os.makedirs(output_dir, exist_ok=True)

    # Process each transcript for translation
    for i, transcript in enumerate(transcripts):
        print(f"Translating video {i+1}/{len(transcripts)}: {transcript.title}")
        
        # Create optimized translation prompt
        translation_prompt = f"""You are a professional translator specializing in YouTube content translation. 

**Task**: Translate the following English video transcript to Chinese.

**Requirements**:
1. **Accuracy**: Preserve exact meaning, context, and nuance
2. **Fluency**: Produce natural, idiomatic Chinese that flows well
3. **Cultural Adaptation**: Adapt cultural references appropriately for Chinese audience
4. **Technical Terms**: Maintain consistency for technical terms throughout
5. **Tone**: Preserve the original speaker's tone, formality level, and personality
6. **Format**: Maintain any existing structure, bullet points, or formatting

**Special Instructions**:
- For proper nouns (names, places, brands): Keep original + add Chinese equivalent in parentheses if helpful
- For technical jargon: Use standard Chinese equivalents or explain briefly
- For cultural references: Adapt or explain as needed for Chinese audience
- For ambiguous text: Choose the most contextually appropriate translation

**Quality Check**: After translation, review for:
- Natural flow and readability
- Consistency of terminology
- Cultural appropriateness
- Completeness (no omissions)

**Source Content**:
{transcript.transcript_text}

**Translation**:"""

        try:
            # Use OpenAI API for translation
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": translation_prompt}],
                temperature=0.3
            )
            
            chinese_text = response.choices[0].message.content
            
            # Calculate and print cost
            usage = response.usage
            input_cost = usage.prompt_tokens * 0.00015 / 1000  # $0.15 per 1M input tokens for gpt-4o-mini
            output_cost = usage.completion_tokens * 0.0006 / 1000  # $0.60 per 1M output tokens for gpt-4o-mini
            total_cost = input_cost + output_cost
            print(f"Translation cost: ${total_cost:.4f} (Input: {usage.prompt_tokens} tokens, Output: {usage.completion_tokens} tokens)")
            
            # Save to file with Chinese-friendly filename
            safe_title = transcript.title.replace('/', '_').replace('\\', '_')[:50]  # Truncate for filename
            output_file = os.path.join(output_dir, f"{safe_title}_chinese.md")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# {transcript.title} (中文翻译)\n\n")
                f.write(f"**原视频标题**: {transcript.title}\n")
                f.write(f"**字数统计**: {transcript.word_count}\n")
                f.write(f"**翻译时间**: {transcript.duration if hasattr(transcript, 'duration') else 'N/A'}\n\n")
                f.write("---\n\n")
                f.write(chinese_text)
            
            print(f"✓ Saved Chinese translation to: {output_file}")
            
        except Exception as e:
            print(f"✗ Error translating {transcript.title}: {e}")
            continue

    print(f"\nChinese translations completed and saved to: {output_dir}")


def main():
    """
    Run all examples (with proper error handling).

    Note: Some examples may fail if you don't have valid API keys
    or if the YouTube URLs become unavailable.
    """
    print("WatchYTPL4Me API Examples")
    print("=" * 50)

    # Check if required environment variables are set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Some examples may fail.")
        print("Please set your API key in a .env file:")
        print("  OPENAI_API_KEY=your_openai_key_here")
        print()

    # Run examples with error handling
    examples = [
        # example_1_single_video,
        # example_2_two_step_process,
        # example_3_error_handling,
        # example_4_environment_config,
        # example_5_progress_callbacks,
        # example_6_transcripts_only,
        example_7_direct_chinese_translation
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {e}")
            continue




if __name__ == "__main__":
    main()