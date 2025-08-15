#!/bin/bash

# Inject secrets from 1Password, run fetch_posts.py, then start app.py
# Usage: ./start.sh [count]
#   count: Number of messages to retrieve (default: 100)

# Set default count if not provided
MESSAGE_COUNT=${1:-100}

echo "Fetching $MESSAGE_COUNT messages..."

env $(op inject -i ./.env.template | xargs) \
  python ./fetch_posts.py --write-output --output-file ./top_posters_output.json --count $MESSAGE_COUNT

python ./app.py
