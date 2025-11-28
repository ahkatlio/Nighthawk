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
    """Modal screen for sudo password input"""
    
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
    """A single chat message widget"""
    
    def __init__(self, content: str, is_user: bool = True, timestamp: str = None):
        super().__init__()
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        # Set the CSS class based on message type
        self.add_class("user-message" if is_user else "ai-message")
    
    def compose(self) -> ComposeResult:
        """Compose the message layout"""
        role = "You" if self.is_user else "🦅 Nighthawk AI"
        
        yield Label(f"[{self.timestamp}] {role}", classes="message-header")
        if self.is_user:
            yield Label(self.content, classes="message-content")
        else:
            # AI messages support markdown
            yield MarkdownWidget(self.content, classes="message-content")


class ChatArea(Container):
    """Tab 1: Main chat interface with split layout - 70/30 horizontal split"""
    
    is_processing = reactive(False)
    current_mode = reactive("CHAT")  # CHAT, SCAN, or EXPLOIT
    
    async def _write_with_typing(self, log: RichLog, text: str, delay: float = 0.02) -> None:
        """Write text to log with typing animation effect"""
        # Simply add a small delay before writing to simulate typing
        # RichLog doesn't support character-by-character, so we do word-by-word
        words = text.split(' ')
        line_buffer = []
        
        for word in words:
            line_buffer.append(word)
            await asyncio.sleep(delay)
        
        # Write the complete line at once
        log.write(text)
    
    def on_mount(self) -> None:
        """Initialize chat area and sync model indicator"""
        assistant = getattr(self.app, 'assistant', None)
        if assistant:
            model_display = "GEMINI" if assistant.current_model == "gemini" else "OLLAMA"
            self.query_one("#model-indicator", Label).update(f"🤖 Model: {model_display}")
        else:
            self.query_one("#model-indicator", Label).update("🤖 Model: Not initialized")
    
    def compose(self) -> ComposeResult:
        """Compose the chat area layout"""
        with Horizontal(id="chat-split"):
            # Left: Chat history (70% width)
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
            
            # Right: Process logs (30% width)
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
        
        # Bottom: Input area with mode indicator
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
        """Handle button presses"""
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
        """Handle Enter key in input"""
        if event.input.id == "chat-input":
            self.send_message()
    
    def send_message(self) -> None:
        """Send a chat message"""
        input_widget = self.query_one("#chat-input", Input)
        message = input_widget.value.strip()
        
        if not message:
            return
        
        # Detect mode using assistant's classify_intent
        assistant = getattr(self.app, 'assistant', None)
        if assistant and hasattr(assistant, 'classify_intent'):
            self.current_mode = assistant.classify_intent(message)
        else:
            # Fallback mode detection - only trigger tools with explicit commands
            msg_lower = message.lower()
            # Only trigger SCAN if user explicitly asks to scan a target
            if any(phrase in msg_lower for phrase in ['scan ', 'nmap ', 'enumerate ', 'do a scan', 'run scan', 'perform scan']):
                self.current_mode = "SCAN"
            # Only trigger EXPLOIT if user explicitly asks to exploit a target
            elif any(phrase in msg_lower for phrase in ['exploit ', 'attack ', 'hack ', 'metasploit ', 'pwn ', 'do an exploit', 'run exploit']):
                self.current_mode = "EXPLOIT"
            else:
                # Default to CHAT for questions and general conversation
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
        """Process AI request using REAL tools and AI analysis from main.py"""
        process_log = self.query_one("#process-log", RichLog)
        chat_history = self.query_one("#chat-history")
        progress = self.query_one("#process-progress", ProgressBar)
        status = self.query_one("#status-indicator", Label)
        spinner = self.query_one("#loading-spinner", LoadingIndicator)
        verbose = self.query_one("#verbose-toggle", Checkbox).value
        autoscroll = self.query_one("#autoscroll-toggle", Checkbox).value
        
        # Show progress and update status with spinner
        progress.remove_class("hidden")
        progress.update(total=None)  # Indeterminate
        spinner.remove_class("hidden")
        status.update(f"Processing ({self.current_mode})...")
        self.is_processing = True
        
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            await self._write_with_typing(process_log, f"[cyan][{timestamp}] 📨 Processing {self.current_mode} request: {message}[/cyan]\n")
            
            # Get assistant from app
            assistant = getattr(self.app, 'assistant', None)
            
            if not assistant:
                chat_history.mount(ChatMessage(
                    "**Error:** Assistant not initialized. Please restart the TUI.",
                    is_user=False
                ))
                status.update("🔴 Error")
                return
            
            # Update model indicator
            model_name = "GEMINI" if assistant.current_model == "gemini" else "OLLAMA"
            model_indicator = self.query_one("#model-indicator", Label)
            model_indicator.update(f"🤖 Model: {model_name}")
            
            if verbose:
                await self._write_with_typing(process_log, f"[yellow]⚡ Using {model_name} model...[/yellow]\n")
            
            # Run in thread to avoid blocking
            if self.current_mode == "CHAT":
                # Casual conversation
                ai_response = await asyncio.to_thread(
                    assistant.ask_ai,
                    message,
                    is_casual=True
                )
                await self._write_with_typing(process_log, "[green]✅ Response generated[/green]\n")
                
                # Display AI response first
                chat_history.mount(ChatMessage(ai_response, is_user=False))
                
                # Scroll to show new message
                if autoscroll:
                    chat_history.scroll_end(animate=True)
                
                # Then speak it (if TTS is enabled)
                if TTS_AVAILABLE:
                    try:
                        tts = get_tts_service()
                        if tts.is_enabled():
                            # Speak the AI response in background (non-blocking)
                            tts.speak_text(ai_response, blocking=False)
                    except Exception as e:
                        # Fail silently - TTS is optional
                        pass
                
            elif self.current_mode in ["SCAN", "EXPLOIT"]:
                # Tool execution mode
                await self._write_with_typing(process_log, f"[yellow]🔧 Detecting required tool...[/yellow]\n")
                
                # Get AI response to figure out what command to run
                ai_response = await asyncio.to_thread(
                    assistant.ask_ai,
                    message,
                    is_casual=False
                )
                
                # Detect which tool to use
                tool_name = assistant.detect_tool(message, ai_response)
                
                if not tool_name or tool_name not in assistant.tools:
                    # Fallback: detect from mode
                    if self.current_mode == "SCAN":
                        tool_name = "nmap"
                    elif self.current_mode == "EXPLOIT":
                        tool_name = "metasploit"
                
                if tool_name in assistant.tools:
                    tool = assistant.tools[tool_name]
                    await self._write_with_typing(process_log, f"[green]✓ Selected tool: {tool_name}[/green]\n")
                    
                    # Extract hostname if present
                    hostname = await asyncio.to_thread(assistant.extract_hostname, message)
                    if hostname:
                        await self._write_with_typing(process_log, f"[cyan]🎯 Target: {hostname}[/cyan]\n")
                    
                    # Generate command
                    await self._write_with_typing(process_log, f"[yellow]🔨 Generating {tool_name} command...[/yellow]\n")
                    
                    # For metasploit, prepare scan context if we have previous scan results
                    if tool_name == "metasploit":
                        scan_context = await asyncio.to_thread(
                            assistant.prepare_scan_context,
                            hostname or assistant.last_target
                        )
                        if scan_context:
                            await self._write_with_typing(process_log, f"[cyan]📊 Using scan results from previous nmap scan[/cyan]\n")
                        # Pass scan context to metasploit via the tool's attribute
                        tool._scan_context = scan_context
                        # Don't use progress callback to avoid execution issues
                        tool.set_progress_callback(None)
                    
                    command = await asyncio.to_thread(tool.generate_command, message, ai_response)
                    
                    if command:
                        # Handle both string and list commands (metasploit returns list)
                        if isinstance(command, list):
                            if not command:
                                process_log.write("[red]❌ No commands generated[/red]")
                                chat_history.mount(ChatMessage(
                                    f"I couldn't generate valid {tool_name} commands for that request.",
                                    is_user=False
                                ))
                                status.update("🟢 Ready")
                                return
                            
                            # For metasploit, execute commands via resource script
                            if tool_name == "metasploit":
                                process_log.write(f"[cyan]📝 Generated {len(command)} Metasploit commands[/cyan]")
                                for cmd in command[:5]:  # Show first 5
                                    process_log.write(f"[dim]  • {cmd}[/dim]")
                                if len(command) > 5:
                                    process_log.write(f"[dim]  ... and {len(command) - 5} more[/dim]")
                                
                                # Execute metasploit commands
                                process_log.write(f"[yellow]{'═' * 50}[/yellow]")
                                process_log.write(f"[yellow]🚀 Executing METASPLOIT...[/yellow]")
                                process_log.write(f"[yellow]{'═' * 50}[/yellow]")
                                
                                # Pass the list directly to execute
                                result = await asyncio.to_thread(tool.execute, command)
                            else:
                                # Other tools that might return lists - join them
                                command = ' && '.join(command)
                                await self._write_with_typing(process_log, f"[cyan]📝 Command: {command}[/cyan]\n")
                        else:
                            # String command (nmap, etc)
                            await self._write_with_typing(process_log, f"[cyan]📝 Command: {command}[/cyan]\n")
                        
                        # Check if sudo is required (only for string commands)
                        if isinstance(command, str) and command.strip().startswith('sudo '):
                            process_log.write(f"[yellow]🔐 Command requires sudo privileges[/yellow]")
                            password = await self.app.push_screen_wait(SudoPasswordScreen(command))
                            
                            if password is None:
                                process_log.write(f"[yellow]⚠️ Authentication cancelled[/yellow]")
                                chat_history.mount(ChatMessage(
                                    "Authentication cancelled. The command was not executed.",
                                    is_user=False
                                ))
                                status.update("🟢 Ready")
                                return
                            
                            process_log.write(f"[green]✓ Password received[/green]")
                            # Execute with sudo password
                            command_clean = command.replace('sudo ', '', 1)
                            result = await self._execute_with_sudo(command_clean, password, process_log)
                        elif isinstance(command, str):
                            # String command without sudo
                            process_log.write(f"[yellow]{'═' * 50}[/yellow]")
                            await self._write_with_typing(process_log, f"[yellow]🚀 Executing {tool_name.upper()}...[/yellow]\n")
                            process_log.write(f"[yellow]{'═' * 50}[/yellow]")
                            # Execute command in thread
                            result = await asyncio.to_thread(tool.execute, command)
                        # else: result was already set for list commands (metasploit)
                        
                        if result['success']:
                            # Store scan results
                            target = hostname if hostname else "unknown"
                            assistant.scan_results[target] = result['stdout']
                            assistant.last_target = target
                            
                            # Parse and store structured data
                            if tool_name == 'nmap' and hasattr(tool, 'parse_scan_data'):
                                parsed_data = tool.parse_scan_data(result['stdout'])
                                assistant.scan_results[f"{target}_parsed"] = parsed_data
                            
                            # Display stdout in right panel
                            for line in result['stdout'].split('\n'):
                                if line.strip():
                                    if 'open' in line.lower():
                                        process_log.write(f"[green]  ✓ {line}[/green]")
                                    elif 'error' in line.lower() or 'failed' in line.lower():
                                        process_log.write(f"[red]  ✗ {line}[/red]")
                                    else:
                                        process_log.write(f"[cyan]  {line}[/cyan]")
                            
                            process_log.write(f"[yellow]{'═' * 50}[/yellow]")
                            await self._write_with_typing(process_log, f"[green]✅ {tool_name.upper()} COMPLETED[/green]\n")
                            process_log.write(f"[yellow]{'═' * 50}[/yellow]")
                            
                            await self._write_with_typing(process_log, f"[yellow]🧠 Analyzing results with {model_name}...[/yellow]\n")
                            analysis = await asyncio.to_thread(
                                assistant.ask_ai,
                                message,
                                output_to_analyze=result['stdout']
                            )
                            
                            await self._write_with_typing(process_log, "[green]✅ Analysis complete[/green]\n")
                            
                            # Display analysis in left panel (chat)
                            chat_history.mount(ChatMessage(analysis, is_user=False))
                            
                            # Scroll to show new message
                            if autoscroll:
                                chat_history.scroll_end(animate=True)
                            
                            # Speak the analysis (if TTS is enabled)
                            if TTS_AVAILABLE:
                                try:
                                    tts = get_tts_service()
                                    if tts.is_enabled():
                                        # Speak the analysis in background
                                        await asyncio.to_thread(tts.speak_text, analysis, blocking=False)
                                except Exception as e:
                                    # Fail silently - TTS is optional
                                    pass
                        else:
                            # Show error
                            process_log.write(f"[red]❌ Error executing {tool_name}:[/red]")
                            for line in result['stderr'].split('\n'):
                                if line.strip():
                                    process_log.write(f"[red]  {line}[/red]")
                            
                            chat_history.mount(ChatMessage(
                                f"**Error executing {tool_name}:**\n```\n{result['stderr']}\n```",
                                is_user=False
                            ))
                    else:
                        process_log.write("[red]❌ Could not generate command[/red]")
                        chat_history.mount(ChatMessage(
                            f"I couldn't generate a {tool_name} command for that request. Can you be more specific?",
                            is_user=False
                        ))
                else:
                    # No tool available, just show AI response
                    process_log.write("[yellow]⚠️ No tool detected, showing AI response[/yellow]")
                    chat_history.mount(ChatMessage(ai_response, is_user=False))
                    
                    # Scroll to show new message
                    if autoscroll:
                        chat_history.scroll_end(animate=True)
                    
                    # Speak the response (if TTS is enabled)
                    if TTS_AVAILABLE:
                        try:
                            tts = get_tts_service()
                            if tts.is_enabled():
                                await asyncio.to_thread(tts.speak_text, ai_response, blocking=False)
                        except Exception as e:
                            pass
            
            # Auto-scroll if enabled (final check)
            if autoscroll:
                chat_history.scroll_end(animate=True)
            
            status.update("🟢 Ready")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            process_log.write(f"[red]❌ Error: {e}[/red]")
            process_log.write(f"[dim]{error_details}[/dim]")
            chat_history.mount(ChatMessage(
                f"**Error occurred:** `{str(e)}`\n\nCheck the process log for details.",
                is_user=False
            ))
            status.update("🔴 Error")
        finally:
            progress.add_class("hidden")
            spinner.add_class("hidden")
            progress.update(total=100, progress=100)
            self.is_processing = False
    
    async def _execute_with_sudo(self, command: str, password: str, process_log: RichLog) -> Dict[str, any]:
        """Execute command with sudo using provided password"""
        process_log.write(f"[yellow]{'═' * 50}[/yellow]")
        process_log.write(f"[yellow]🚀 Executing with SUDO...[/yellow]")
        process_log.write(f"[yellow]{'═' * 50}[/yellow]")
        
        def run_sudo():
            try:
                # Use sudo -S to read password from stdin
                process = subprocess.Popen(
                    ['sudo', '-S'] + command.split(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Send password
                stdout, stderr = process.communicate(input=password + '\n', timeout=300)
                
                return {
                    'success': process.returncode == 0,
                    'stdout': stdout,
                    'stderr': stderr,
                    'returncode': process.returncode
                }
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': 'Command timed out after 5 minutes',
                    'returncode': -1
                }
            except Exception as e:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': str(e),
                    'returncode': -1
                }
        
        return await asyncio.to_thread(run_sudo)


