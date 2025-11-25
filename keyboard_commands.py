from textual.widgets import Static


class KeyboardCommands(Static):
    """A widget to display available keyboard commands"""
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.commands = [
            "[bold cyan]Keyboard Commands:[/bold cyan]",
            "[yellow]q[/yellow] - Quit the application",
            "[yellow]/[/yellow] - Open filter mode", 
            "[yellow]ESC[/yellow] - Cancel filter mode / Dismiss summary",
            "[yellow]↑/↓[/yellow] - Navigate message list",
            "[yellow]Enter[/yellow] - Open message in browser",
            "[yellow]s[/yellow] - Summarize message with AI",
            "[yellow]Shift+S[/yellow] - Summarize all visible messages",
            "[yellow]d[/yellow] - Toggle debug window",
            "[yellow]t[/yellow] - Test Gemini connection",
            # "[yellow]Tab[/yellow] - Switch between panels"
        ]
        self.update_commands()
    
    def update_commands(self) -> None:
        """Update the display with available keyboard commands, wrapping based on width"""
        if not self.size or self.size.width <= 0:
            # If size not available yet, use simple format
            content = " | ".join(self.commands)
            self.update(content)
            return
            
        # Use more of the available width - account for border (2 chars) and padding (2 chars)
        width = self.size.width - 4
        lines = []
        current_line = ""
        current_line_display = ""
        
        for i, command in enumerate(self.commands):
            # Calculate the display length (without markup)
            # This is approximate since markup doesn't count toward display width
            display_command = command.replace("[bold cyan]", "").replace("[/bold cyan]", "")
            display_command = display_command.replace("[yellow]", "").replace("[/yellow]", "")
            
            separator = " | " if i > 0 and current_line else ""
            separator_display = " | " if i > 0 and current_line_display else ""
            
            test_line_display = current_line_display + separator_display + display_command
            
            # If adding this command would exceed width, start a new line
            if len(test_line_display) > width and current_line:
                lines.append(current_line)
                current_line = command
                current_line_display = display_command
            else:
                if i == 0:
                    current_line = command
                    current_line_display = display_command
                else:
                    current_line = current_line + separator + command
                    current_line_display = current_line_display + separator_display + display_command
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        content = "\n".join(lines)
        self.update(content)
    
    def on_resize(self) -> None:
        """Handle widget resize by updating command layout"""
        self.update_commands() 