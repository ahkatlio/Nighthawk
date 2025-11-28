from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, Tabs
from textual.containers import Container
from textual import events
from textual.binding import Binding

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
    BINDINGS = [
        Binding("ctrl+1", "switch_tab_1", "Chat", priority=True),
        Binding("ctrl+2", "switch_tab_2", "Settings", priority=True),
        Binding("ctrl+w", "stop_audio", "Stop Audio", priority=True),
    ]
    
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
    
    def action_switch_tab_1(self) -> None:
        """Switch to Chat tab"""
        tabs = self.query_one(Tabs)
        tabs.active = "tab-1"
    
    def action_switch_tab_2(self) -> None:
        """Switch to Settings tab"""
        tabs = self.query_one(Tabs)
        tabs.active = "tab-2"
    
    def action_stop_audio(self) -> None:
        """Stop any playing TTS audio."""
        try:
            from tui.tts_service import get_tts_service
            tts = get_tts_service()
            if tts.is_speaking:
                tts.stop_speech()
                self.notify("🔇 Audio stopped", severity="information", timeout=2)
            else:
                self.notify("ℹ️ No audio playing", severity="information", timeout=2)
        except Exception as e:
            self.notify(f"⚠️ Could not stop audio: {e}", severity="warning", timeout=2)

if __name__ == "__main__":
    app = NighthawkTUI()
    app.run()
