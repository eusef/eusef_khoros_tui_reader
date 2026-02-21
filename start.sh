# Run unified fetch script, then start app.py
# Secrets are now loaded automatically via the 1Password SDK
# Usage: ./start.sh [khoros_count] [social_count] [--debug]
#   khoros_count: Number of Khoros messages to retrieve (default: 100)
#   social_count: Number of BlueSky/Mastodon posts to retrieve (default: 50)
#   --debug: Enable verbose debug output (optional)

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Run ./setup.sh first to set up the project, then try again."
    exit 1
fi

# Check for config.toml
if [ ! -f "config.toml" ]; then
    echo "Error: config.toml not found."
    echo "Run ./setup.sh first, then edit config.toml with your settings."
    exit 1
fi

# Parse arguments
KHOROS_COUNT=${1:-100}
SOCIAL_COUNT=${2:-50}
DEBUG_FLAG=""

# Check if --debug flag is present in any position
for arg in "$@"; do
    if [ "$arg" = "--debug" ]; then
        DEBUG_FLAG="--debug"
        break
    fi
done

# Run unified script that fetches data and starts app in a single Python process
# This ensures 1Password authentication only happens once
source ./.venv/bin/activate
python ./start_combined.py --khoros-count $KHOROS_COUNT --social-count $SOCIAL_COUNT $DEBUG_FLAG
