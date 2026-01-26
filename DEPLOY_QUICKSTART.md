# Quick Start Deployment Guide

## 🚀 Fastest Option: Hugging Face Spaces (5 minutes)

You already have a Space! Just follow these steps:

### Step 1: Prepare Files
Make sure you have these files in your repo:
- ✅ `downloader.py`
- ✅ `requirements.txt`
- ✅ `Dockerfile.hf`
- ✅ `README.md` (with HF metadata)

### Step 2: Push to Hugging Face

**Option A: Using Git (Recommended)**
```bash
# Add HF remote if not already added
git remote add hf https://huggingface.co/spaces/MrKunveng/YouTube_downloader

# Push to HF
git push hf main
```

**Option B: Using Web UI**
1. Go to https://huggingface.co/spaces/MrKunveng/YouTube_downloader
2. Click "Files and versions" tab
3. Upload all files
4. Wait for deployment (2-3 minutes)

### Step 3: Access Your App
Your app will be live at:
`https://huggingface.co/spaces/MrKunveng/YouTube_downloader`

---

## 🚂 Alternative: Railway (10 minutes)

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repo
6. Railway auto-detects Dockerfile
7. Click "Deploy"
8. Done! Get your URL from Railway dashboard

---

## 📦 Alternative: Render (10 minutes)

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Render will auto-detect `render.yaml`
6. Click "Create Web Service"
7. Wait for deployment
8. Done!

---

## Which Should You Choose?

| If you want... | Choose... |
|----------------|-----------|
| **Easiest setup** | Hugging Face Spaces |
| **Production app** | Railway |
| **Free tier** | Render or Hugging Face |
| **Full control** | VPS (see README_DEPLOYMENT.md) |

---

## Troubleshooting

### "FFmpeg not found"
- Make sure your Dockerfile includes: `apt-get install -y ffmpeg`
- Check that it's installed before the app runs

### "Port already in use"
- Use `$PORT` environment variable
- Most platforms set this automatically

### "Build failed"
- Check Dockerfile syntax
- Ensure all files are in the repo
- Check platform logs for specific errors

---

## Need More Details?

See `README_DEPLOYMENT.md` for comprehensive deployment guides.
