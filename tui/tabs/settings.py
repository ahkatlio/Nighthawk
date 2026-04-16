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
            dropdown = self.query_one("#model-dropdown", Select)
            default_value = "gemini-2.5-flash"
            if assistant.current_model == "gemini":
                # Check if assistant has a gemini chat instance and its model name
                model_name = getattr(assistant.gemini_chat.model, "model_name", "gemini-2.5-flash") if getattr(assistant, "gemini_chat", None) else "gemini-2.5-flash"
                default_value = model_name if model_name.startswith("gemini-") else "gemini-2.5-flash"
            elif assistant.current_model == "ollama":
                default_value = f"ollama-{assistant.model}"
            
            # If the option doesn't exist, we fall back to something default or let Select default out.
            try:
                dropdown.value = default_value
            except Exception:
                dropdown.value = "gemini-2.5-flash"
        
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
                
                # Load Ollama models safely
                ollama_options = []
                try:
                    import ollama
                    response = ollama.list()
                    # `ollama.list()` returns an object with a `models` attribute in newer versions
                    models = getattr(response, "models", [])
                    if not models and isinstance(response, dict):
                        models = response.get("models", [])
                        
                    for m in models:
                        if isinstance(m, dict):
                            name = m.get("name") or m.get("model", str(m))
                        else:
                            name = getattr(m, "model", getattr(m, "name", str(m)))
                        
                        if name:
                            ollama_options.append((f"Ollama - {name}", f"ollama-{name}"))
                except Exception:
                    pass
                
                yield Select(
                    [
                        ("Gemini 2.5 Pro (Recommended)", "gemini-2.5-pro"),
                        ("Gemini 2.5 Flash (Faster, Lower Cost)", "gemini-2.5-flash"),
                    ] + ollama_options,
                    value="gemini-2.5-flash",
                    id="model-dropdown",
                    allow_blank=False
                )
            
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
                
        elif event.select.id == "model-dropdown":
            selected = event.value
            assistant = getattr(self.app, 'assistant', None)
            
            if assistant:
                if selected.startswith("gemini-"):
                    if assistant.switch_model(selected):
                        self.notify(f"🧠 Switched to {selected}", severity="information")
                    else:
                        self.notify(f"⚠️ Failed to init {selected}", severity="warning")
                elif selected.startswith("ollama-"):
                    if assistant.switch_model(selected):
                        model_name = selected[7:]
                        self.notify(f"🧠 Switched to Ollama ({model_name})", severity="information")
                    else:
                        self.notify(f"⚠️ Failed to init {selected}", severity="warning")
                
                try:
                    chat_area = self.app.query_one("#chat-content")
                    model_indicator = chat_area.query_one("#model-indicator", Label)
                    model_name_disp = "GEMINI" if "gemini" in selected else "OLLAMA"
                    model_indicator.update(f"🤖 Model: {model_name_disp}")
                except:
                    pass
            else:
                self.notify("⚠️ Assistant not initialized", severity="warning")
    
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
    

