"""
Tests for utility functions.
"""

import pytest
from getoutvideo.utils import sanitize_filename, split_text_into_chunks


class TestSanitizeFilename:
    """Test filename sanitization function."""
    
    def test_basic_sanitization(self):
        """Test basic character removal."""
        assert sanitize_filename("hello<world>") == "hello_world"
        assert sanitize_filename('file:name*test') == "file_name_test"
        assert sanitize_filename('path/to\\file') == "path_to_file"
    
    def test_empty_filename(self):
        """Test empty filename handling."""
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"
    
    def test_reserved_names(self):
        """Test Windows reserved names."""
        assert sanitize_filename("CON") == "_CON"
        assert sanitize_filename("PRN") == "_PRN"
        assert sanitize_filename("con") == "_con"  # Case insensitive
    
    def test_length_limiting(self):
        """Test filename length limiting."""
        long_name = "a" * 150
        result = sanitize_filename(long_name, max_length=100)
        assert len(result) == 100
    
    def test_multiple_spaces(self):
        """Test multiple space/underscore handling."""
        assert sanitize_filename("hello   world") == "hello_world"
        assert sanitize_filename("hello___world") == "hello_world"
        assert sanitize_filename("hello _ _ world") == "hello_world"
    
    def test_leading_trailing_chars(self):
        """Test removal of leading/trailing spaces and dots."""
        assert sanitize_filename(" .hello world. ") == "hello_world"
        assert sanitize_filename("...test...") == "test"


class TestSplitTextIntoChunks:
    """Test text chunking function."""
    
    def test_basic_splitting(self):
        """Test basic text splitting."""
        text = "word " * 100  # 100 words
        chunks = split_text_into_chunks(text, chunk_size=50)
        
        assert len(chunks) == 2
        assert len(chunks[0].split()) == 50
        assert len(chunks[1].split()) == 50
    
    def test_small_text(self):
        """Test text smaller than chunk size."""
        text = "hello world"
        chunks = split_text_into_chunks(text, chunk_size=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_minimum_chunk_merge(self):
        """Test merging of small final chunks."""
        # Create text that would result in a small final chunk
        text = "word " * 105  # 105 words with 50-word chunks = 3 chunks (50, 50, 5)
        chunks = split_text_into_chunks(text, chunk_size=50, min_chunk_size=10)
        
        # Should merge the small final chunk with the previous one
        assert len(chunks) == 2
        assert len(chunks[0].split()) == 50
        assert len(chunks[1].split()) == 55  # 50 + 5
    
    def test_no_merge_if_above_minimum(self):
        """Test that chunks above minimum size are not merged."""
        text = "word " * 120  # 120 words = 3 chunks (50, 50, 20)
        chunks = split_text_into_chunks(text, chunk_size=50, min_chunk_size=10)
        
        # Should not merge since final chunk (20 words) > min_chunk_size (10)
        assert len(chunks) == 3
        assert len(chunks[2].split()) == 20
    
    def test_empty_text(self):
        """Test empty text handling."""
        chunks = split_text_into_chunks("", chunk_size=50)
        assert len(chunks) == 1
        assert chunks[0] == ""