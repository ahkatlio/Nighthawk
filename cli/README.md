# Nighthawk CLI Commands

## Overview
Nighthawk includes a built-in CLI command system for managing the assistant and viewing system information.

## Available Commands

### `help`
Shows all available CLI commands and usage information.

**Usage:**
```
help
help <command>
```

**Examples:**
- `help` - Show all commands
- `help status` - Show help for status command

---

### `status`
Display current system status including active model, cached scans, and tool availability.

**Usage:**
```
status
```

**Shows:**
- Active AI model (Ollama/Gemini)
- Available models
- Number of cached scans
- Conversation message count
- Last scanned target
- Tool installation status

---

### `tokens`
Show Gemini API token usage statistics and rate limits.

**Usage:**
```
tokens
```

**Shows:**
- Prompt tokens (current session)
- Completion tokens (current session)
- Total tokens used
- Free tier rate limits
- Daily request limits
- Context window size

**Note:** Token counts are estimates based on conversation history.

---

### `clear`
Clear cached data (conversation history and/or scan results).

**Usage:**
```
clear [history|scans|all]
```

**Examples:**
- `clear` - Clear everything (default: all)
- `clear history` - Clear only conversation history
- `clear scans` - Clear only scan results

---

### `tools`
Show available security tools and their installation status.

**Usage:**
```
tools
```

---

### `model`
Switch between AI models (Ollama/Gemini).

**Usage:**
```
model <name>
```

**Examples:**
- `model ollama` - Switch to Ollama
- `model gemini` - Switch to Google Gemini

---

## Regular Commands

These are built-in commands (not CLI commands):

- `quit` / `exit` / `q` - Exit Nighthawk
- `tools` - Show available security tools
- `model <name>` - Switch AI models

## Usage Tips

1. **Check system status before scanning:**
   ```
   status
   ```

2. **Monitor Gemini usage:**
   ```
   tokens
   ```

3. **Clear data between sessions:**
   ```
   clear all
   ```

4. **Get help on any command:**
   ```
   help <command>
   ```

## Architecture

```
cli/
├── __init__.py           - Module initialization
├── base_command.py       - Base class for all commands
├── command_manager.py    - Command routing and execution
├── help_command.py       - Help command implementation
├── status_command.py     - Status command implementation
├── token_command.py      - Token usage command
└── clear_command.py      - Clear data command
```

## Adding New Commands

To add a new CLI command:

1. Create a new file in `cli/` (e.g., `mycommand_command.py`)
2. Inherit from `BaseCommand`
3. Implement `execute()` method
4. Register in `CommandManager._register_commands()`

**Example:**
```python
from .base_command import BaseCommand

class MyCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="mycommand",
            description="My custom command",
            usage="mycommand [args]"
        )
    
    def execute(self, assistant, args: list) -> str:
        # Your implementation here
        return "Output"
```
