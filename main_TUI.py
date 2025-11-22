from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, Tabs
from textual.containers import Container
from textual import events

# Import tab modules
from tui.tabs.chat import ChatArea
from tui.tabs.settings import SettingsTab

# Import backend
try:
    from main import NighthawkAssistant
except ImportError:
    print("Warning: Could not import NighthawkAssistant from main.py")
    class NighthawkAssistant:
        def __init__(self): pass

class NighthawkTUI(App):
    """Nighthawk Penetration Testing Assistant TUI"""
    
    CSS_PATH = "tui/styles/nighthawk.tcss"
    TITLE = "🦅 Nighthawk AI - Advanced Pentesting Assistant"
    
    TAB_NAMES = [
        "💬 Chat & Operations",
        "⚙️  Settings"
    ]
    
    def __init__(self):
        super().__init__()
        self.assistant = NighthawkAssistant()
        self.current_tab_index = 0
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Tabs(*self.TAB_NAMES, id="main-tabs")
        
        with Container(id="tab-content"):
            yield ChatArea(id="chat-content")
            yield SettingsTab(id="settings-content").add_class("hidden")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app on mount."""
        # Set Tokyo Night theme
        self.theme = "tokyo-night"
        # Focus the tabs
        self.query_one(Tabs).focus()
    
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle tab switching."""
        # Hide all content containers
        self.query_one("#chat-content").add_class("hidden")
        self.query_one("#settings-content").add_class("hidden")
        
        # Show selected tab content
        tab_id = event.tab.id if event.tab else None
        if tab_id == "tab-1":  # Chat
            self.query_one("#chat-content").remove_class("hidden")
            self.current_tab_index = 0
        elif tab_id == "tab-2":  # Settings
            self.query_one("#settings-content").remove_class("hidden")
            self.current_tab_index = 1
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts for tab switching."""
        tabs = self.query_one(Tabs)
        
        # Ctrl+1 for Chat tab
        if event.key == "ctrl+1":
            tabs.active = "tab-1"
            event.prevent_default()
        # Ctrl+2 for Settings tab
        elif event.key == "ctrl+2":
            tabs.active = "tab-2"
            event.prevent_default()

if __name__ == "__main__":
    app = NighthawkTUI()
    app.run()
