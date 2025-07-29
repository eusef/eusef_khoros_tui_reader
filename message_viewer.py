from textual.widgets import Static
from textual.reactive import reactive
from textual import log
from html2text import HTML2Text


class MessageViewer(Static):
    """
    A reusable widget for displaying detailed message information.
    
    This widget displays message details including ID, subject, post time,
    view URL, author information, and the message body converted from HTML to markdown.
    """
    
    content = reactive(None)
    
    def watch_content(self, value: dict) -> None:
        """
        Watch for changes to the content reactive variable and update the display.
        
        Args:
            value: Dictionary containing message data with keys like 'id', 'subject', 
                   'body', 'postTime', 'viewHref', 'author'
        """
        log.info(f"watch_content called with value: {value}")
        
        # Check if we have valid message data
        if not value or not isinstance(value, dict) or "body" not in value:
            log.info("No valid message data, skipping update")
            return
            
        # Format all message data fields
        message_data = value
        
        # Convert HTML body to Markdown for better terminal display
        h = HTML2Text()
        h.ignore_links = False
        h.body_width = 0  # Disable line wrapping
        markdown_body = h.handle(message_data["body"])
        
        # Create formatted display of all fields
        formatted_content = self._format_message_content(message_data, markdown_body)
        
        log.info(f"Formatted content length: {len(formatted_content)}")
        # Update with formatted content
        self.update(formatted_content)
    
    def _format_message_content(self, message_data: dict, markdown_body: str) -> str:
        """
        Format message data into a readable display string.
        
        Args:
            message_data: Dictionary containing message information
            markdown_body: The message body converted to markdown
            
        Returns:
            Formatted string for display
        """
        return f"""
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
    
    def set_message(self, message_data: dict) -> None:
        """
        Set the message data to display.
        
        Args:
            message_data: Dictionary containing message information
        """
        self.content = message_data
    
    def clear_content(self) -> None:
        """Clear the current message content."""
        self.content = None
        self.update("") 