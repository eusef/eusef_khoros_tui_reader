# Khoros TUI Reader

A modern terminal-based user interface for reading Khoros forum messages and BlueSky posts using Textual. This application provides a rich, keyboard-driven experience for browsing and interacting with Khoros community content and BlueSky social media posts directly from your terminal.

## Features

- **📱 Modern TUI Interface**: Built with Textual for a responsive, modern terminal experience
- **🔐 Secure Authentication**: Integrated with 1Password CLI for secure credential management
- **📨 Message Browsing**: Browse forum messages with subject, author, and timestamp information
- **🦋 BlueSky Integration**: Fetch and display BlueSky posts alongside Khoros messages
- **🔍 Smart Filtering**: Real-time message filtering and search capabilities
- **📖 Message Viewer**: Full message content display with HTML-to-text conversion
- **🤖 AI Summarization**: Powered by Google Gemini API for intelligent message summaries
- **⚡ Performance**: Asynchronous message loading and efficient data handling
- **🛠️ Debug Tools**: Built-in debugging and connection testing utilities

## Prerequisites

- Python 3.8+
- 1Password CLI (`op`) installed and authenticated
- Access to a Khoros community
- BlueSky account with App Password (optional, for BlueSky integration)
- Google Gemini API key (optional, for AI summarization)

## Getting Started

### 1. Clone and Setup

```bash
git clone <repository-url>
cd khoros_tui_reader
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Configure the `.env.template` file with your Khoros community and BlueSky credentials:

```bash
hostname=your-community.khoros.com
username=op://path/to/1password/username
password=op://path/to/1password/password
sessionStartTime=
sessionLastUsed=
sessionKey=
tapestry=t5
BLUESKY_HANDLE=op://path/to/1password/bluesky-handle
BLUESKY_APP_PASSWORD=op://path/to/1password/bluesky-app-password
GEMINI_API_KEY=op://path/to/1password/gemini-api-key
```

**Note**: The `sessionStartTime`, `sessionLastUsed`, and `sessionKey` fields are managed automatically by the application.

### 3. Set Up 1Password Integration

1. Install 1Password CLI: https://1password.com/downloads/command-line/
2. Authenticate with your 1Password account: `op signin`
3. Store your Khoros credentials, BlueSky credentials, and Gemini API key in 1Password
4. Update the `.env.template` file with the correct 1Password references

### 4. Run the Application

#### Option A: Use the Start Script (Recommended)
```bash
# Fetch 100 messages and start the TUI
./start.sh

# Or specify a custom message count
./start.sh 50
```

#### Option B: Run Components Individually
```bash
# Test authentication
env $(op inject -i ./.env.template | xargs) python ./auth.py

# Fetch messages and save to file
env $(op inject -i ./.env.template | xargs) python ./fetch_posts.py --write-output --output-file ./current_data.json

# Start the TUI viewer
python ./app.py
```

## Usage

### Navigation
- **↑/↓**: Navigate through message list
- **Enter**: Open selected message in browser
- **q**: Quit the application

### Filtering and Search
- **/**: Enter filter mode to search messages
- **ESC**: Cancel filter mode or dismiss summary

### AI Features
- **s**: Generate AI summary of current message (requires Gemini API key)
- **t**: Test Gemini API connection

### Debug and Utilities
- **d**: Toggle debug window
- **ESC**: Dismiss dialogs and summaries

## Configuration

### Message Count
Control how many messages to fetch by modifying the `start.sh` script or passing arguments to `fetch_posts.py`:

```bash
python ./fetch_posts.py --write-output --output-file ./current_data.json --count 200
```

### BlueSky Integration
To enable BlueSky posts alongside your Khoros messages:

#### 1. Create a BlueSky App Password
1. Log into your BlueSky account at [bsky.app](https://bsky.app)
2. Go to **Settings** → **Privacy and security** → **App passwords**
3. Click **Add app password**
4. Enter a name for this application (e.g., "Khoros TUI Reader")
5. Click **Create app password**
6. **Important**: Copy the generated password immediately - you won't be able to see it again!

#### 2. Store Credentials in 1Password
1. Create a new item in 1Password for your BlueSky credentials
2. Store your BlueSky handle (e.g., `yourname.bsky.social`)
3. Store the app password you just created
4. Note the 1Password reference paths for both items

#### 3. Update Environment Configuration
Add the BlueSky credentials to your `.env.template` file:
```bash
BLUESKY_HANDLE=op://path/to/1password/bluesky-handle
BLUESKY_APP_PASSWORD=op://path/to/1password/bluesky-app-password
```

#### 4. Test the Integration
Run the application with `./start.sh` and you should see:
- 🏢 **Khoros messages** (displayed in white text)
- 🦋 **BlueSky posts** (displayed in cyan text)
- 📅 **Combined timeline** sorted by date

**Notes**: 
- BlueSky integration is optional - the app works fine with just Khoros messages
- The app searches for posts containing "1password" by default
- If BlueSky authentication fails, only Khoros messages will be displayed
- BlueSky posts are automatically cleaned of newlines for better list display

### Gemini AI Integration
To enable AI-powered message summarization:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Store it securely in 1Password
3. Update your `.env.template` file
4. Press `s` while viewing a message to generate summaries

**Note**: The Gemini API requires an internet connection and may have usage limits based on your Google Cloud account.

## Architecture

### Core Components

- **`app.py`**: Main application entry point and UI orchestration
- **`auth.py`**: Khoros authentication and session management
- **`fetch_posts.py`**: GraphQL-based message retrieval from Khoros
- **`fetch_bluesky.py`**: BlueSky API integration and post retrieval
- **`message_list.py`**: Reusable message list widget with filtering
- **`message_viewer.py`**: Message content display with HTML conversion
- **`gemini_summarizer.py`**: AI integration for message summarization
- **`keyboard_commands.py`**: Dynamic keyboard shortcut display
- **`loading_screen.py`**: Asynchronous loading interface
- **`debug_widget.py`**: Development and debugging utilities

### Data Flow

1. **Authentication**: Secure credential retrieval via 1Password CLI (Khoros + BlueSky)
2. **Data Fetching**: GraphQL queries to Khoros community API + REST API calls to BlueSky
3. **Processing**: HTML-to-text conversion, data formatting, and message normalization
4. **Display**: Rich TUI rendering with Textual framework and color-coded sources
5. **Interaction**: Keyboard-driven navigation and AI features

## Development

### Project Structure
```
khoros_tui_reader/
├── app.py                 # Main application
├── auth.py               # Authentication module
├── fetch_posts.py        # Khoros data fetching
├── fetch_bluesky.py      # BlueSky data fetching
├── message_list.py       # Message list widget
├── message_viewer.py     # Message display widget
├── gemini_summarizer.py  # AI integration
├── keyboard_commands.py  # UI controls
├── loading_screen.py     # Loading interface
├── debug_widget.py       # Debug utilities
├── summary_widget.py     # AI summary display
├── style.css             # TUI styling
├── start.sh              # Convenience script
├── requirements.txt      # Python dependencies
└── .env.template         # Environment configuration
```

### Adding New Features
The modular architecture makes it easy to extend functionality:

- **New Widgets**: Create custom Textual widgets in separate modules
- **API Integration**: Add new data sources in dedicated modules
- **UI Enhancements**: Modify `style.css` for visual improvements
- **Keyboard Shortcuts**: Extend `keyboard_commands.py` for new interactions

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify 1Password CLI is authenticated: `op whoami`
- Check credential paths in `.env.template`
- Ensure your Khoros community credentials are correct

**No Messages Displayed**
- Check if `current_data.json` exists and contains data
- Verify network connectivity to your Khoros community
- Check authentication token validity

**Gemini API Issues**
- Verify API key is correctly stored in 1Password
- Check internet connectivity
- Test connection with `t` key in the application

**BlueSky Integration Issues**
- Verify BlueSky handle and app password are correctly stored in 1Password
- Check that your BlueSky app password hasn't expired
- Ensure your BlueSky account is active and not suspended
- Test authentication by running: `env $(op inject -i ./.env.template | xargs) python -c "from fetch_bluesky import create_bluesky_session; print('Token:', create_bluesky_session() is not None)"`
- If BlueSky fails, the app will continue with only Khoros messages

**Performance Issues**
- Reduce message count in `start.sh` or fetch command
- Check network latency to Khoros community
- Monitor system resources during operation

### Debug Mode
Enable debug mode with the `d` key to see detailed application state and error information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the debug output (press `d` in the application)
- Open an issue on the repository