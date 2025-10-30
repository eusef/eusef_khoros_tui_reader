#!/usr/bin/env python3
"""
Test that the app can initialize the GeminiSummarizer without errors
"""
import asyncio
from gemini_summarizer import GeminiSummarizer

async def test_app_init():
    """Test initializing GeminiSummarizer in async context (like the real app)"""
    print("Testing GeminiSummarizer initialization in async context...")
    print("=" * 60)
    
    try:
        summarizer = GeminiSummarizer()
        
        if summarizer.is_available():
            print("✅ GeminiSummarizer initialized successfully!")
            print(f"   Status: {summarizer.get_status_message()}")
            
            # Test the connection
            print("\nTesting API connection...")
            result = await summarizer.test_connection()
            print(f"   {result}")
        else:
            print("❌ GeminiSummarizer not available")
            print(f"   Status: {summarizer.get_status_message()}")
    except Exception as e:
        print(f"❌ Error initializing GeminiSummarizer: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_app_init())

