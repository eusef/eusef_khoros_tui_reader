# Run unified fetch script, then start app.py
# Secrets are now loaded automatically via the 1Password SDK
# Usage: ./start.sh [khoros_count] [social_count]
#   khoros_count: Number of Khoros messages to retrieve (default: 100)
#   social_count: Number of BlueSky/Mastodon posts to retrieve (default: 50)

# Set default counts if not provided
KHOROS_COUNT=${1:-100}
SOCIAL_COUNT=${2:-50}

# Run unified fetch script (authenticates with 1Password only once)
python ./fetch_all.py --khoros-count $KHOROS_COUNT --social-count $SOCIAL_COUNT

# Check if fetch was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Warning: Some data sources failed to fetch."
    echo "   The TUI will load with whatever data is available."
    echo ""
fi

echo "============================================================"
echo "🎨 Starting TUI application..."
echo "============================================================"
echo ""

python ./app.py
