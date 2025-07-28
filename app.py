from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import ListView, ListItem, Static
from textual.reactive import reactive
from textual.message import Message
from textual import log
from textual import on
from textual.events import Key
import json
from datetime import datetime, timezone
import re

def calculate_age(post_time_str: str) -> str:
    """Calculate the age of a message from its post time string"""
    try:
        # Parse the ISO format time string
        post_time = datetime.fromisoformat(post_time_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        # Calculate the difference (use abs to handle future dates)
        diff = abs(now - post_time)
        
        # Convert to total seconds
        total_seconds = diff.total_seconds()
        
        # If the post time is in the future, show "in X time"
        if now < post_time:
            if total_seconds < 60:
                return f"in {int(total_seconds)}s"
            elif total_seconds < 3600:
                minutes = int(total_seconds // 60)
                return f"in {minutes}m"
            elif total_seconds < 86400:
                hours = int(total_seconds // 3600)
                return f"in {hours}h"
            elif total_seconds < 2592000:  # 30 days
                days = int(total_seconds // 86400)
                return f"in {days}d"
            else:
                months = int(total_seconds // 2592000)
                return f"in {months}mo"
        else:
            # Past dates
            if total_seconds < 60:
                return f"{int(total_seconds)}s ago"
            elif total_seconds < 3600:
                minutes = int(total_seconds // 60)
                return f"{minutes}m ago"
            elif total_seconds < 86400:
                hours = int(total_seconds // 3600)
                return f"{hours}h ago"
            elif total_seconds < 2592000:  # 30 days
                days = int(total_seconds // 86400)
                return f"{days}d ago"
            else:
                months = int(total_seconds // 2592000)
                return f"{months}mo ago"
    except Exception as e:
        return "unknown"

# MESSAGES = [
#     {"subject": "Welcome to the forum", "body": "Thanks for joining! We're glad to have you."},
#     {"subject": "Textual UI Tips", "body": "Explore styling, reactive state, and message handling."},
#     {"subject": "Next Meeting", "body": "Don't forget the team sync on Friday at 10am."},
# ]

MESSAGES = [
    {
        "subject": msg["node"]["subject"],
        "body": msg["node"]["body"],
        "id": msg["node"]["id"],
        "postTime": msg["node"]["postTime"],
        "viewHref": msg["node"]["viewHref"],
        "author": msg["node"]["author"],
        "age": calculate_age(msg["node"]["postTime"])
    }
    for msg in json.load(open("top_posters_output.json"))["data"]["messages"]["edges"]
]


class MessageSelected(Message):
    def __init__(self, item: dict) -> None:
        self.item = item
        super().__init__()

class MessageItem(Static):
    """Custom widget to display message subject and age"""
    
    def __init__(self, subject: str, age: str) -> None:
        self.subject = subject
        self.age = age
        super().__init__()
    
    def render(self) -> str:
        # Calculate available width and format the display
        width = self.size.width if self.size else 80
        age_width = len(self.age) + 2  # +2 for parentheses
        subject_width = width - age_width - 1  # -1 for space
        
        # Truncate subject if needed
        display_subject = self.subject[:subject_width-3] + "..." if len(self.subject) > subject_width else self.subject
        display_subject = display_subject.ljust(subject_width)
        
        return f"{display_subject} ({self.age})"

class MessageList(ListView):
    def compose(self) -> ComposeResult:
        for msg in MESSAGES:
            yield ListItem(MessageItem(msg["subject"], msg["age"]))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        log.info(f"Message highlighted at index {event.list_view.index}")
        selected_message = MESSAGES[event.list_view.index]
        log.info(f"Highlighted message: {selected_message}")
        self.post_message(MessageSelected(selected_message))

class DebugWidget(Static):
    """A widget to display debug information on screen"""
    
    def update_debug_info(self, info: str) -> None:
        self.update(f"[red]DEBUG:[/red] {info}")

class MessageViewer(Static):
    content = reactive(None)
    
    def watch_content(self, value: dict) -> None:
        log.info(f"watch_content called with value: {value}")
        
        # Check if we have valid message data
        if not value or not isinstance(value, dict) or "body" not in value:
            log.info("No valid message data, skipping update")
            return
            
        # Format all message data fields
        message_data = value
        
        # Convert HTML body to Markdown for better terminal display
        from html2text import HTML2Text
        h = HTML2Text()
        h.ignore_links = False
        h.body_width = 0  # Disable line wrapping
        markdown_body = h.handle(message_data["body"])
        
        # Create formatted display of all fields
        formatted_content = f"""
[bold blue]Message Details[/bold blue]

[bold]ID:[/bold] {message_data["id"]}
[bold]Subject:[/bold] {message_data["subject"]}
[bold]Post Time:[/bold] {message_data["postTime"]}
[bold]View URL:[/bold] {message_data["viewHref"]}

[bold]Author:[/bold]
  Title: {message_data["author"]["title"] or "N/A"}
  First Name: {message_data["author"]["firstName"] or "N/A"}
  Last Name: {message_data["author"]["lastName"] or "N/A"}

[bold blue]Message Body:[/bold blue]
{markdown_body}
"""
        
        log.info(f"Formatted content length: {len(formatted_content)}")
        # Update with formatted content
        self.update(formatted_content)

class EmailApp(App):
    CSS_PATH = "style.css"

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            yield MessageList(id="message-list")
            yield MessageViewer(id="message-viewer")
            yield DebugWidget(id="debug-widget")

    def on_message_selected(self, event: MessageSelected) -> None:
        log.info(f"on_message_selected called with item: {event.item}")
        viewer = self.query_one("#message-viewer", MessageViewer)
        debug_widget = self.query_one("#debug-widget", DebugWidget)
        log.info(f"Found viewer: {viewer}")
        viewer.content = event.item
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