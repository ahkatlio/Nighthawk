from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Label, RadioButton, RadioSet, Switch, Select
from textual.reactive import reactive
from textual_slider import Slider

class SettingsTab(Container):
    current_theme = reactive("tokyo-night")
    tts_enabled = reactive(False)
    selected_voice = reactive("en-US-AriaNeural")
    speech_rate = reactive(0)
    
    def on_mount(self) -> None:
        assistant = getattr(self.app, 'assistant', None)
        if assistant:
            radio_set = self.query_one("#model-select")
            if assistant.current_model == "gemini":
                self.query_one("#model-pro").value = True
            elif assistant.current_model == "ollama":
                self.query_one("#model-ollama").value = True
        
        try:
            from tui.tts_service import get_tts_service
            tts = get_tts_service()
            self.query_one("#tts-switch", Switch).value = tts.is_enabled()
            
            if not tts.is_available():
                status_label = self.query_one("#tts-status", Label)
                status_label.update("Status: ⚠️ Not Installed")
        except Exception as e:
            pass
        
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="settings-scroll"):
            yield Label("🔧 Nighthawk Configuration", classes="page-title")
            
            with Container(classes="settings-group"):
                yield Label("🧠 AI Model Selection", classes="group-title")
                yield Label("Choose your preferred AI model:", classes="setting-label")
                with RadioSet(id="model-select"):
                    yield RadioButton("Gemini 2.5 Pro (Recommended)", value=True, id="model-pro")
                    yield RadioButton("Gemini 2.5 Flash (Faster, Lower Cost)", id="model-flash")
                    yield RadioButton("Ollama (Local/Offline)", id="model-ollama")
            
            with Container(classes="settings-group"):
                yield Label("🔊 Text-to-Speech", classes="group-title")
                yield Label("Enable voice output for AI responses:", classes="setting-label")
                yield Switch(value=False, id="tts-switch", animate=True)
                yield Label("Status: OFF", id="tts-status", classes="setting-label")
                yield Label("")
                yield Label("Voice Model:", classes="setting-label")
                yield Select(
                    [
                        ("English (US) - Aria [Female]", "en-US-AriaNeural"),
                        ("English (US) - Guy [Male]", "en-US-GuyNeural"),
                        ("English (UK) - Sonia [Female]", "en-GB-SoniaNeural"),
                        ("English (UK) - Ryan [Male]", "en-GB-RyanNeural"),
                        ("English (AU) - Natasha [Female]", "en-AU-NatashaNeural"),
                        ("English (AU) - William [Male]", "en-AU-WilliamNeural"),
                        ("English (CA) - Clara [Female]", "en-CA-ClaraNeural"),
                        ("English (CA) - Liam [Male]", "en-CA-LiamNeural"),
                    ],
                    value="en-US-AriaNeural",
                    id="voice-select",
                    allow_blank=False
                )
                yield Label("")
                yield Label("Speech Speed:", classes="setting-label")
                yield Slider(min=-50, max=50, step=5, value=0, id="speech-rate-slider")
                yield Label("Speed: Normal (0%)", id="speed-label", classes="setting-label")
                yield Label("")
                yield Label("💡 Voice speaks only AI responses in chat panel", classes="setting-label")
            
            yield Label("")
            yield Label("💡 Tip: Change themes with Ctrl+P", classes="setting-label")
    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "voice-select":
            try:
                from tui.tts_service import get_tts_service
                tts = get_tts_service()
                
                new_voice = event.value
                self.selected_voice = new_voice
                tts.set_voice_model(new_voice)
                
                self.notify(f"🎤 Voice model changed", severity="information")
            except Exception as e:
                self.notify(f"⚠️ Voice change failed: {e}", severity="error")
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "tts-switch":
            try:
                from tui.tts_service import get_tts_service
                tts = get_tts_service()
                
                if not tts.is_available():
                    self.notify("⚠️ TTS not available. Run: pip install edge-tts", severity="warning")
                    event.switch.value = False
                    return
                
                tts.set_enabled(event.value)
                self.tts_enabled = event.value
                
                status_label = self.query_one("#tts-status", Label)
                if event.value:
                    status_label.update("Status: 🔊 ON")
                    self.notify("🔊 Text-to-Speech enabled", severity="information")
                else:
                    status_label.update("Status: 🔇 OFF")
                    self.notify("🔇 Text-to-Speech disabled", severity="information")
            
            except Exception as e:
                self.notify(f"⚠️ TTS error: {e}", severity="error")
                event.switch.value = False
    
    def on_slider_changed(self, event: Slider.Changed) -> None:
        if event.slider.id == "speech-rate-slider":
            try:
                from tui.tts_service import get_tts_service
                tts = get_tts_service()
                
                rate = int(event.value)
                self.speech_rate = rate
                tts.set_speech_rate(rate)
                
                speed_label = self.query_one("#speed-label", Label)
                if rate == 0:
                    speed_label.update("Speed: Normal (0%)")
                elif rate > 0:
                    speed_label.update(f"Speed: Faster (+{rate}%)")
                else:
                    speed_label.update(f"Speed: Slower ({rate}%)")
            
            except Exception as e:
                pass
    
    def on_radio_set_changed(self, event) -> None:
        if event.radio_set.id == "model-select":
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
                
                try:
                    chat_area = self.app.query_one("#chat-content")
                    model_indicator = chat_area.query_one("#model-indicator", Label)
                    model_name = "GEMINI" if assistant.current_model == "gemini" else "OLLAMA"
                    model_indicator.update(f"🤖 Model: {model_name}")
                except:
                    pass
            else:
                self.notify("⚠️ Assistant not initialized", severity="warning")
