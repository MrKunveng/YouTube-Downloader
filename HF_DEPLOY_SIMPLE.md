# 🚀 Quick Deploy to Hugging Face Spaces (5 Steps)

## Step 1: Prepare Files ✅

Make sure these 4 files are ready:

```
✅ downloader.py
✅ requirements.txt  
✅ Dockerfile.hf
✅ README.md
```

## Step 2: Go to Your Space 🌐

Open: https://huggingface.co/spaces/MrKunveng/YouTube_downloader

(Or create new: https://huggingface.co/new-space)

## Step 3: Upload Files 📤

1. Click **"Files and versions"** tab
2. Click **"Add file"** → **"Upload file"**
3. Upload each file:
   - `downloader.py`
   - `requirements.txt`
   - `Dockerfile.hf` → **Rename to `Dockerfile`** after upload
   - `README.md`

## Step 4: Wait ⏳

1. Click **"App"** tab
2. Watch "Building..." status
3. Wait 2-5 minutes

## Step 5: Done! 🎉

Your app is live at:
**https://huggingface.co/spaces/MrKunveng/YouTube_downloader**

---

## OR Use Git (Faster) 🐙

```bash
# In your project folder
git remote add hf https://huggingface.co/spaces/MrKunveng/YouTube_downloader
git push hf main
```

Done! 🚀
