from __future__ import annotations

import asyncio
import subprocess
from datetime import datetime
from typing import Dict
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Input, Label, Markdown as MarkdownWidget, ProgressBar, RichLog, Static, LoadingIndicator
from textual.reactive import reactive
from textual.screen import ModalScreen

try:
    from main import NighthawkAssistant
except ImportError:
    NighthawkAssistant = None

try:
    from tui.tts_service import get_tts_service
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    get_tts_service = None


class SudoPasswordScreen(ModalScreen):
    def __init__(self, command: str):
        super().__init__()
        self.command = command
        self.password = None
    
    def compose(self) -> ComposeResult:
        with Container(id="sudo-dialog"):
            yield Label("🔒 Sudo Password Required", id="sudo-title")
            yield Label(f"Command needs elevated privileges:", classes="sudo-label")
            yield Label(f"[dim]{self.command}[/dim]", classes="sudo-command")
            yield Label("Enter your password:", classes="sudo-label")
            yield Input(password=True, placeholder="Password", id="sudo-password-input")
            with Horizontal(classes="sudo-buttons"):
                yield Button("Cancel", variant="error", id="sudo-cancel")
                yield Button("Authenticate", variant="success", id="sudo-submit")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sudo-cancel":
            self.dismiss(None)
        elif event.button.id == "sudo-submit":
            password_input = self.query_one("#sudo-password-input", Input)
            self.password = password_input.value
            self.dismiss(self.password)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "sudo-password-input":
            self.password = event.value
            self.dismiss(self.password)


class ChatMessage(Container):
    def __init__(self, content: str, is_user: bool = True, timestamp: str = None):
        super().__init__()
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        # Set the CSS class based on message type
        self.add_class("user-message" if is_user else "ai-message")
    
    def compose(self) -> ComposeResult:
        role = "You" if self.is_user else "🦅 Nighthawk AI"
        
        yield Label(f"[{self.timestamp}] {role}", classes="message-header")
        if self.is_user:
            yield Label(self.content, classes="message-content")
        else:
            # AI messages support markdown
            yield MarkdownWidget(self.content, classes="message-content")


class ChatArea(Container):
    is_processing = reactive(False)
    current_mode = reactive("CHAT")  # CHAT, SCAN, or EXPLOIT
    
    async def _write_with_typing(self, log: RichLog, text: str, delay: float = 0.02) -> None:
        words = text.split(' ')
        line_buffer = []
        
        for word in words:
            line_buffer.append(word)
            await asyncio.sleep(delay)
        
        log.write(text)
    
    def on_mount(self) -> None:
        assistant = getattr(self.app, 'assistant', None)
        if assistant:
            model_display = "GEMINI" if assistant.current_model == "gemini" else "OLLAMA"
            self.query_one("#model-indicator", Label).update(f"🤖 Model: {model_display}")
        else:
            self.query_one("#model-indicator", Label).update("🤖 Model: Not initialized")
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="chat-split"):
            with Vertical(id="left-chat"):
                with Container(id="chat-header"):
                    yield Label("💬 AI Conversation", classes="section-title")
                    yield Button("Clear Chat", id="clear-chat-btn", variant="default", classes="small-btn")
                with VerticalScroll(id="chat-history"):
                    yield ChatMessage(
                        "**Welcome to Nighthawk!** 🦅\n\n"
                        "I'm your AI-powered pentesting assistant.\n\n"
                        "**Left Panel:** AI analysis and responses\n"
                        "**Right Panel:** Live subprocess output and tool execution\n\n"
                        "I can help you:\n"
                        "• 🔍 Scan networks with **nmap**\n"
                        "• 💥 Exploit vulnerabilities using **Metasploit**\n"
                        "• 🕷️ Analyze web applications with **sqlmap**\n\n"
                        "*Try: 'Scan 192.168.1.1' or 'Exploit vsftpd 2.3.4'*",
                        is_user=False
                    )
                
                yield ProgressBar(id="process-progress", total=100, show_eta=False, classes="hidden")
            
            with Vertical(id="right-logs"):
                with Container(id="log-header"):
                    yield Label("⚙️  Background Processes", classes="section-title")
                    with Horizontal(id="log-controls"):
                        yield Checkbox("Verbose", value=True, id="verbose-toggle")
                        yield Checkbox("Auto-scroll", value=True, id="autoscroll-toggle")
                        yield Button("Clear", id="clear-logs", variant="warning", classes="small-btn")
                
                process_log = RichLog(highlight=True, markup=True, id="process-log", wrap=True)
                process_log.can_focus = True  # Make it focusable and selectable
                yield process_log
                with Horizontal(id="status-bar"):
                    yield LoadingIndicator(id="loading-spinner", classes="hidden")
                    yield Label("🟢 Ready", id="status-indicator")
        
        with Container(id="input-container"):
            with Horizontal(id="model-status-bar"):
                yield Label("💬 Mode: CHAT", id="mode-indicator")
                yield Label("🤖 Model: Loading...", id="model-indicator")
            with Horizontal(id="input-area"):
                yield Input(
                    placeholder="Ask me anything... (e.g., 'Scan 192.168.1.1', 'Exploit vsftpd 2.3.4', or just chat)",
                    id="chat-input",
                    max_length=0  # No limit
                )
                yield Button("Send 🚀", variant="success", id="send-btn")
            yield Label("💡 Tip: Press Enter to send | I can chat, scan, or exploit - just ask naturally!", id="input-hint")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.send_message()
        elif event.button.id == "clear-logs":
            self.query_one("#process-log", RichLog).clear()
            self.notify("Process logs cleared")
        elif event.button.id == "clear-chat-btn":
            chat_history = self.query_one("#chat-history")
            # Remove all messages except welcome
            for msg in chat_history.query(ChatMessage):
                msg.remove()
            # Re-add welcome message
            chat_history.mount(ChatMessage(
                "**Chat cleared.** Ready for new conversation! 🔄",
                is_user=False
            ))
            self.notify("Chat history cleared")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            self.send_message()
    
    def send_message(self) -> None:
        input_widget = self.query_one("#chat-input", Input)
        message = input_widget.value.strip()
        
        if not message:
            return
        
        assistant = getattr(self.app, 'assistant', None)
        if assistant and hasattr(assistant, 'classify_intent'):
            self.current_mode = assistant.classify_intent(message)
        else:
            msg_lower = message.lower()
            if any(phrase in msg_lower for phrase in ['scan ', 'nmap ', 'enumerate ', 'do a scan', 'run scan', 'perform scan']):
                self.current_mode = "SCAN"
            elif any(phrase in msg_lower for phrase in ['exploit ', 'attack ', 'hack ', 'metasploit ', 'pwn ', 'do an exploit', 'run exploit']):
                self.current_mode = "EXPLOIT"
            else:
                self.current_mode = "CHAT"
        
        # Update mode indicator
        mode_indicator = self.query_one("#mode-indicator", Label)
        mode_icons = {"CHAT": "💬", "SCAN": "🔍", "EXPLOIT": "💥"}
        mode_colors = {"CHAT": "cyan", "SCAN": "yellow", "EXPLOIT": "red"}
        icon = mode_icons.get(self.current_mode, "💬")
        mode_indicator.update(f"{icon} Mode: {self.current_mode}")
        
        # Add user message to history
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(message, is_user=True))
        
        # Clear input
        input_widget.value = ""
        
        # Process message asynchronously
        self.process_ai_request(message)
    
    @work(exclusive=True)
    async def process_ai_request(self, message: str) -> None:
        process_log = self.query_one("#process-log", RichLog)
        chat_history = self.query_one("#chat-history")
        progress = self.query_one("#process-progress", ProgressBar)
        status = self.query_one("#status-indicator", Label)
        spinner = self.query_one("#loading-spinner", LoadingIndicator)
        
        progress.remove_class("hidden")
        progress.update(total=None)
        spinner.remove_class("hidden")
        status.update(f"Processing...")
        self.is_processing = True
        
        try:
            assistant = getattr(self.app, 'assistant', None)
            if not assistant:
                chat_history.mount(ChatMessage("**Error:** Assistant not initialized.", is_user=False))
                return
            
            if not assistant.mcp_client.session:
                process_log.write("[yellow]Connecting to MCP Server...[/yellow]\n")
                await assistant.mcp_client.connect()
                process_log.write("[green]✓ Connection established[/green]\n")
                
            process_log.write(f"[cyan]Processing with {assistant.current_model}...[/cyan]\n")
            
            def log_callback(msg):
                process_log.write(msg + "\n")
                process_log.scroll_end(animate=True)

            ai_response = await assistant.process_request(message, log_callback=log_callback)
            
            chat_history.mount(ChatMessage(ai_response, is_user=False))
            chat_history.scroll_end(animate=True)
                
            # If TTS is available, we speak it
            # Not fully supported dynamically here since TTS is complex without TUI context
                
        except Exception as e:
            process_log.write(f"[red]❌ Error:[/red] {str(e)}\n")
            chat_history.mount(ChatMessage(f"**Error:** `{e}`", is_user=False))
        finally:
            progress.add_class("hidden")
            spinner.add_class("hidden")
            status.update("🟢 Ready")
            self.is_processing = False

