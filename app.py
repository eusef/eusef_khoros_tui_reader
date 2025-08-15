import subprocess
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Input
from textual.reactive import reactive
from textual import log
from textual import on
from textual.events import Key
from textual.binding import Binding
from textual.widget import Widget
from textual.timer import Timer
from message_list import MessageList, MessageSelected, load_messages_from_json
from message_viewer import MessageViewer
from keyboard_commands import KeyboardCommands
from loading_screen import LoadingScreen
from debug_widget import DebugWidget
from gemini_summarizer import GeminiSummarizer
from summary_widget import SummaryWidget

# Load messages from JSON file
MESSAGES = load_messages_from_json("top_posters_output.json")

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
        Binding("escape", "cancel_filter", "Cancel Filter", show=False),
        Binding("enter", "open_href", "Open in Browser"),
        Binding("d", "toggle_debug", "Toggle Debug", show=False),
        Binding("s", "summarize", "Summarize Message"),
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
    
    async def load_messages_async(self) -> None:
        """Load messages asynchronously and transition to main interface when complete"""
        try:
            # Check if the JSON file exists and has content
            import os
            json_file = "top_posters_output.json"
            
            # Update loading message to show we're checking the file
            loading_screen = self.query_one("#loading-screen", LoadingScreen)
            loading_screen.update("⠋ Checking message data...")
            
            if not os.path.exists(json_file):
                self.handle_loading_error(f"JSON file '{json_file}' not found")
                return
            
            # Check file size to ensure it has content
            file_size = os.path.getsize(json_file)
            if file_size == 0:
                self.handle_loading_error(f"JSON file '{json_file}' is empty")
                return
            
            # Update loading message to show we're processing
            loading_screen.update("⠙ Processing messages...")
            
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
            # Get the message list widget
            message_list = self.query_one("#message-list", MessageList)
            # Select the first item (index 0)
            message_list.index = 0
            # Give focus to the message list
            message_list.focus()
            # The MessageSelected event will be handled automatically by the event handler
        
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
    
    def action_cancel_filter(self) -> None:
        """Action to hide filter input"""
        log.info("Cancel filter action triggered")
        if self.filter_mode:
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
                return
            
            # Show summary widget and start loading
            log.info("Showing summary widget")
            summary_widget.show_summary()
            summary_widget.set_loading(True)
            
            # Start async summarization
            self.call_after_refresh(self.summarize_message_async, selected_message)
            
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("Generating summary with Gemini...")
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
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info("Summary generated successfully")
            
            log.info("Message summarization completed")
            
        except Exception as e:
            log.error(f"Error during summarization: {e}")
            
            # Show error in summary widget
            summary_widget = self.query_one("#summary-widget", SummaryWidget)
            summary_widget.set_summary(f"Error generating summary: {str(e)}")
            
            # Update debug info
            debug_widget = self.query_one("#debug-widget", DebugWidget)
            debug_widget.update_debug_info(f"Summarization error: {str(e)}")
    
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