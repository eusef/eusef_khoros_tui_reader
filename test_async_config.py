#!/usr/bin/env python3
"""
Test config loading in an async context (like the Textual app)
"""
import asyncio
from onepassword_config import get_config_value, load_config_from_toml, clear_config_cache

async def test_in_async_context():
    """Test config loading from within an async context"""
    print("Testing config loading in async context (like Textual app)")
    print("=" * 60)
    
    # Clear cache to simulate fresh start
    clear_config_cache()
    
    print("\n1. Loading config.toml in async context...")
    try:
        config = load_config_from_toml()
        print(f"   Loaded {len(config)} values")
        print(f"   Keys: {list(config.keys())}")
        
        if 'GEMINI_API_KEY' in config:
            key = config['GEMINI_API_KEY']
            masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
            print(f"   ✅ GEMINI_API_KEY in config: {masked}")
        else:
            print(f"   ❌ GEMINI_API_KEY NOT in config")
    except Exception as e:
        print(f"   ❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. Testing get_config_value() in async context...")
    try:
        key = get_config_value("GEMINI_API_KEY")
        if key:
            if key.startswith("op://"):
                print(f"   ❌ Got unresolved op:// reference: {key}")
            else:
                masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
                print(f"   ✅ Got valid key: {masked} ({len(key)} chars)")
        else:
            print(f"   ❌ Got None")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_in_async_context())

