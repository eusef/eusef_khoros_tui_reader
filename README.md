# Khoros TUI Reader

A terminal-based user interface for reading Khoros forum messages using Textual.

## Installation

1. python -m venv .venv && pip install -r requirements.txt

## Gemini AI Integration

This application includes AI-powered message summarization using Google's Gemini API. To use this feature:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set the environment variable: `export GEMINI_API_KEY=your_api_key_here`
3. Press `s` while viewing a message to generate an AI summary

**Note:** The Gemini API requires an internet connection and may have usage limits based on your Google Cloud account.

### Testing Gemini Integration

Before running the main application, you can test your Gemini API setup:

```bash
python test_gemini.py
```

This will verify your API key and test the connection to ensure everything is working correctly.

## Components

### MessageList (`message_list.py`)

A reusable Textual widget for displaying lists of messages. This component has been refactored into its own module for reusability.

**Features:**
- Displays messages with subject and age
- Handles message selection events
- Supports loading messages from JSON files
- Dynamic message updates
- Responsive layout with proper text truncation

**Usage:**
```python
from message_list import MessageList, MessageSelected, load_messages_from_json

# Create a message list with pre-loaded messages
messages = load_messages_from_json("messages.json")
message_list = MessageList(messages, id="message-list")

# Or create empty and load later
message_list = MessageList(id="message-list")
message_list.load_messages_from_file("messages.json")

# Update messages dynamically
message_list.update_messages(new_messages)
```

## To run using 1Password CLI

If you just want to run individually
	env $(op inject -i ./.env.template | xargs) python ./auth.py

To generate the post data for the viewer
	env $(op inject -i ./.env.template | xargs) python ./fetch_posts.py --write-output --output-file ./top_posters_output.json

To run the viewer
	python ./app.py

## Examples

See `example_usage.py` for a demonstration of how to reuse the MessageList component in different applications.