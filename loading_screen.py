from textual.widgets import Static
from textual.timer import Timer

class LoadingScreen(Static):
    """A cool loading screen widget"""
    
    def __init__(self, **kwargs) -> None:
        super().__init__("⠋ Loading Khoros TUI Reader...", **kwargs)
        self.styles.display = "block"
        self.loading_frames = [
            "⠋ Loading Khoros TUI Reader...",
            "⠙ Loading Khoros TUI Reader...",
            "⠹ Loading Khoros TUI Reader...",
            "⠸ Loading Khoros TUI Reader...",
            "⠼ Loading Khoros TUI Reader...",
            "⠴ Loading Khoros TUI Reader...",
            "⠦ Loading Khoros TUI Reader...",
            "⠧ Loading Khoros TUI Reader...",
            "⠇ Loading Khoros TUI Reader...",
            "⠏ Loading Khoros TUI Reader..."
        ]
        self.current_frame = 0
        self.animation_timer: Timer | None = None
    
    def on_mount(self) -> None:
        """Start the loading animation"""
        self.animation_timer = self.set_interval(0.1, self.animate_loading)
    
    def animate_loading(self) -> None:
        """Animate the loading spinner"""
        self.current_frame = (self.current_frame + 1) % len(self.loading_frames)
        self.update(self.loading_frames[self.current_frame])
    
    def hide(self) -> None:
        """Hide the loading screen"""
        self.styles.display = "none"
        if self.animation_timer:
            self.animation_timer.stop() 