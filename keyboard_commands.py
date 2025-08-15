from textual.widgets import Static


class KeyboardCommands(Static):
    """A widget to display available keyboard commands"""
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.update_commands()
    
    def update_commands(self) -> None:
        """Update the display with available keyboard commands"""
        commands = [
            "[bold cyan]Keyboard Commands:[/bold cyan]",
            "[yellow]q[/yellow] - Quit the application",
            "[yellow]/[/yellow] - Open filter mode",
            "[yellow]ESC[/yellow] - Cancel filter mode",
            "[yellow]↑/↓[/yellow] - Navigate message list",
            "[yellow]Enter[/yellow] - Open message in browser",
            "[yellow]s[/yellow] - Summarize message with AI",
            "[yellow]d[/yellow] - Toggle debug window",
            "[yellow]t[/yellow] - Test Gemini connection",
            # "[yellow]Tab[/yellow] - Switch between panels"
        ]
        
        content = " | ".join(commands)
        self.update(content) 