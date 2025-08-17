"""
AI processing functionality for the WatchYTPL4Me API.

This module provides the AI processing logic adapted from the original
GUI application's GPT5ProcessingThread class.
"""

import os
import time
from typing import List, Optional, Callable
import openai

from .config import APIConfig
from .models import VideoTranscript, ProcessingResult
from .exceptions import AIProcessingError, OpenAIAPIError, FileOperationError
from .prompts import text_refinement_prompts, get_available_styles, get_prompt_for_style
from .utils import sanitize_filename, split_text_into_chunks, safe_progress_callback, safe_status_callback, ensure_directory_exists


class AIProcessor:
    """
    Processes video transcripts using OpenAI's GPT-5 API.
    
    This class provides AI processing functionality for refining transcripts
    using various processing styles and handling large transcripts through chunking.
    """
    
    # OpenAI API pricing per 1M tokens (as of 2025 rates)
    # These rates should be updated regularly as OpenAI pricing changes frequently
    OPENAI_PRICING = {
        "gpt-4.1": {"input": 2.00, "output": 8.00},         # per 1M tokens
        "gpt-5": {"input": 1.25, "output": 10.00},           # per 1M tokens (placeholder)
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},   # per 1M tokens
        "gpt-4o": {"input": 3.00, "output": 10.00},         # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},     # per 1M tokens
    }
    
    def __init__(self, config: APIConfig):
        """
        Initialize the AI processor.
        
        Args:
            config: API configuration containing OpenAI settings
        """
        self.config = config
        self._cancelled = False
        
        # Configure OpenAI API
        self.client = openai.OpenAI(api_key=config.openai_api_key)
    
    def cancel(self) -> None:
        """Cancel the current processing operation."""
        self._cancelled = True
    
    def _calculate_openai_cost(self, input_tokens: int, output_tokens: int, model_name: str) -> float:
        """
        Calculate the cost of OpenAI API usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            model_name: Name of the OpenAI model used
            
        Returns:
            float: Cost in USD
        """
        pricing = self.OPENAI_PRICING.get(model_name, self.OPENAI_PRICING.get("gpt-5"))
        input_cost = (input_tokens / 1000000) * pricing["input"]  # OpenAI pricing is per 1M tokens
        output_cost = (output_tokens / 1000000) * pricing["output"]  # OpenAI pricing is per 1M tokens
        return input_cost + output_cost
    
    def process_transcripts(self,
                          transcripts: List[VideoTranscript],
                          output_dir: str,
                          progress_callback: Optional[Callable[[int], None]] = None,
                          status_callback: Optional[Callable[[str], None]] = None) -> List[ProcessingResult]:
        """
        Process multiple transcripts with AI refinement.
        
        Args:
            transcripts: List of video transcripts to process
            output_dir: Directory where processed files will be saved
            progress_callback: Optional callback for progress updates (0-100)
            status_callback: Optional callback for status messages
            
        Returns:
            List[ProcessingResult]: List of processing results
            
        Raises:
            AIProcessingError: If processing fails
        """
        self._cancelled = False
        
        try:
            ensure_directory_exists(output_dir)
            
            # Get styles to process
            styles_to_process = self._get_styles_to_process()
            if not styles_to_process:
                raise AIProcessingError("No processing styles specified")
            
            total_videos = len(transcripts)
            if total_videos == 0:
                safe_status_callback(status_callback, "No video transcripts to process.")
                return []
            
            safe_status_callback(status_callback, 
                               f"Starting AI processing for {total_videos} transcripts with {len(styles_to_process)} styles.")
            
            results = []
            
            for video_index, transcript in enumerate(transcripts):
                if self._cancelled:
                    safe_status_callback(status_callback, "Processing cancelled by user.")
                    break
                
                if not transcript.transcript_text:
                    safe_status_callback(status_callback,
                                       f"Skipping Video {video_index + 1}/{total_videos} "
                                       f"(Title: {transcript.title[:30]}...) - No transcript text found.")
                    continue
                
                sanitized_title = sanitize_filename(transcript.title)
                safe_status_callback(status_callback,
                                   f"\\nProcessing Video {video_index + 1}/{total_videos}: {transcript.title[:50]}...")
                
                word_count = len(transcript.transcript_text.split())
                safe_status_callback(status_callback, f"Word Count: {word_count} words")
                safe_status_callback(status_callback, f"Chunk Size: {self.config.processing_config.chunk_size} words")
                
                # Split transcript into chunks
                chunks = split_text_into_chunks(transcript.transcript_text, 
                                              self.config.processing_config.chunk_size)
                
                # Process each style for this transcript
                for style_name in styles_to_process:
                    if self._cancelled:
                        break
                    
                    try:
                        start_time = time.time()
                        result = self._process_single_transcript(transcript, style_name, chunks,
                                                               sanitized_title, output_dir,
                                                               video_index + 1, total_videos,
                                                               status_callback)
                        processing_time = time.time() - start_time
                        
                        if result:
                            result.processing_time = processing_time
                            result.chunk_count = len(chunks)
                            results.append(result)
                            
                    except Exception as e:
                        safe_status_callback(status_callback,
                                           f"Error processing style '{style_name}' for video {video_index + 1}: {str(e)}")
                        continue
                
                # Update progress
                progress_percent = int(((video_index + 1) / total_videos) * 100)
                safe_progress_callback(progress_callback, progress_percent)
            
            safe_status_callback(status_callback, f"AI processing completed. {len(results)} files generated.")
            return results
            
        except Exception as e:
            error_msg = f"Failed to process transcripts: {str(e)}"
            safe_status_callback(status_callback, error_msg)
            raise AIProcessingError(error_msg) from e
    
    def _get_styles_to_process(self) -> List[str]:
        """Get the list of styles to process based on configuration."""
        config_styles = self.config.processing_config.styles
        
        if config_styles is None:
            # Use all available styles
            return get_available_styles()
        elif isinstance(config_styles, list):
            # Validate specified styles
            available_styles = get_available_styles()
            invalid_styles = [style for style in config_styles if style not in available_styles]
            if invalid_styles:
                raise AIProcessingError(f"Invalid styles specified: {invalid_styles}. "
                                       f"Available styles: {available_styles}")
            return config_styles
        else:
            raise AIProcessingError("styles configuration must be None or a list of style names")
    
    def _process_single_transcript(self,
                                 transcript: VideoTranscript,
                                 style_name: str,
                                 chunks: List[str],
                                 sanitized_title: str,
                                 output_dir: str,
                                 video_index: int,
                                 total_videos: int,
                                 status_callback: Optional[Callable[[str], None]] = None) -> Optional[ProcessingResult]:
        """
        Process a single transcript with one style.
        
        Args:
            transcript: The video transcript to process
            style_name: Name of the processing style
            chunks: List of text chunks to process
            sanitized_title: Sanitized version of the video title for filename
            output_dir: Output directory for the processed file
            video_index: Current video index (1-based)
            total_videos: Total number of videos being processed
            status_callback: Optional callback for status messages
            
        Returns:
            ProcessingResult: Result of the processing operation
        """
        try:
            style_prompt = get_prompt_for_style(style_name)
            full_response = ""
            total_input_tokens = 0
            total_output_tokens = 0
            
            # Process each chunk
            for chunk_index, chunk in enumerate(chunks):
                if self._cancelled:
                    return None
                
                # Format prompt with language
                formatted_prompt = style_prompt.replace("[Language]", self.config.processing_config.output_language)
                full_prompt = f"{formatted_prompt}\n\n{chunk}"
                
                # Generate content with OpenAI GPT-5
                try:
                    safe_status_callback(status_callback,
                                       f"Generating style '{style_name}' for Video {video_index}, "
                                       f"Chunk {chunk_index + 1}/{len(chunks)}...")
                    
                    # Use appropriate parameters based on model
                    if 'gpt-5' in self.config.processing_config.model_name.lower():
                        response = self.client.chat.completions.create(
                            model=self.config.processing_config.model_name,
                            messages=[{"role": "user", "content": full_prompt}]
                        )
                    else:
                        response = self.client.chat.completions.create(
                            model=self.config.processing_config.model_name,
                            messages=[{"role": "user", "content": full_prompt}],
                            temperature=0.7
                        )
                    
                    response_text = response.choices[0].message.content
                    full_response += response_text + "\n\n"
                    
                    # Track token usage if available
                    if hasattr(response, 'usage') and response.usage:
                        total_input_tokens += response.usage.prompt_tokens or 0
                        total_output_tokens += response.usage.completion_tokens or 0
                        safe_status_callback(status_callback,
                                           f"Chunk {chunk_index + 1}/{len(chunks)} tokens: "
                                           f"input={response.usage.prompt_tokens}, "
                                           f"output={response.usage.completion_tokens}")
                    
                    safe_status_callback(status_callback,
                                       f"Chunk {chunk_index + 1}/{len(chunks)} processed for style '{style_name}'.")
                    
                except Exception as e:
                    error_msg = f"OpenAI API error for chunk {chunk_index + 1}: {str(e)}"
                    safe_status_callback(status_callback, error_msg)
                    raise OpenAIAPIError(error_msg) from e
            
            # Save the processed content to file
            output_filename = f"{sanitized_title} [{style_name}].md"
            output_path = os.path.join(output_dir, output_filename)
            
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    # Add title and URL header
                    f.write(f"# {transcript.title}\n\n")
                    f.write(f"**Original Video URL:** {transcript.url}\n\n")
                    f.write(full_response.strip())
                
                # Calculate cost
                openai_cost = self._calculate_openai_cost(total_input_tokens, total_output_tokens, 
                                                        self.config.processing_config.model_name)
                
                safe_status_callback(status_callback,
                                   f"Saved '{style_name}' output for video {video_index} to {output_path}")
                safe_status_callback(status_callback,
                                   f"OpenAI usage - Input tokens: {total_input_tokens}, "
                                   f"Output tokens: {total_output_tokens}, Cost: ${openai_cost:.6f}")
                
                return ProcessingResult(
                    video_transcript=transcript,
                    style_name=style_name,
                    output_file_path=output_path,
                    processing_time=0.0,  # Will be set by caller
                    chunk_count=len(chunks),
                    openai_input_tokens=total_input_tokens,
                    openai_output_tokens=total_output_tokens,
                    openai_cost=openai_cost
                )
                
            except IOError as e:
                error_msg = f"Error writing file {output_path}: {str(e)}"
                safe_status_callback(status_callback, error_msg)
                raise FileOperationError(error_msg) from e
            
        except (GeminiAPIError, FileOperationError):
            raise
        except Exception as e:
            error_msg = f"Error processing transcript with style '{style_name}': {str(e)}"
            raise AIProcessingError(error_msg) from e