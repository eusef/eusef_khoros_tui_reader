#!/usr/bin/env python3
"""
Fetch all data sources (Khoros, BlueSky, Mastodon) in a single run.
This ensures 1Password authentication happens only once.
"""
import sys
import json
import argparse
from datetime import datetime

# Import fetch functions
from fetch_posts import fetch_posts
from fetch_bluesky import fetch_bluesky_posts
from fetch_mastodon import fetch_mastodon_posts
from auth import get_hostname

def main():
    parser = argparse.ArgumentParser(description='Fetch all messages from Khoros, BlueSky, and Mastodon')
    parser.add_argument('--khoros-count', type=int, default=100,
                       help='Number of Khoros messages to fetch (default: 100)')
    parser.add_argument('--social-count', type=int, default=50,
                       help='Number of BlueSky and Mastodon posts to fetch (default: 50)')
    parser.add_argument('--khoros-output', default='./current_data.json',
                       help='Output file for Khoros messages (default: ./current_data.json)')
    parser.add_argument('--bluesky-output', default='./bluesky_data.json',
                       help='Output file for BlueSky posts (default: ./bluesky_data.json)')
    parser.add_argument('--mastodon-output', default='./mastodon_data.json',
                       help='Output file for Mastodon posts (default: ./mastodon_data.json)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable verbose debug output')
    args = parser.parse_args()
    
    # Set debug mode for fetch modules
    import os
    if args.debug:
        os.environ['FETCH_DEBUG'] = '1'

    if args.debug:
        print("=" * 60)
        print("🚀 KHOROS TUI READER - UNIFIED DATA FETCH")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("NOTE: You may be prompted to authenticate with 1Password.")
        print("      This will happen ONCE for all data sources.")
        print("=" * 60)
        print()
    else:
        print("Fetching data from Khoros, BlueSky, and Mastodon...")

    success_count = 0
    failed_sources = []

    # Fetch Khoros messages
    if args.debug:
        print("📥 [1/3] Fetching Khoros messages...")
        print("-" * 60)
    try:
        hostname = get_hostname()
        # fetch_posts constructs its own URL, just pass the base hostname
        khoros_data = fetch_posts(hostname, args.khoros_count)
        
        if khoros_data:
            with open(args.khoros_output, 'w') as f:
                json.dump(khoros_data, f, indent=2)
            if not args.debug:
                print("  ✅ Khoros")
            else:
                print(f"✅ Khoros: Saved to {args.khoros_output}")
                print()
            success_count += 1
        else:
            print(f"  ⚠️  Khoros: No data returned")
            if args.debug:
                print()
            failed_sources.append("Khoros")
    except Exception as e:
        if args.debug:
            print(f"❌ Khoros: Failed with error: {e}")
            print()
        else:
            print(f"  ❌ Khoros: {e}")
        failed_sources.append("Khoros")

    # Fetch BlueSky posts
    if args.debug:
        print("🦋 [2/3] Fetching BlueSky posts...")
        print("-" * 60)
    try:
        bluesky_posts = fetch_bluesky_posts(post_count=args.social_count)
        
        if bluesky_posts:
            with open(args.bluesky_output, 'w') as f:
                json.dump(bluesky_posts, f, indent=2)
            if not args.debug:
                print("  ✅ BlueSky")
            else:
                print(f"✅ BlueSky: Saved to {args.bluesky_output}")
                print()
            success_count += 1
        else:
            print(f"  ⚠️  BlueSky: No posts returned")
            if args.debug:
                print()
            failed_sources.append("BlueSky")
    except Exception as e:
        if args.debug:
            print(f"❌ BlueSky: Failed with error: {e}")
            print()
        else:
            print(f"  ❌ BlueSky: {e}")
        failed_sources.append("BlueSky")

    # Fetch Mastodon posts
    if args.debug:
        print("🐘 [3/3] Fetching Mastodon posts...")
        print("-" * 60)
    try:
        mastodon_posts = fetch_mastodon_posts(post_count=args.social_count)
        
        if mastodon_posts:
            with open(args.mastodon_output, 'w') as f:
                json.dump(mastodon_posts, f, indent=2)
            if not args.debug:
                print("  ✅ Mastodon")
            else:
                print(f"✅ Mastodon: Saved to {args.mastodon_output}")
                print()
            success_count += 1
        else:
            print(f"  ⚠️  Mastodon: No posts returned")
            if args.debug:
                print()
            failed_sources.append("Mastodon")
    except Exception as e:
        if args.debug:
            print(f"❌ Mastodon: Failed with error: {e}")
            print()
        else:
            print(f"  ❌ Mastodon: {e}")
        failed_sources.append("Mastodon")

    # Summary
    if args.debug:
        print("=" * 60)
        print("📊 FETCH SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {success_count}/3 data sources")
        if failed_sources:
            print(f"❌ Failed: {', '.join(failed_sources)}")
        else:
            print("🎉 All data sources fetched successfully!")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
    else:
        if success_count == 3:
            print("Done! ✨")
        else:
            print(f"Done ({success_count}/3 sources succeeded)")
            if failed_sources:
                print(f"Failed: {', '.join(failed_sources)}")

    # Return exit code based on success
    if success_count == 0:
        print("⚠️  Warning: No data sources were successfully fetched!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

