from textual.widgets import Static

class DebugWidget(Static):
    """A widget to display debug information on screen"""
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.styles.display = "none"
    
    def update_debug_info(self, info: str) -> None:
        self.update(f"[red]DEBUG:[/red] {info}") 