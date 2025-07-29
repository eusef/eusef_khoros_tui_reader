from textual.widgets import ListView, ListItem, Static
from textual.message import Message
from textual import log
from datetime import datetime, timezone
import json


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


def load_messages_from_json(json_file_path: str = "top_posters_output.json") -> list:
    """Load and process messages from a JSON file"""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        messages = [
            {
                "subject": msg["node"]["subject"],
                "body": msg["node"]["body"],
                "id": msg["node"]["id"],
                "postTime": msg["node"]["postTime"],
                "viewHref": msg["node"]["viewHref"],
                "author": msg["node"]["author"],
                "age": calculate_age(msg["node"]["postTime"])
            }
            for msg in data["data"]["messages"]["edges"]
        ]
        return messages
    except Exception as e:
        log.error(f"Error loading messages from {json_file_path}: {e}")
        return []


class MessageSelected(Message):
    """Message sent when a message item is selected"""
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
    """A reusable list view widget for displaying messages"""
    
    def __init__(self, messages: list = None, **kwargs) -> None:
        self.messages = messages or []
        super().__init__(**kwargs)
    
    def compose(self):
        for msg in self.messages:
            yield ListItem(MessageItem(msg["subject"], msg["age"]))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        log.info(f"Message highlighted at index {event.list_view.index}")
        if (event.list_view.index is not None and 
            0 <= event.list_view.index < len(self.messages)):
            selected_message = self.messages[event.list_view.index]
            log.info(f"Highlighted message: {selected_message}")
            self.post_message(MessageSelected(selected_message))
    
    def update_messages(self, messages: list) -> None:
        """Update the messages displayed in the list"""
        log.info(f"Updating message list with {len(messages)} messages")
        self.messages = messages
        self.clear()
        for msg in self.messages:
            self.append(ListItem(MessageItem(msg["subject"], msg["age"])))
        log.info(f"Message list updated, now has {len(self.messages)} items")
    
    def load_messages_from_file(self, json_file_path: str) -> None:
        """Load messages from a JSON file and update the list"""
        messages = load_messages_from_json(json_file_path)
        self.update_messages(messages) 