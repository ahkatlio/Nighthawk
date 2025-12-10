# 🤝 Contributing to Nighthawk

First off, thank you for considering contributing to Nighthawk! It's people like you that make Nighthawk such a great tool for the security community.

## 🌟 Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher
- Ollama with `dolphin-llama3:8b` model
- Basic security tools (nmap, ssh-audit, etc.)
- Git for version control

### Setting Up Development Environment

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Nighthawk.git
   cd Nighthawk
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .pyenv
   source .pyenv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Add your Google API key if testing Gemini features
   ```

5. **Test Your Setup**
   ```bash
   ./start_tui.sh
   ```

## 🎯 How Can I Contribute?

### 🐛 Reporting Bugs

Found a bug? Help us squash it!

**Before Submitting:**
- Check if the bug has already been reported in [Issues](https://github.com/ahkatlio/Nighthawk/issues)
- Ensure you're using the latest version
- Collect relevant information (OS, Python version, error messages)

**Submit a Bug Report:**
```markdown
**Bug Description:**
Clear and concise description of the bug

**Steps to Reproduce:**
1. Launch Nighthawk
2. Run command '...'
3. See error

**Expected Behavior:**
What should have happened

**Actual Behavior:**
What actually happened

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python Version: [e.g., 3.11.4]
- Nighthawk Version: [e.g., commit hash]

**Logs/Screenshots:**
Attach relevant error messages or screenshots
```

### 💡 Suggesting Features

Have an idea to make Nighthawk better?

**Feature Request Template:**
```markdown
**Feature Description:**
Clear description of the proposed feature

**Problem It Solves:**
What problem does this address?

**Proposed Solution:**
How would you implement this?

**Alternatives Considered:**
Other approaches you've thought about

**Additional Context:**
Mockups, examples, or references
```

### 🔧 Contributing Code

#### Finding Something to Work On

- Check [Issues](https://github.com/ahkatlio/Nighthawk/issues) labeled `good first issue`
- Look for `help wanted` tags
- Review the roadmap in README.md

#### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/amazing-feature
   # or
   git checkout -b fix/bug-description
   ```

2. **Make Your Changes**
   - Write clean, readable code
   - Follow existing code style
   - Add comments for complex logic
   - Keep commits atomic and focused

3. **Test Your Changes**
   ```bash
   # Run Nighthawk and test your feature
   ./start_tui.sh
   
   # Test edge cases
   # Verify nothing broke
   ```

4. **Commit with Meaningful Messages**
   ```bash
   git commit -m "feat: add DNS enumeration tool integration"
   git commit -m "fix: resolve ssh-audit port detection issue"
   git commit -m "docs: update installation instructions"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/amazing-feature
   ```

#### Pull Request Guidelines

**PR Title Format:**
- `feat: Add new feature`
- `fix: Fix bug description`
- `docs: Update documentation`
- `style: Code style improvements`
- `refactor: Code refactoring`
- `test: Add or update tests`
- `chore: Maintenance tasks`

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested on Linux
- [ ] Tested on macOS
- [ ] Tested on Windows
- [ ] Manual testing performed
- [ ] Edge cases verified

## Checklist
- [ ] Code follows project style
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Tested thoroughly

## Screenshots (if applicable)
Add screenshots demonstrating the changes
```

## 🔨 Development Guidelines

### Code Style

**Python Style:**
- Follow PEP 8 conventions
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable names

**Example:**
```python
def parse_scan_results(self, output: str) -> Dict[str, any]:
    """
    Parse tool output into structured data
    
    Args:
        output: Raw command output string
        
    Returns:
        Dictionary containing parsed results
    """
    results = {}
    # Implementation...
    return results
```

**Bash Style:**
- Use shellcheck for validation
- Add comments for complex logic
- Use `set -e` for error handling
- Quote variables: `"$variable"`

### Adding a New Security Tool

1. **Create Tool Class** (`tools/your_tool.py`):
   ```python
   from .base_tool import BaseTool
   
   class YourTool(BaseTool):
       def __init__(self):
           super().__init__(name="tool-name", command="tool-command")
           self.description = "Tool description"
           self.knowledge = {}
       
       def check_installed(self) -> bool:
           # Check if tool is installed
           pass
       
       def generate_command(self, user_request: str, ai_response: str) -> str:
           # Generate command from user input
           pass
       
       def execute(self, command: str) -> Dict:
           # Execute the command
           pass
       
       def format_output(self, result: Dict) -> None:
           # Display formatted results
           pass
   ```

2. **Register Tool** (`main.py`):
   ```python
   from tools.your_tool import YourTool
   
   def _register_tools(self):
       # ... existing tools
       your_tool = YourTool()
       self.tools['tool-name'] = your_tool
   ```

3. **Update Detection** (`main.py` - `detect_tool` method):
   ```python
   if any(phrase in request_lower for phrase in ['tool keyword', 'tool-name']):
       if 'tool-name' in self.tools:
           return 'tool-name'
   ```

4. **Add Documentation**:
   - Update README.md with tool description
   - Add usage examples
   - Document any special requirements

### Testing Checklist

Before submitting your PR, verify:

- [ ] Tool detection works with natural language
- [ ] Commands generate correctly
- [ ] Error handling works gracefully
- [ ] Output formatting is clean and readable
- [ ] No regression in existing features
- [ ] Works with and without previous scan context
- [ ] Help text is clear and informative

## 📚 Documentation

Good documentation is crucial! When contributing:

- **Code Comments:** Explain *why*, not *what*
- **Docstrings:** Use for all functions and classes
- **README Updates:** Keep feature list current
- **Examples:** Add usage examples for new features

## 🎨 Animation Contributions

Contributing animations? Follow these guidelines:

- Use bash with `tput` for portability
- Clear screen appropriately
- Keep timing reasonable (not too slow)
- Test on different terminal sizes
- Add comments explaining the effect

## 🤔 Questions?

- **General Questions:** Open a [Discussion](https://github.com/ahkatlio/Nighthawk/discussions)
- **Bug Reports:** File an [Issue](https://github.com/ahkatlio/Nighthawk/issues)
- **Security Concerns:** Email directly (don't post publicly)

## 📜 License

By contributing to Nighthawk, you agree that your contributions will be licensed under the same license as the project.

## 🏆 Recognition

Contributors are recognized in:
- README.md Contributors section
- Release notes
- GitHub Contributors graph

---

<div align="center">

**Thank you for making Nighthawk better! 🦅**

*Every contribution, no matter how small, is valued and appreciated.*

</div>
