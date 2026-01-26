# Step-by-Step: Deploy to Hugging Face Spaces

This guide will walk you through deploying your YouTube Downloader to Hugging Face Spaces.

## Prerequisites

- ✅ A Hugging Face account (free at https://huggingface.co)
- ✅ Your code files ready
- ✅ Git installed (optional, but recommended)

---

## Method 1: Using Git (Recommended - 10 minutes)

### Step 1: Create/Verify Your Hugging Face Account

1. Go to https://huggingface.co
2. Sign up or log in
3. Verify your email if required

### Step 2: Create a New Space (if you don't have one)

1. Click your profile picture (top right)
2. Click **"New Space"**
3. Fill in the details:
   - **Space name**: `YouTube_downloader` (or your preferred name)
   - **SDK**: Select **"Docker"** (important!)
   - **Hardware**: **CPU basic** (free tier)
   - **Visibility**: **Public** (or Private if you prefer)
4. Click **"Create Space"**

### Step 3: Prepare Your Local Files

Make sure you have these files in your project directory:

```
YouTube/
├── downloader.py          ✅ Your main app
├── requirements.txt       ✅ Python dependencies
├── Dockerfile.hf          ✅ Docker configuration
├── README.md              ✅ HF Spaces metadata
└── app.py                 ✅ Entry point (optional)
```

### Step 4: Initialize Git (if not already done)

Open terminal in your project directory:

```bash
cd "/Users/lukman/Desktop/Work and projects/YouTube"

# Check if git is initialized
git status

# If not initialized, run:
git init
git add .
git commit -m "Initial commit for HF Spaces deployment"
```

### Step 5: Add Hugging Face Remote

```bash
# Add your HF Space as a remote
# Replace 'MrKunveng' with your HF username if different
git remote add hf https://huggingface.co/spaces/MrKunveng/YouTube_downloader

# Verify it was added
git remote -v
```

You should see:
```
hf  https://huggingface.co/spaces/MrKunveng/YouTube_downloader (fetch)
hf  https://huggingface.co/spaces/MrKunveng/YouTube_downloader (push)
```

### Step 6: Push to Hugging Face

```bash
# Push to main branch
git push hf main

# If you get an error about branch name, try:
git push hf main:main

# Or if your default branch is master:
git push hf master:main
```

### Step 7: Wait for Deployment

1. Go to your Space: https://huggingface.co/spaces/MrKunveng/YouTube_downloader
2. You'll see a build log
3. Wait 2-5 minutes for the build to complete
4. Status will change from "Building" to "Running" ✅

### Step 8: Access Your App

Once deployed, your app will be live at:
```
https://huggingface.co/spaces/MrKunveng/YouTube_downloader
```

---

## Method 2: Using Web UI (No Git Required - 15 minutes)

### Step 1: Create/Verify Your Space

1. Go to https://huggingface.co/spaces/MrKunveng/YouTube_downloader
2. If it doesn't exist, create it (see Method 1, Step 2)

### Step 2: Open the Space

1. Click on your Space
2. Click the **"Files and versions"** tab (top menu)

### Step 3: Upload Files

Upload these files one by one using the **"Add file"** button:

#### File 1: `downloader.py`
1. Click **"Add file"** → **"Upload file"**
2. Select your `downloader.py` file
3. Click **"Upload file"**

#### File 2: `requirements.txt`
1. Click **"Add file"** → **"Upload file"**
2. Select your `requirements.txt` file
3. Click **"Upload file"**

#### File 3: `Dockerfile.hf`
1. Click **"Add file"** → **"Upload file"**
2. Select your `Dockerfile.hf` file
3. **Important**: After uploading, click on the file and rename it to just `Dockerfile` (remove `.hf`)

#### File 4: `README.md`
1. Click **"Add file"** → **"Upload file"**
2. Select your `README.md` file
3. Click **"Upload file"**

### Step 4: Verify Files

Your Space should now have:
- ✅ `downloader.py`
- ✅ `requirements.txt`
- ✅ `Dockerfile` (renamed from `Dockerfile.hf`)
- ✅ `README.md`

### Step 5: Wait for Auto-Deployment

1. HF Spaces automatically detects changes
2. Go to the **"App"** tab
3. You'll see "Building..." status
4. Wait 2-5 minutes
5. Your app will appear when ready!

---

## Method 3: Using Hugging Face CLI (Advanced)

### Step 1: Install HF CLI

```bash
pip install huggingface_hub
```

### Step 2: Login

```bash
huggingface-cli login
```

Enter your HF token (get it from https://huggingface.co/settings/tokens)

### Step 3: Clone Your Space

```bash
git clone https://huggingface.co/spaces/MrKunveng/YouTube_downloader
cd YouTube_downloader
```

### Step 4: Copy Files

```bash
# Copy your files to the cloned directory
cp ../downloader.py .
cp ../requirements.txt .
cp ../Dockerfile.hf ./Dockerfile
cp ../README.md .
```

### Step 5: Commit and Push

```bash
git add .
git commit -m "Deploy YouTube Downloader"
git push
```

---

## Troubleshooting

### ❌ Build Fails: "Dockerfile not found"

**Solution:**
- Make sure the file is named exactly `Dockerfile` (not `Dockerfile.hf`)
- Check it's in the root of your Space
- Verify it was uploaded correctly

### ❌ Build Fails: "FFmpeg not found"

**Solution:**
- Check your Dockerfile includes: `apt-get install -y ffmpeg`
- Make sure it's in the RUN command before the app starts
- Check the build logs for specific errors

### ❌ App Crashes: "Port already in use"

**Solution:**
- Update `Dockerfile.hf` to use: `--server.port=${PORT:-7860}`
- HF Spaces sets the PORT environment variable automatically

### ❌ "Module not found" errors

**Solution:**
- Verify `requirements.txt` has all dependencies
- Check the build logs to see which module is missing
- Make sure `yt-dlp` and `streamlit` are in requirements.txt

### ❌ Build takes too long

**Solution:**
- This is normal for first build (2-5 minutes)
- Subsequent builds are faster (cached layers)
- Check build logs for any errors

### ❌ "Permission denied" when pushing

**Solution:**
- Make sure you're logged in: `huggingface-cli login`
- Verify you have write access to the Space
- Check you're using the correct Space URL

---

## Verifying Your Deployment

### ✅ Check Build Status

1. Go to your Space
2. Click **"App"** tab
3. Look for:
   - 🟢 **"Running"** = Success!
   - 🟡 **"Building"** = Still deploying
   - 🔴 **"Failed"** = Check logs

### ✅ Check Build Logs

1. Click **"Files and versions"** tab
2. Click **"Logs"** (top right)
3. Look for errors in red
4. Common issues:
   - Missing dependencies
   - Dockerfile syntax errors
   - Port conflicts

### ✅ Test Your App

1. Go to the **"App"** tab
2. Try downloading a video:
   - Paste a YouTube URL
   - Select video/audio
   - Click Download
3. If it works, you're done! 🎉

---

## Updating Your App

### Using Git:

```bash
# Make your changes to downloader.py
git add downloader.py
git commit -m "Update app"
git push hf main
```

### Using Web UI:

1. Go to **"Files and versions"** tab
2. Click on the file you want to edit
3. Click **"Edit"** button
4. Make changes
5. Click **"Commit changes"**
6. Wait for auto-deployment

---

## File Structure Reference

Your HF Space should have this structure:

```
YouTube_downloader/
├── Dockerfile          # Docker configuration (renamed from Dockerfile.hf)
├── downloader.py       # Your main Streamlit app
├── requirements.txt    # Python dependencies
├── README.md          # Space metadata and description
└── .gitignore         # (optional) Git ignore file
```

---

## Quick Checklist

Before deploying, make sure:

- [ ] `Dockerfile` exists and installs ffmpeg
- [ ] `requirements.txt` has `streamlit` and `yt-dlp`
- [ ] `downloader.py` is your main app file
- [ ] `README.md` has HF Spaces metadata (sdk: docker)
- [ ] You're logged into Hugging Face
- [ ] You have write access to the Space

---

## Common Commands Reference

```bash
# Add HF remote
git remote add hf https://huggingface.co/spaces/USERNAME/SPACE_NAME

# Push to HF
git push hf main

# Check remotes
git remote -v

# View build logs (in HF web UI)
# Go to Space → Files and versions → Logs

# Clone Space locally
git clone https://huggingface.co/spaces/USERNAME/SPACE_NAME
```

---

## Next Steps

Once deployed:

1. ✅ Share your app URL with others
2. ✅ Monitor usage in HF dashboard
3. ✅ Update app as needed (just push changes)
4. ✅ Check logs if issues arise

## Need Help?

- **HF Spaces Docs**: https://huggingface.co/docs/hub/spaces
- **HF Community**: https://huggingface.co/discuss
- **Build Logs**: Check in your Space's "Logs" section

---

## Success Indicators

You'll know it's working when:

1. ✅ Build status shows "Running" (green)
2. ✅ App loads in the browser
3. ✅ You can paste a YouTube URL
4. ✅ Download works without errors
5. ✅ No errors in the browser console

**Congratulations! Your YouTube Downloader is now live! 🎉**
