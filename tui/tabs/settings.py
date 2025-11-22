from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Label, RadioButton, RadioSet
from textual.reactive import reactive

class SettingsTab(Container):
    """Tab 2: Configuration settings with Tokyo Night default theme"""
    
    current_theme = reactive("tokyo-night")
    
    def on_mount(self) -> None:
        """Initialize settings with current assistant state"""
        assistant = getattr(self.app, 'assistant', None)
        if assistant:
            # Sync radio buttons with current model
            radio_set = self.query_one("#model-select")
            if assistant.current_model == "gemini":
                # Check if using pro or flash (default to pro)
                self.query_one("#model-pro").value = True
            elif assistant.current_model == "ollama":
                self.query_one("#model-ollama").value = True
    
    def compose(self) -> ComposeResult:
        """Compose the settings layout"""
        with VerticalScroll(id="settings-scroll"):
            yield Label("🔧 Nighthawk Configuration", classes="page-title")
            
            # AI Model Configuration
            with Container(classes="settings-group"):
                yield Label("🧠 AI Model Selection", classes="group-title")
                yield Label("Choose your preferred AI model:", classes="setting-label")
                with RadioSet(id="model-select"):
                    yield RadioButton("Gemini 2.5 Pro (Recommended)", value=True, id="model-pro")
                    yield RadioButton("Gemini 2.5 Flash (Faster, Lower Cost)", id="model-flash")
                    yield RadioButton("Ollama (Local/Offline)", id="model-ollama")
                
                yield Label("")
                yield Label("💡 Tip: Change themes with Ctrl+P", classes="setting-label")
    
    def on_radio_set_changed(self, event) -> None:
        """Handle AI model selection changes"""
        if event.radio_set.id == "model-select":
            # Get selected model
            selected = event.pressed.id
            assistant = getattr(self.app, 'assistant', None)
            
            if assistant:
                if "pro" in selected or "flash" in selected:
                    assistant.current_model = "gemini"
                    model_display = "Gemini 2.5 Pro" if "pro" in selected else "Gemini 2.5 Flash"
                    self.notify(f"🧠 Switched to {model_display}", severity="information")
                elif "ollama" in selected:
                    assistant.current_model = "ollama"
                    self.notify(f"🧠 Switched to Ollama (Local)", severity="information")
                
                # Update model indicator in chat tab
                try:
                    chat_area = self.app.query_one("#chat-content")
                    model_indicator = chat_area.query_one("#model-indicator", Label)
                    model_name = "GEMINI" if assistant.current_model == "gemini" else "OLLAMA"
                    model_indicator.update(f"🤖 Model: {model_name}")
                except:
                    pass  # Chat tab might not be mounted yet
            else:
                self.notify("⚠️ Assistant not initialized", severity="warning")
