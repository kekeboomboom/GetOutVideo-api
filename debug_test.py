#!/usr/bin/env python3

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simple debug test without external dependencies
def debug_api_issue():
    """Simple test to identify where the 0 files issue occurs."""
    print("DEBUG: Testing API issue...")
    
    # First, let's test if we can import the API modules
    try:
        from api.config import APIConfig, TranscriptConfig, ProcessingConfig
        print("✓ Successfully imported API config modules")
    except ImportError as e:
        print(f"✗ Failed to import API config: {e}")
        return False
    
    try:
        from api.models import VideoTranscript, ProcessingResult  
        print("✓ Successfully imported API models")
    except ImportError as e:
        print(f"✗ Failed to import API models: {e}")
        return False
        
    try:
        from api import process_youtube_playlist
        print("✓ Successfully imported process_youtube_playlist function")
    except ImportError as e:
        print(f"✗ Failed to import main API function: {e}")
        return False
        
    # Test basic configuration creation
    try:
        config = APIConfig(gemini_api_key="test-key")
        print(f"✓ Successfully created APIConfig: {config}")
    except Exception as e:
        print(f"✗ Failed to create APIConfig: {e}")
        return False
        
    # Test if we can create the main classes
    try:
        from api import WatchYTPL4MeAPI
        api = WatchYTPL4MeAPI("test-key")
        print("✓ Successfully created WatchYTPL4MeAPI instance")
    except Exception as e:
        print(f"✗ Failed to create WatchYTPL4MeAPI: {e}")
        return False
    
    print("DEBUG: All basic imports and object creation successful.")
    return True

if __name__ == "__main__":
    success = debug_api_issue()
    if not success:
        print("\nDEBUG: Basic setup failed. Dependencies issue likely.")
        sys.exit(1)
    else:
        print("\nDEBUG: Basic setup works. The issue is likely in the processing logic or missing API keys.")