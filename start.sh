# Run fetch_posts.py, fetch BlueSky, fetch Mastodon, then start app.py
# Secrets are now loaded automatically via the 1Password SDK
# Usage: ./start.sh [count]
#   count: Number of messages to retrieve (default: 100)

# Set default count if not provided
MESSAGE_COUNT=${1:-100}

echo "============================================================"
echo "🚀 KHOROS TUI READER - DATA LOADING"
echo "============================================================"
echo ""

echo "📥 [1/3] Fetching $MESSAGE_COUNT Khoros messages..."
python ./fetch_posts.py --write-output --output-file ./current_data.json --count $MESSAGE_COUNT

if [ $? -eq 0 ]; then
    echo "✅ Khoros messages saved to current_data.json"
else
    echo "⚠️  Warning: Khoros fetch failed, continuing anyway..."
fi

echo ""
echo "🦋 [2/3] Fetching BlueSky posts..."
python ./fetch_bluesky.py --write-output --output-file ./bluesky_data.json --count 50

if [ $? -eq 0 ]; then
    echo "✅ BlueSky posts saved to bluesky_data.json"
else
    echo "⚠️  Warning: BlueSky fetch failed, continuing anyway..."
fi

echo ""
echo "🐘 [3/3] Fetching Mastodon posts..."
python ./fetch_mastodon.py --write-output --output-file ./mastodon_data.json --count 50

if [ $? -eq 0 ]; then
    echo "✅ Mastodon posts saved to mastodon_data.json"
else
    echo "⚠️  Warning: Mastodon fetch failed, continuing anyway..."
fi

echo ""
echo "============================================================"
echo "🎨 Starting TUI application..."
echo "============================================================"
echo ""

python ./app.py
