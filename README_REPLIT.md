# 🎥 YouTube Downloader - Replit Deployment Guide

This guide will help you deploy the YouTube Downloader to Replit.

## 🚀 Quick Deployment Steps

### 1. Create a Replit Account
- Go to [replit.com](https://replit.com) and sign up (free)

### 2. Create a New Repl
1. Click "Create Repl" or the "+" button
2. Select **"Import from GitHub"**
3. Enter your repository URL: `https://github.com/MrKunveng/YouTube-Downloader`
4. Choose **"Python"** as the template
5. Click "Import"

### 3. Configure Replit
The repository already includes:
- ✅ `.replit` - Configuration file for running Streamlit
- ✅ `replit.nix` - System packages (includes ffmpeg)
- ✅ `requirements.txt` - Python dependencies
- ✅ `downloader.py` - Main application

### 4. Install Dependencies
Replit will automatically install packages from `requirements.txt` when you run the repl.

If you need to manually install:
```bash
pip install -r requirements.txt
```

### 5. Run the App
1. Click the **"Run"** button in Replit
2. The app will start and show a URL
3. Click the URL or use the webview to access your app

## 📋 Replit Configuration Files

### `.replit` File
This file configures:
- Language: Python 3
- Run command: Streamlit with proper port and address
- Environment variables for cloud deployment

### `replit.nix` File
This file installs system packages:
- `ffmpeg` - Required for video/audio processing
- Python 3.11
- Other necessary dependencies

## 🔧 Important Notes for Replit

### Port Configuration
- Replit uses port `8080` by default
- The `.replit` file is configured to use this port
- The app will be accessible via Replit's webview

### File Storage
- Files are stored in the repl's file system
- Downloads will be in the `temp_downloads` folder
- Files persist as long as the repl is active

### Always-On Repls
- Free tier: Repls may sleep after inactivity
- To keep it running: Upgrade to "Always On" (paid) or use Replit's free "Always On" for students

### Environment Variables
The app automatically detects Replit environment and:
- Uses cloud mode settings
- Stores files in appropriate locations
- Handles downloads correctly

## 🎯 Running Your App

### Method 1: Using the Run Button
1. Click the green **"Run"** button
2. Wait for dependencies to install
3. Click the webview URL that appears

### Method 2: Using the Shell
```bash
streamlit run downloader.py --server.port=8080 --server.address=0.0.0.0
```

## 🔍 Troubleshooting

### Issue: FFmpeg not found
- Check if `replit.nix` includes `pkgs.ffmpeg`
- Try running: `which ffmpeg` in the shell
- If missing, the app will show installation instructions

### Issue: Port already in use
- Replit should handle port 8080 automatically
- If issues occur, check the `.replit` file configuration

### Issue: App not starting
- Check the console for errors
- Verify all dependencies are installed: `pip list`
- Check if Streamlit is installed: `pip show streamlit`

### Issue: Downloads not working
- Check file permissions in Replit
- Verify temp_downloads folder exists
- Check console logs for errors

## 📝 Replit Features

### Webview
- Replit automatically provides a webview for web apps
- Click the webview tab to see your app
- The URL is automatically generated

### Secrets (Environment Variables)
To add secrets (like API keys):
1. Click the "Secrets" tab (lock icon)
2. Add key-value pairs
3. Access via `os.environ.get('KEY_NAME')`

### Always-On
- Free tier: Repls sleep after 1 hour of inactivity
- Paid/Student: Can enable "Always On"
- Consider using a ping service for free tier

## 🚀 Deployment Options

### Option 1: Keep Running in Replit
- Just click "Run" whenever you want to use it
- Free tier: Repl sleeps after inactivity
- Good for: Development and testing

### Option 2: Deploy as Web App
- Replit can deploy your app as a web service
- Click "Deploy" button (if available)
- Creates a public URL for your app

## ✅ Deployment Checklist

- [ ] Created Replit account
- [ ] Imported repository from GitHub
- [ ] Verified `.replit` and `replit.nix` files exist
- [ ] Clicked "Run" button
- [ ] Verified app loads in webview
- [ ] Tested video download functionality
- [ ] Checked console for any errors

## 📚 Resources

- [Replit Documentation](https://docs.replit.com)
- [Replit Python Guide](https://docs.replit.com/programming-ide/running-code)
- [Your Repl URL]: Will be shown in Replit interface

## 💡 Tips

- **Keep it running**: Use "Always On" if you want 24/7 availability
- **Monitor usage**: Check Replit's usage dashboard
- **Backup code**: Your code is saved automatically
- **Share easily**: Replit provides shareable links

Good luck with your deployment! 🚀
