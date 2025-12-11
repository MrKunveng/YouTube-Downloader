# 🎥 YouTube Downloader - Hugging Face Spaces Deployment

This guide will help you deploy the YouTube Downloader to Hugging Face Spaces.

## 🚀 Quick Deployment Steps

### 1. Create a Hugging Face Account
- Go to [huggingface.co](https://huggingface.co) and sign up (free)

### 2. Create a New Space
1. Go to your profile → "New Space"
2. Fill in the details:
   - **Space name**: `youtube-downloader` (or your preferred name)
   - **SDK**: Select **Streamlit**
   - **Visibility**: Public (required for free tier)
   - Click "Create Space"

### 3. Push Your Code
You have two options:

#### Option A: Direct Git Push (Recommended)
```bash
# Add HF Spaces as a remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push hf main
```

#### Option B: Upload via Web Interface
1. Go to your Space page
2. Click "Files and versions" tab
3. Click "Add file" → "Upload files"
4. Upload all files from this repository

### 4. Required Files for HF Spaces
The repository already includes:
- ✅ `app.py` - Entry point for HF Spaces
- ✅ `downloader.py` - Main application code
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Space description

### 5. Wait for Build
- HF Spaces will automatically:
  - Install dependencies from `requirements.txt`
  - Install system packages (ffmpeg) if needed
  - Build and deploy your app
- This usually takes 2-5 minutes
- You can watch the build logs in the "Logs" tab

## 📋 Important Notes for HF Spaces

### System Packages
HF Spaces doesn't use `packages.txt` like Streamlit Cloud. Instead:
- FFmpeg is usually pre-installed
- If not, you may need to use a Dockerfile (see below)

### Environment Variables
HF Spaces automatically sets:
- `STREAMLIT_SERVER_HEADLESS=true` (detected by your code)
- Your app will use `/tmp` for downloads automatically

### File Storage
- Files in `/tmp` are ephemeral (deleted after session)
- Downloads are available via download button only
- No persistent storage on free tier

## 🐳 Optional: Using Dockerfile

If you need more control (e.g., specific ffmpeg version), create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Streamlit port
EXPOSE 7860

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
```

## 🔧 Troubleshooting

### Issue: App not starting
- Check the "Logs" tab for errors
- Ensure `app.py` exists and imports correctly
- Verify `requirements.txt` has all dependencies

### Issue: FFmpeg not found
- Check if ffmpeg is available: `which ffmpeg` in logs
- If not, use Dockerfile to install it
- Or update code to handle missing ffmpeg gracefully

### Issue: Downloads not working
- Check `/tmp` directory permissions
- Verify file paths are correct
- Check logs for file access errors

### Issue: 403 Forbidden errors
- YouTube may block HF Spaces IPs
- Consider adding cookies support (see main README)
- Try different videos to test

## 📝 Space Settings

In your Space settings, you can configure:
- **Hardware**: CPU (free) or GPU (paid)
- **Sleep time**: How long before app sleeps (free tier: 48 hours)
- **Variables**: Environment variables if needed
- **Secrets**: For API keys or cookies (if you add that feature)

## 🎯 Testing Your Deployment

1. Once deployed, visit your Space URL
2. Try downloading a simple video
3. Check the logs if there are issues
4. Test both video and audio downloads

## 📚 Resources

- [HF Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Streamlit on HF Spaces](https://huggingface.co/docs/hub/spaces-sdks-streamlit)
- [Your Space URL]: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

## ✅ Deployment Checklist

- [ ] Created HF account
- [ ] Created new Space with Streamlit SDK
- [ ] Pushed code to Space
- [ ] Verified build completed successfully
- [ ] Tested app functionality
- [ ] Checked logs for any errors

Good luck with your deployment! 🚀
