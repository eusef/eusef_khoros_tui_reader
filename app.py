import subprocess
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Input
from textual.reactive import reactive
from textual import log
from textual import on
from textual.events import Key
from textual.binding import Binding
from message_list import MessageList, MessageSelected, load_messages_from_json
from message_viewer import MessageViewer
from keyboard_commands import KeyboardCommands

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

class DebugWidget(Static):
    """A widget to display debug information on screen"""
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.styles.display = "none"
    
    def update_debug_info(self, info: str) -> None:
        self.update(f"[red]DEBUG:[/red] {info}")

class EmailApp(App):
    CSS_PATH = "style.css"
    
    # Track if we're in filter mode
    filter_mode = reactive(False)
    
    # Define key bindings
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "filter", "Filter"),
        Binding("escape", "cancel_filter", "Cancel Filter", show=False),
        Binding("enter", "open_href", "Open in Browser"),
        Binding("d", "toggle_debug", "Toggle Debug", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            yield MessageList(MESSAGES, id="message-list")
            yield MessageViewer(id="message-viewer")
            yield FilterInput(id="filter-input")
            yield KeyboardCommands(id="keyboard-commands")
            yield DebugWidget(id="debug-widget")

    def on_message_selected(self, event: MessageSelected) -> None:
        log.info(f"on_message_selected called with item: {event.item}")
        viewer = self.query_one("#message-viewer", MessageViewer)
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        log.info(f"Found viewer: {viewer}")
        viewer.set_message(event.item)
        debug_widget.update_debug_info(f"Selected: {event.item['subject'][:50]}...")
        log.info("Set viewer content")

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
            debug_widget.update_debug_info("Debug window shown")
        else:
            debug_widget.styles.display = "none"
            debug_widget.update_debug_info("Debug window hidden")
    
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

    def on_mount(self) -> None:
        """Called when the app is mounted - select the first message if available"""
        if MESSAGES:
            # Get the message list widget
            message_list = self.query_one("#message-list", MessageList)
            # Select the first item (index 0)
            message_list.index = 0
            # Give focus to the message list
            message_list.focus()
            # Trigger the selection event manually
            self.on_message_selected(MessageSelected(MESSAGES[0]))
    
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