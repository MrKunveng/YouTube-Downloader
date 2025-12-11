# Cloud Deployment Guide

This guide helps you deploy the YouTube Downloader to Streamlit Cloud successfully.

## ✅ Checklist for Cloud Deployment

### 1. Required Files

- ✅ `packages.txt` - Contains `ffmpeg` (already included)
- ✅ `requirements.txt` - Updated with latest yt-dlp version
- ✅ `downloader.py` - Configured for cloud mode

### 2. Cloud Mode Configuration

The app automatically detects cloud deployment using:
```python
IS_CLOUD_DEPLOYMENT = os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false').lower() == 'true'
```

In cloud mode:
- Downloads are saved to `/tmp` (ephemeral)
- Custom download folders are ignored
- Files are available for download via download button

### 3. Optional: Add Cookies (Recommended for Cloud)

YouTube may block cloud IPs. Adding cookies helps bypass this:

1. **Export cookies from your browser:**
   - Install browser extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Visit YouTube and export cookies
   - Save as `cookies.txt`

2. **Add to your repo:**
   - Place `cookies.txt` in the root directory, OR
   - Place in `.streamlit/cookies.txt` folder

3. **The app will automatically detect and use it**

### 4. Update yt-dlp

The `requirements.txt` includes:
```
yt-dlp>=2023.12.30
```

Make sure to update if needed:
```bash
pip install --upgrade yt-dlp
```

### 5. Check Logs

In Streamlit Cloud:
1. Go to your app
2. Click "Manage app"
3. View "Logs"

Look for:
- `Cloud mode: True`
- `ffmpeg path: ffmpeg`
- `Using cookies file: cookies.txt` (if added)
- Any 403 Forbidden errors

### 6. Common Issues

#### Issue: 403 Forbidden
**Solution:**
- Add `cookies.txt` file
- Update yt-dlp to latest version
- Wait a few minutes (rate limiting)

#### Issue: No formats found
**Solution:**
- Check if video is available
- Try different video
- Update yt-dlp

#### Issue: ffmpeg not found
**Solution:**
- Ensure `packages.txt` contains `ffmpeg`
- Redeploy the app

## 📝 File Structure

```
YouTube-Downloader/
├── downloader.py          # Main app
├── requirements.txt       # Python dependencies
├── packages.txt          # System packages (ffmpeg)
├── cookies.txt          # Optional: YouTube cookies
├── .streamlit/
│   └── cookies.txt      # Alternative location for cookies
└── README.md
```

## 🚀 Deployment Steps

1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Deploy from GitHub repo
4. (Optional) Add `cookies.txt` via Streamlit secrets or file upload
5. Test with a simple video URL

## 💡 Tips

- **Cookies**: Highly recommended for cloud deployment
- **Logs**: Check logs first when debugging
- **Updates**: Keep yt-dlp updated for latest YouTube changes
- **Testing**: Test with simple videos first before complex playlists
