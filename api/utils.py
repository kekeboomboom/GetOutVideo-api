"""
Utility functions for the WatchYTPL4Me API.

This module provides helper functions used across the API components,
including filename sanitization and text chunking functionality.
"""

import re
import os
from typing import List, Optional, Callable


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize a filename by removing invalid characters and limiting length.
    
    This function replicates the _sanitize_filename method from the original
    GUI application to ensure consistent file naming.
    
    Args:
        filename: The original filename to sanitize
        max_length: Maximum length for the sanitized filename
        
    Returns:
        str: Sanitized filename safe for filesystem use
    """
    if not filename:
        return "untitled"
    
    # Remove invalid characters for Windows/Unix filesystems
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[_\s]+', '_', sanitized)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' ._')
    
    # Ensure we don't create reserved Windows names
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                      'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                      'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    
    if sanitized.upper() in reserved_names:
        sanitized = f"_{sanitized}"
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_. ')
    
    # Ensure we have something
    if not sanitized:
        sanitized = "untitled"
    
    return sanitized


def split_text_into_chunks(text: str, chunk_size: int, min_chunk_size: int = 0) -> List[str]:
    """
    Split text into chunks based on word count.
    
    This function replicates the chunking logic from the original
    GeminiProcessingThread to ensure consistent text processing.
    
    Args:
        text: The text to split into chunks
        chunk_size: Maximum number of words per chunk
        min_chunk_size: Minimum number of words for a chunk (smaller chunks get merged)
        
    Returns:
        List[str]: List of text chunks
    """
    if not text:
        return [""]
        
    if chunk_size <= 0:
        return [text]
    
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    current_chunk = []
    
    for word in words:
        current_chunk.append(word)
        
        if len(current_chunk) >= chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
    
    # Handle remaining words
    if current_chunk:
        remaining_chunk = ' '.join(current_chunk)
        
        # If final chunk is too small and we have previous chunks, merge with last chunk
        if (min_chunk_size > 0 and len(current_chunk) < min_chunk_size and 
            chunks and len(chunks) > 0):
            # Merge with previous chunk
            last_chunk = chunks.pop()
            chunks.append(last_chunk + ' ' + remaining_chunk)
        else:
            chunks.append(remaining_chunk)
    
    return chunks


def safe_progress_callback(callback: Optional[Callable[[int], None]], 
                          progress: int) -> None:
    """
    Safely call a progress callback function.
    
    Args:
        callback: Optional progress callback function that accepts progress percentage
        progress: Progress percentage (0-100)
    """
    if callback is not None:
        try:
            callback(progress)
        except Exception:
            # Silently ignore callback errors to prevent them from breaking processing
            pass


def safe_status_callback(callback: Optional[Callable[[str], None]], 
                        message: str) -> None:
    """
    Safely call a status callback function.
    
    Args:
        callback: Optional status callback function that accepts status messages
        message: Status message string
    """
    if callback is not None:
        try:
            callback(message)
        except Exception:
            # Silently ignore callback errors to prevent them from breaking processing
            pass


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Raises:
        OSError: If directory cannot be created
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)