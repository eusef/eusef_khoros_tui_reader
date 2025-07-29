#!/usr/bin/env python3
"""
Example usage of the refactored MessageList component.

This demonstrates how the MessageList can be reused in different applications.
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static
from message_list import MessageList, MessageSelected, load_messages_from_json
from message_viewer import MessageViewer





class ExampleApp(App):
    """Example application demonstrating MessageList reuse"""
    
    def compose(self) -> ComposeResult:
        with Container():
            yield MessageList(id="message-list")
            yield MessageViewer(id="message-viewer")
    
    def on_mount(self) -> None:
        """Load messages when the app starts"""
        message_list = self.query_one("#message-list", MessageList)
        
        # Option 1: Load from file
        message_list.load_messages_from_file("top_posters_output.json")
        
        # Option 2: Update with custom messages
        # custom_messages = [
        #     {"subject": "Test Message 1", "age": "2h ago", "id": "123"},
        #     {"subject": "Test Message 2", "age": "1d ago", "id": "456"},
        # ]
        # message_list.update_messages(custom_messages)
        
        # Select first message if available
        if message_list.messages:
            message_list.index = 0


if __name__ == "__main__":
    ExampleApp().run() 