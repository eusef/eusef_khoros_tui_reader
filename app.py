import subprocess
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Input
from textual.reactive import reactive
from textual import log
from textual import on
from textual.events import Key
from textual.binding import Binding
from message_list import MessageList, MessageSelected, load_messages_from_json, calculate_age
from message_viewer import MessageViewer
from keyboard_commands import KeyboardCommands
from loading_screen import LoadingScreen
from debug_widget import DebugWidget
from gemini_summarizer import GeminiSummarizer
from summary_widget import SummaryWidget
import json
import os
import re
 
# Load messages from JSON file
MESSAGES = []

class FilterInput(Input):
    """A filter input widget that can be shown/hidden"""
    
    def __init__(self, **kwargs) -> None:
        super().__init__(placeholder="Filter messages...", **kwargs)
        self.styles.display = "none"
    
    def show(self) -> None:
        """Show the filter input and focus it"""
        self.styles.display = "block"
        self.focus()
    
    def hide(self) -> None:
        """Hide the filter input and clear it"""
        self.styles.display = "none"
        self.value = ""
        self.blur()

class EmailApp(App):
    CSS_PATH = "style.css"
    
    # Track if we're in filter mode
    filter_mode = reactive(False)
    
    # Track if loading is complete
    loading_complete = reactive(False)
    
    # Define key bindings
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "filter", "Filter"),
        Binding("escape", "cancel_or_dismiss", "Cancel Filter/Dismiss Summary", show=False),
        Binding("enter", "open_href", "Open in Browser"),
        Binding("d", "toggle_debug", "Toggle Debug", show=False),
        Binding("s", "summarize", "Summarize Message"),
        Binding("S", "summarize_all", "Summarize All Visible Messages"),
        Binding("t", "test_gemini", "Test Gemini Connection", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            with Container(id="content-area"):
                yield MessageList(MESSAGES, id="message-list")
                yield MessageViewer(id="message-viewer")
            yield SummaryWidget(id="summary-widget")
            yield FilterInput(id="filter-input")
            yield KeyboardCommands(id="keyboard-commands")
            yield DebugWidget(id="debug-widget")
            yield LoadingScreen(id="loading-screen")
    
    def on_mount(self) -> None:
        """Called when the app is mounted - show loading screen first"""
        # Initialize Gemini summarizer
        self.gemini_summarizer = GeminiSummarizer()
        
        # Initially hide the main interface and show loading screen
        self.hide_main_interface()
        self.show_loading_screen()
        
        # Start loading messages asynchronously
        self.call_after_refresh(self.load_messages_async)
        
        # Store reference to message list for later use
        self.message_list = self.query_one("#message-list", MessageList)
    
    def on_unmount(self) -> None:
        """Called when app is unmounting - clean up resources"""
        from onepassword_config import clear_op_client
        try:
            clear_op_client()
            log.info("App unmounted, 1Password client closed")
        except Exception as e:
            log.error(f"Error closing 1Password client during unmount: {e}")
    
    def load_bluesky_from_json(self, json_file_path: str = "bluesky_data.json") -> list:
        """Load BlueSky posts from JSON file"""
        bluesky_messages = []
        if not os.path.exists(json_file_path):
            print(f"⚠️  BlueSky data file not found: {json_file_path}")
            return []
        
        try:
            with open(json_file_path, 'r') as f:
                bluesky_posts = json.load(f)
            
            if not bluesky_posts:
                print(f"⚠️  BlueSky data file is empty")
                return []
            
            print(f"→ Processing {len(bluesky_posts)} BlueSky posts from {json_file_path}...")
            for post in bluesky_posts:
                # Extract text and date from the record field
                record = post.get('record', {})
                raw_text = record.get('text', 'No content')
                
                # Clean up text for list display: remove newlines and extra whitespace
                clean_text = ' '.join(raw_text.split())
                created_at = record.get('createdAt', post.get('indexedAt', ''))
                
                bluesky_messages.append({
                    "subject": clean_text,
                    "body": raw_text,
                    "id": post['uri'],
                    "postTime": created_at,
                    "viewHref": f"https://bsky.app/profile/{post['author']['handle']}/post/{post['uri'].split('/')[-1]}",
                    "author": {
                        "title": post['author'].get('displayName', ''),
                        "lastName": "",
                        "firstName": post['author']['handle'],
                    },
                    "source": "bluesky",
                    "age": calculate_age(created_at)
                })
            print(f"✅ Processed {len(bluesky_messages)} BlueSky messages\n")
            return bluesky_messages
        except Exception as e:
            print(f"❌ Error loading BlueSky data: {e}\n")
            log.error(f"Error loading BlueSky data from {json_file_path}: {e}")
            return []
    
    def load_mastodon_from_json(self, json_file_path: str = "mastodon_data.json") -> list:
        """Load Mastodon posts from JSON file"""
        mastodon_messages = []
        if not os.path.exists(json_file_path):
            print(f"⚠️  Mastodon data file not found: {json_file_path}")
            return []
        
        try:
            with open(json_file_path, 'r') as f:
                mastodon_posts = json.load(f)
            
            if not mastodon_posts:
                print(f"⚠️  Mastodon data file is empty")
                return []
            
            print(f"→ Processing {len(mastodon_posts)} Mastodon posts from {json_file_path}...")
            for i, post in enumerate(mastodon_posts):
                try:
                    # Extract text content, handling HTML
                    raw_content = post.get('content', 'No content')
                    clean_content = re.sub(r'<[^>]+>', '', raw_content)
                    clean_subject = ' '.join(clean_content.split())
                    
                    # Validate required fields
                    if not post.get('id'):
                        log.warning(f"Mastodon post {i} missing 'id', skipping")
                        continue
                    if not post.get('created_at'):
                        log.warning(f"Mastodon post {i} missing 'created_at', skipping")
                        continue
                    if 'account' not in post:
                        log.warning(f"Mastodon post {i} missing 'account', skipping")
                        continue
                    
                    mastodon_messages.append({
                        "subject": clean_subject,
                        "body": clean_content,
                        "id": post['id'],
                        "postTime": post['created_at'],
                        "viewHref": post['url'] if post.get('url') else f"{post.get('uri', '')}",
                        "author": {
                            "title": post['account'].get('display_name', ''),
                            "lastName": "",
                            "firstName": post['account']['username'],
                        },
                        "source": "mastodon",
                        "age": calculate_age(post['created_at'])
                    })
                except Exception as post_error:
                    print(f"  ⚠️  Error processing Mastodon post {i}: {post_error}")
                    log.error(f"Error processing Mastodon post {i}: {post_error}")
                    continue
            
            print(f"✅ Processed {len(mastodon_messages)} Mastodon messages\n")
            return mastodon_messages
        except Exception as e:
            print(f"❌ Error loading Mastodon data: {e}\n")
            log.error(f"Error loading Mastodon data from {json_file_path}: {e}")
            return []

    async def load_all_messages(self):
        print(f"\n{'='*60}")
        print(f"📊 LOADING ALL MESSAGES - TUI MODE")
        print(f"{'='*60}\n")
        
        print("[STEP 1] Loading Khoros messages from current_data.json...")
        khoros_messages = load_messages_from_json("current_data.json")
        for msg in khoros_messages:
            msg['source'] = 'khoros'
        print(f"✅ Loaded {len(khoros_messages)} Khoros messages\n")

        # Load BlueSky posts from JSON file (fetched by start.sh)
        print("[STEP 2] Loading BlueSky posts from bluesky_data.json...")
        bluesky_messages = []
        try:
            bluesky_messages = self.load_bluesky_from_json("bluesky_data.json")
            if not bluesky_messages:
                print(f"⚠️  No BlueSky messages loaded\n")
            log.info(f"Loaded {len(bluesky_messages)} BlueSky messages")
        except Exception as e:
            print(f"❌ BlueSky loading failed: {e}\n")
            log.warning(f"Failed to load BlueSky messages: {e}")

        # Load Mastodon posts from JSON file (fetched by start.sh)
        print("[STEP 3] Loading Mastodon posts from mastodon_data.json...")
        mastodon_messages = []
        try:
            mastodon_messages = self.load_mastodon_from_json("mastodon_data.json")
            if not mastodon_messages:
                print(f"⚠️  No Mastodon messages loaded\n")
            log.info(f"Loaded {len(mastodon_messages)} Mastodon messages")
        except Exception as e:
            print(f"❌ Mastodon loading failed: {e}\n")
            log.warning(f"Failed to load Mastodon messages: {e}")

        print("[STEP 4] Combining and sorting messages...")
        combined_messages = khoros_messages + bluesky_messages + mastodon_messages
        print(f"Combined totals before sorting:")
        print(f"  • Khoros: {len(khoros_messages)}")
        print(f"  • BlueSky: {len(bluesky_messages)}")
        print(f"  • Mastodon: {len(mastodon_messages)}")
        print(f"  • TOTAL: {len(combined_messages)}")
        
        # Sort by actual datetime, not string - need to parse timestamps properly
        def parse_timestamp(timestamp_str):
            """Parse various timestamp formats to datetime for proper sorting"""
            from datetime import datetime, timezone
            try:
                # Handle different timestamp formats
                if '.' in timestamp_str and timestamp_str.endswith('Z'):
                    # BlueSky format: 2024-07-15T18:30:00.123Z
                    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                elif timestamp_str.endswith('Z'):
                    # Some formats without microseconds: 2024-07-15T18:30:00Z
                    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                elif '+' in timestamp_str or timestamp_str.endswith(('-07:00', '-08:00', '+00:00')):
                    # Khoros/Mastodon format with timezone: 2024-07-15T18:30:00.123-07:00
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    # Fallback: try to parse as ISO format
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                log.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
                # Return epoch time as fallback so message doesn't break sorting
                return datetime(1970, 1, 1, tzinfo=timezone.utc)
        
        combined_messages.sort(key=lambda x: parse_timestamp(x['postTime']), reverse=True)
        
        # Count by source after sorting
        source_counts = {}
        for msg in combined_messages:
            source = msg.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print(f"\n✅ Sorting complete. Final message counts by source:")
        for source, count in sorted(source_counts.items()):
            icon = {"khoros": "🏢", "bluesky": "🦋", "mastodon": "🐘"}.get(source, "❓")
            print(f"  {icon} {source}: {count}")
        print(f"  📊 TOTAL: {len(combined_messages)}")
        print(f"{'='*60}\n")
        
        log.info(f"Total messages loaded: {len(combined_messages)} ({len(khoros_messages)} Khoros, {len(bluesky_messages)} BlueSky, {len(mastodon_messages)} Mastodon)")
        return combined_messages

    async def load_messages_async(self) -> None:
        """Load messages asynchronously and transition to main interface when complete"""
        try:
            loading_screen = self.query_one("#loading-screen", LoadingScreen)
            loading_screen.update("⠋ Checking message data...")

            global MESSAGES
            MESSAGES = await self.load_all_messages()

            # Small delay to show loading animation (can be adjusted)
            await asyncio.sleep(0.3)

            # Check if messages loaded successfully
            if MESSAGES:
                # Transition to main interface
                self.transition_to_main_interface()
            else:
                # Handle case where no messages were loaded
                self.handle_no_messages()
        except Exception as e:
            log.error(f"Error loading messages: {e}")
            self.handle_loading_error(str(e))
    
    def handle_no_messages(self) -> None:
        """Handle case where no messages were loaded"""
        loading_screen = self.query_one("#loading-screen", LoadingScreen)
        loading_screen.update_message("No messages found. Press 'q' to quit.")
        # Keep loading screen visible with error message
    
    def handle_loading_error(self, error_msg: str) -> None:
        """Handle loading errors"""
        loading_screen = self.query_one("#loading-screen", LoadingScreen)
        loading_screen.update_message(f"Error loading messages: {error_msg}\nPress 'q' to quit.")
        # Keep loading screen visible with error message
    
    def hide_main_interface(self) -> None:
        """Hide the main interface widgets"""
        content_area = self.query_one("#content-area", Container)
        summary_widget = self.query_one("#summary-widget", SummaryWidget)
        filter_input = self.query_one("#filter-input", FilterInput)
        keyboard_commands = self.query_one("#keyboard-commands", KeyboardCommands)
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        
        content_area.styles.display = "none"
        summary_widget.styles.display = "none"
        filter_input.styles.display = "none"
        keyboard_commands.styles.display = "none"
        debug_widget.styles.display = "none"
    
    def show_loading_screen(self) -> None:
        """Show the loading screen"""
        loading_screen = self.query_one("#loading-screen", LoadingScreen)
        loading_screen.styles.display = "block"
    
    def show_main_interface(self) -> None:
        """Show the main interface widgets"""
        content_area = self.query_one("#content-area", Container)
        summary_widget = self.query_one("#summary-widget", SummaryWidget)
        filter_input = self.query_one("#filter-input", FilterInput)
        keyboard_commands = self.query_one("#keyboard-commands", KeyboardCommands)
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        
        content_area.styles.display = "block"
        summary_widget.styles.display = "none"  # Keep hidden initially
        filter_input.styles.display = "none"  # Keep hidden initially
        keyboard_commands.styles.display = "block"
        debug_widget.styles.display = "none"  # Keep hidden initially
    
    def transition_to_main_interface(self) -> None:
        """Transition from loading screen to main interface"""
        # Set loading screen to not loading state
        loading_screen = self.query_one("#loading-screen", LoadingScreen)
        loading_screen.set_loading_state(False)
        
        # Hide loading screen
        loading_screen.hide()
        
        # Show main interface
        self.show_main_interface()
        
        # Initialize the app as before
        if MESSAGES:
            print(f"[TUI] About to update message list with {len(MESSAGES)} messages")
            # Get the message list widget and update it with loaded messages
            message_list = self.query_one("#message-list", MessageList)
            print(f"[TUI] Found message_list widget: {message_list}")
            print(f"[TUI] Calling update_messages...")
            message_list.update_messages(MESSAGES)
            print(f"[TUI] Update complete. Message list now has {len(message_list.messages)} messages")
            # Give focus to the message list first
            message_list.focus()
            # Then select the first item (index 0) - this will trigger MessageSelected event
            if len(MESSAGES) > 0:
                message_list.index = 0
                print(f"[TUI] Set index to 0")
        else:
            print(f"[TUI] WARNING: MESSAGES is empty or None!")
        
        self.loading_complete = True

    @on(MessageSelected)
    def on_message_selected(self, event: MessageSelected) -> None:
        log.info(f"on_message_selected called with item: {event.item}")
        viewer = self.query_one("#message-viewer", MessageViewer)
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        log.info(f"Found viewer: {viewer}")
        viewer.set_message(event.item)
        debug_widget.update_debug_info(f"Selected: {event.item['subject'][:50]}...")
        log.info("Set viewer content")
        
        # Hide summary when a new message is selected
        summary_widget = self.query_one("#summary-widget", SummaryWidget)
        if summary_widget:
            summary_widget.hide_summary()

    def action_filter(self) -> None:
        """Action to show filter input"""
        log.info("Filter action triggered")
        if not self.filter_mode:
            self.show_filter()
    
    def action_cancel_or_dismiss(self) -> None:
        """Action to hide filter input or dismiss summary window"""
        log.info("Cancel or dismiss action triggered")
        
        # Check if summary widget is visible and dismiss it first
        summary_widget = self.query_one("#summary-widget", SummaryWidget)
        if summary_widget.styles.display != "none":
            log.info("Summary widget visible, dismissing it")
            summary_widget.hide_summary()
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("Summary dismissed")
            # Return focus to the message list
            message_list = self.query_one("#message-list", MessageList)
            message_list.focus()
            return
        
        # If no summary visible, handle filter cancellation
        if self.filter_mode:
            log.info("Filter mode active, canceling filter")
            self.hide_filter()
    
    def action_open_href(self) -> None:
        """Action to open the current message's HREF in the browser"""
        log.info("action_open_href called")
        
        # Get the currently selected message
        message_list = self.query_one("#message-list", MessageList)
        log.info(f"Message list index: {message_list.index}")
        log.info(f"Message list length: {len(message_list.messages)}")
        
        if message_list.index is not None and 0 <= message_list.index < len(message_list.messages):
            selected_message = message_list.messages[message_list.index]
            log.info(f"Selected message: {selected_message}")
            
            if "viewHref" in selected_message and selected_message["viewHref"]:
                href = selected_message["viewHref"]
                log.info(f"Opening HREF in browser: {href}")
                
                try:
                    # Use the 'open' command to open URL in default browser
                    subprocess.run(["open", href], check=True)
                    debug_widget = self.query_one("#debug-widget", DebugWidget)
                    debug_widget.update_debug_info(f"Opened: {href}")
                except subprocess.CalledProcessError as e:
                    log.error(f"Error opening HREF: {e}")
                    debug_widget = self.query_one("#debug-widget", DebugWidget)
                    debug_widget.update_debug_info(f"Error opening HREF: {e}")
                except FileNotFoundError:
                    log.error("'open' command not found (not on macOS)")
                    debug_widget = self.query_one("#debug-widget", DebugWidget)
                    debug_widget.update_debug_info("'open' command not available on this system")
            else:
                log.warning("No viewHref found in selected message")
                debug_widget = self.query_one("#debug-widget", DebugWidget)
                debug_widget.update_debug_info("No HREF available for this message")
        else:
            log.warning("No message selected")
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("No message selected")
    
    def action_toggle_debug(self) -> None:
        """Action to toggle debug widget visibility"""
        log.info("Toggle debug action triggered")
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        
        if debug_widget.styles.display == "none":
            debug_widget.styles.display = "block"
            # Show Gemini status when debug is first shown
            gemini_status = self.gemini_summarizer.get_status_message()
            debug_widget.update_debug_info(f"Debug window shown | {gemini_status}")
        else:
            debug_widget.styles.display = "none"
            debug_widget.update_debug_info("Debug window hidden")
    
    def action_summarize(self) -> None:
        """Action to summarize the currently selected message using Gemini"""
        log.info("Summarize action triggered")
        
        # Get the currently selected message
        message_list = self.query_one("#message-list", MessageList)
        log.info(f"Message list index: {message_list.index}")
        log.info(f"Message list length: {len(message_list.messages)}")
        
        if message_list.index is not None and 0 <= message_list.index < len(message_list.messages):
            selected_message = message_list.messages[message_list.index]
            log.info(f"Selected message for summarization: {selected_message}")
            
            # Check if summary is already visible - if so, hide it
            summary_widget = self.query_one("#summary-widget", SummaryWidget)
            log.info(f"Summary widget found: {summary_widget}")
            log.info(f"Summary widget current display: {summary_widget.styles.display}")
            
            if summary_widget.styles.display != "none":
                log.info("Summary already visible, hiding it")
                summary_widget.hide_summary()
                debug_widget = self.query_one("#debug-widget", DebugWidget)
                debug_widget.update_debug_info("Summary hidden")
                # Give focus back to the message list
                message_list.focus()
                return
            
            # Show summary widget and start loading
            log.info("Showing summary widget")
            summary_widget.show_summary()
            summary_widget.set_loading(True)
            
            # Start async summarization
            self.call_after_refresh(self.summarize_message_async, selected_message)
            
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("Generating summary with Gemini...")
            
            # Keep focus on summary widget so user can scroll when ready
            summary_widget.focus()
        else:
            log.warning("No message selected for summarization")
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("No message selected for summarization")
    
    async def summarize_message_async(self, message_data: dict) -> None:
        """Asynchronously summarize a message using Gemini"""
        try:
            log.info("Starting message summarization")
            
            # Generate summary
            summary = await self.gemini_summarizer.summarize_message(message_data)
            
            # Update summary widget
            summary_widget = self.query_one("#summary-widget", SummaryWidget)
            summary_widget.set_summary(summary)
            
            # Ensure focus is on the summary widget so user can scroll
            summary_widget.focus()
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("✅ Summary ready (use ↑/↓ to scroll)")
            
            log.info("Message summarization completed")
            
        except Exception as e:
            log.error(f"Error during summarization: {e}")
            
            # Show error in summary widget
            summary_widget = self.query_one("#summary-widget", SummaryWidget)
            summary_widget.set_summary(f"Error generating summary: {str(e)}")
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info(f"❌ Summarization error: {str(e)}")
    
    def action_test_gemini(self) -> None:
        """Action to test the Gemini API connection"""
        log.info("Test Gemini action triggered")
        
        if not hasattr(self, 'gemini_summarizer'):
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("Gemini summarizer not initialized")
            return
        
        # Show debug widget if hidden
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        if debug_widget.styles.display == "none":
            debug_widget.styles.display = "block"
        
        debug_widget.update_debug_info("Testing Gemini connection...")
        
        # Start async test
        self.call_after_refresh(self.test_gemini_async)
    
    async def test_gemini_async(self) -> None:
        """Asynchronously test the Gemini API connection"""
        try:
            log.info("Starting Gemini connection test")
            
            # Test connection
            result = await self.gemini_summarizer.test_connection()
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info(f"Gemini test result: {result}")
            
            log.info(f"Gemini test completed: {result}")
            
        except Exception as e:
            log.error(f"Error during Gemini test: {e}")
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info(f"Gemini test error: {str(e)}")
    
    def action_summarize_all(self) -> None:
        """Action to summarize all visible messages in the message list"""
        log.info("Summarize all action triggered (Shift+S pressed)")
        
        # Get the message list
        message_list = self.query_one("#message-list", MessageList)
        visible_messages = message_list.messages
        
        log.info(f"Number of visible messages: {len(visible_messages)}")
        
        # Always update debug widget to show the feature was triggered
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        
        if not visible_messages:
            log.warning("No visible messages to summarize")
            debug_widget.update_debug_info("⚠️ No visible messages to summarize")
            return
        
        # Show immediate feedback
        debug_widget.update_debug_info(f"🔄 Preparing to summarize {len(visible_messages)} messages...")
        
        # Check if summary is already visible - if so, hide it
        summary_widget = self.query_one("#summary-widget", SummaryWidget)
        log.info(f"Summary widget found: {summary_widget}")
        log.info(f"Summary widget current display: {summary_widget.styles.display}")
        
        if summary_widget.styles.display != "none":
            log.info("Summary already visible, hiding it")
            summary_widget.hide_summary()
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("Summary hidden")
            # Give focus back to the message list
            message_list.focus()
            return
        
        # Show summary widget and start loading
        log.info("Showing summary widget for all messages")
        summary_widget.show_summary()
        summary_widget.set_loading(True)
        
        # Start async summarization
        self.call_after_refresh(self.summarize_all_messages_async, visible_messages)
        
        debug_widget.update_debug_info(f"Generating summary for {len(visible_messages)} messages...")
        
        # Keep focus on summary widget so user can scroll when ready
        summary_widget.focus()
    
    async def summarize_all_messages_async(self, messages: list) -> None:
        """Asynchronously summarize all visible messages using Gemini"""
        try:
            log.info(f"Starting summarization of {len(messages)} messages")
            
            # Generate summary
            summary = await self.gemini_summarizer.summarize_multiple_messages(messages)
            
            # Update summary widget
            summary_widget = self.query_one("#summary-widget", SummaryWidget)
            summary_widget.set_summary(summary)
            
            # Ensure focus is on the summary widget so user can scroll
            summary_widget.focus()
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info(f"✅ Summary of {len(messages)} messages ready (use ↑/↓ to scroll)")
            
            log.info("Multi-message summarization completed")
            
        except Exception as e:
            log.error(f"Error during multi-message summarization: {e}")
            
            # Show error in summary widget
            summary_widget = self.query_one("#summary-widget", SummaryWidget)
            summary_widget.set_summary(f"Error generating summary: {str(e)}")
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info(f"❌ Summarization error: {str(e)}")
    
    def show_filter(self) -> None:
        """Show the filter input"""
        filter_input = self.query_one("#filter-input", FilterInput)
        filter_input.show()
        self.filter_mode = True
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        debug_widget.update_debug_info("Filter mode: Type to filter, Enter to apply, Esc to cancel")
    
    def hide_filter(self) -> None:
        """Hide the filter input and clear filter"""
        filter_input = self.query_one("#filter-input", FilterInput)
        filter_input.hide()
        self.filter_mode = False
        
        # Clear filter and show all messages
        message_list = self.query_one("#message-list", MessageList)
        message_list.update_messages(MESSAGES)
        
        # Give focus back to the message list
        message_list.focus()
        
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        debug_widget.update_debug_info("Filter cleared")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle filter input submission"""
        if self.filter_mode:
            log.info(f"Input submitted with value: '{event.value}'")
            log.info(f"Input value type: {type(event.value)}")
            log.info(f"Input value length: {len(event.value) if event.value else 0}")
            
            filter_text = event.value.lower().strip()
            
            log.info(f"Filtering with text: '{filter_text}'")
            log.info(f"Total messages before filtering: {len(MESSAGES)}")
            
            if filter_text:
                # Filter messages
                filtered_messages = []
                for i, msg in enumerate(MESSAGES):
                    # Convert message to string and search entire content
                    msg_str = str(msg).lower()
                    if filter_text in msg_str:
                        filtered_messages.append(msg)
                        log.info(f"Found match in message: {msg['subject'][:50]}...")
                
                log.info(f"Found {len(filtered_messages)} matching messages")
                
                message_list = self.query_one("#message-list", MessageList)
                message_list.update_messages(filtered_messages)
                
                debug_widget = self.query_one("#debug-widget", DebugWidget)
                debug_widget.update_debug_info(f"Filtered to {len(filtered_messages)} messages for '{filter_text}'")
            else:
                # Empty filter, show all messages
                log.info("Filter text is empty, showing all messages")
                message_list = self.query_one("#message-list", MessageList)
                message_list.update_messages(MESSAGES)
                
                debug_widget = self.query_one("#debug-widget", DebugWidget)
                debug_widget.update_debug_info("Filter cleared")
            
            # Hide the filter input but don't clear the filter
            filter_input = self.query_one("#filter-input", FilterInput)
            filter_input.styles.display = "none"
            filter_input.blur()
            self.filter_mode = False
            
            # Give focus back to the message list
            message_list = self.query_one("#message-list", MessageList)
            message_list.focus()


    
    def on_key(self, event: Key) -> None:
        """Handle key events for debugging"""
        log.info(f"Key pressed: {event.key}")
        if event.key == "enter" and not self.filter_mode:
            log.info("Enter key detected - calling action_open_href")
            self.action_open_href()
        # Don't call super() since the parent doesn't have on_key

if __name__ == "__main__":
    # Run with debug mode enabled
    # You can also run with: python app.py --dev
    EmailApp().run()
