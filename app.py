from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static
from textual.reactive import reactive
from textual import log
from textual import on
from textual.events import Key
from message_list import MessageList, MessageSelected, load_messages_from_json
from message_viewer import MessageViewer

# Load messages from JSON file
MESSAGES = load_messages_from_json("top_posters_output.json")

class DebugWidget(Static):
    """A widget to display debug information on screen"""
    
    def update_debug_info(self, info: str) -> None:
        self.update(f"[red]DEBUG:[/red] {info}")



class EmailApp(App):
    CSS_PATH = "style.css"

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            yield MessageList(MESSAGES, id="message-list")
            yield MessageViewer(id="message-viewer")
            yield DebugWidget(id="debug-widget")

    def on_message_selected(self, event: MessageSelected) -> None:
        log.info(f"on_message_selected called with item: {event.item}")
        viewer = self.query_one("#message-viewer", MessageViewer)
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        log.info(f"Found viewer: {viewer}")
        viewer.set_message(event.item)
        debug_widget.update_debug_info(f"Selected: {event.item['subject'][:50]}...")
        log.info("Set viewer content")

    def on_key(self, event: Key) -> None:
        """Handle key events"""
        if event.key == "q":
            self.exit()

    def on_mount(self) -> None:
        """Called when the app is mounted - select the first message if available"""
        if MESSAGES:
            # Get the message list widget
            message_list = self.query_one("#message-list", MessageList)
            # Select the first item (index 0)
            message_list.index = 0
            # Trigger the selection event manually
            self.on_message_selected(MessageSelected(MESSAGES[0]))

if __name__ == "__main__":
    # Run with debug mode enabled
    # You can also run with: python app.py --dev
    EmailApp().run()