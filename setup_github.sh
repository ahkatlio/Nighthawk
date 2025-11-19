#!/bin/bash
# Quick setup script to push Nighthawk to GitHub

echo "🦅 Nighthawk GitHub Setup"
echo "========================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✓ Git initialized"
else
    echo "✓ Git already initialized"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo ""
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Backup files
*.old
*.backup
*.bak

# Logs
*.log

# Temporary files
*.tmp
.pytest_cache/
EOF
    echo "✓ .gitignore created"
fi

# Check for remote
if git remote | grep -q "origin"; then
    echo ""
    echo "⚠️  Remote 'origin' already exists:"
    git remote -v
    echo ""
    read -p "Remove existing remote? (y/n): " remove_remote
    if [ "$remove_remote" = "y" ]; then
        git remote remove origin
        echo "✓ Remote removed"
    fi
fi

# Get GitHub username and repo name
echo ""
echo "📝 GitHub Repository Setup"
echo "=========================="
read -p "Enter your GitHub username: " github_user
read -p "Enter repository name (default: Nighthawk): " repo_name
repo_name=${repo_name:-Nighthawk}

# Add remote
echo ""
echo "🔗 Adding GitHub remote..."
git remote add origin "https://github.com/$github_user/$repo_name.git"
echo "✓ Remote added: https://github.com/$github_user/$repo_name.git"

# Stage all files
echo ""
echo "📦 Staging files..."
git add .
echo "✓ Files staged"

# Show what will be committed
echo ""
echo "📋 Files to be committed:"
git status --short

# Commit
echo ""
read -p "Enter commit message (default: Initial commit - Nighthawk v2.0): " commit_msg
commit_msg=${commit_msg:-"Initial commit - Nighthawk v2.0"}
git commit -m "$commit_msg"
echo "✓ Changes committed"

# Push
echo ""
echo "🚀 Pushing to GitHub..."
echo ""
echo "⚠️  IMPORTANT: Create the repository on GitHub first!"
echo "   Go to: https://github.com/new"
echo "   Repository name: $repo_name"
echo "   Description: AI-powered modular security tool orchestrator"
echo "   Make it: Public or Private (your choice)"
echo "   DO NOT initialize with README, .gitignore, or license"
echo ""
read -p "Have you created the repository on GitHub? (y/n): " created

if [ "$created" = "y" ]; then
    echo ""
    echo "Pushing to main branch..."
    git branch -M main
    git push -u origin main
    echo ""
    echo "✅ SUCCESS! Nighthawk is now on GitHub!"
    echo "🔗 View at: https://github.com/$github_user/$repo_name"
else
    echo ""
    echo "⏸️  Push cancelled. When ready, run:"
    echo "   git branch -M main"
    echo "   git push -u origin main"
fi

echo ""
echo "🎉 Done!"
