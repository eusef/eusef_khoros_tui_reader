# Run fetch_posts.py, then start app.py
# Secrets are now loaded automatically via the 1Password SDK
# Usage: ./start.sh [count]
#   count: Number of messages to retrieve (default: 100)

# Set default count if not provided
MESSAGE_COUNT=${1:-100}

echo "Fetching $MESSAGE_COUNT messages..."

python ./fetch_posts.py --write-output --output-file ./current_data.json --count $MESSAGE_COUNT

echo "Starting TUI application..."

python ./app.py
