# GitHub Setup Instructions

Your project is now ready to push to GitHub! Follow these steps:

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Repository settings:
   - **Name:** `ActionFigureTracker` (or whatever you prefer)
   - **Description:** "iOS app for tracking action figure collections"
   - **Visibility:** Private (recommended) or Public
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

## Step 2: Add Remote and Push

After creating the repo, GitHub will show you commands. Use these:

### On Windows (where you are now):

```powershell
cd c:\Code\ActionFigureTracker
git remote add origin https://github.com/YOUR_USERNAME/ActionFigureTracker.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### If you need to authenticate:
- GitHub may prompt for credentials
- Use a Personal Access Token (not your password)
- Create one at: https://github.com/settings/tokens
- Select scope: `repo` (full control of private repositories)

## Step 3: Clone on Mac

On your Mac Mini:

```bash
cd ~/Desktop  # or wherever you want it
git clone https://github.com/YOUR_USERNAME/ActionFigureTracker.git
cd ActionFigureTracker
open ActionFigureTracker.xcodeproj
```

## Step 4: Workflow Between Machines

### Making changes on Mac:
```bash
cd ~/Desktop/ActionFigureTracker
# Make your changes in Xcode
git add .
git commit -m "Your commit message"
git push
```

### Pulling changes on Windows:
```powershell
cd c:\Code\ActionFigureTracker
git pull
```

### Making changes on Windows:
```powershell
cd c:\Code\ActionFigureTracker
# Make your changes
git add .
git commit -m "Your commit message"
git push
```

### Pulling changes on Mac:
```bash
cd ~/Desktop/ActionFigureTracker
git pull
```

## Important Notes

### Line Endings (LF vs CRLF)
- Git will automatically handle line endings between Windows (CRLF) and Mac (LF)
- The warnings you saw are normal and won't cause issues
- If you want to configure it explicitly:
  ```bash
  git config core.autocrlf true  # On Windows
  git config core.autocrlf input # On Mac
  ```

### What's NOT in Git (by design)
The `.gitignore` excludes:
- `xcuserdata/` - Your personal Xcode settings
- `build/` - Build artifacts
- `DerivedData/` - Xcode derived data
- `*.xcworkspace` - If you add CocoaPods later

### What IS in Git
- ✅ All Swift source files
- ✅ Project file (`project.pbxproj`)
- ✅ Assets (images, colors)
- ✅ JSON data file (`all_figures.json`)
- ✅ Documentation (README, etc.)

## Troubleshooting

### "Repository not found"
- Check your GitHub username is correct
- Verify you have access to the repository
- Make sure you're using HTTPS (not SSH) if you haven't set up SSH keys

### Authentication Issues
- Use a Personal Access Token instead of password
- Create at: https://github.com/settings/tokens
- Select `repo` scope

### Merge Conflicts
If you get conflicts when pulling:
```bash
git pull
# Fix conflicts in Xcode
git add .
git commit -m "Resolved merge conflicts"
git push
```

## Quick Reference

```bash
# Check status
git status

# See what changed
git diff

# View commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- .
```
