#!/usr/bin/env python3
"""
Combined startup script that runs fetch and app in the same Python process.
This ensures 1Password authentication only happens once.
"""
import sys
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch data and start TUI app')
    parser.add_argument('--khoros-count', type=int, default=100,
                       help='Number of Khoros messages to fetch (default: 100)')
    parser.add_argument('--social-count', type=int, default=50,
                       help='Number of BlueSky and Mastodon posts to fetch (default: 50)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable verbose debug output')
    args = parser.parse_args()
    
    # Import and run fetch_all
    from fetch_all import main as fetch_main
    
    # Override sys.argv for fetch_all's argument parsing
    old_argv = sys.argv
    sys.argv = ['fetch_all.py', 
                '--khoros-count', str(args.khoros_count),
                '--social-count', str(args.social_count)]
    if args.debug:
        sys.argv.append('--debug')
    
    try:
        fetch_result = fetch_main()
        
        if fetch_result != 0:
            print("")
            print("⚠️  Warning: Some data sources failed to fetch.")
            print("   The TUI will load with whatever data is available.")
            print("")
    except Exception as e:
        print(f"Error during fetch: {e}")
        print("Continuing to TUI...")
    finally:
        sys.argv = old_argv
    
    print("============================================================")
    print("🎨 Starting TUI application...")
    print("============================================================")
    print("")
    
    # Import and run the app
    # Note: We can't easily call app.py's main, so we'll use run() from textual
    from app import EmailApp
    app = EmailApp()
    app.run()

if __name__ == "__main__":
    main()

