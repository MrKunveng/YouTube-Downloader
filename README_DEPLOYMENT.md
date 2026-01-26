# Deployment Guide for YouTube Downloader

This guide covers the best deployment options for the YouTube Downloader app, which requires `ffmpeg` and `yt-dlp`.

## Why Streamlit Cloud Has Issues

Streamlit Cloud has limitations:
- ❌ Cannot install system packages like `ffmpeg`
- ❌ Limited control over the environment
- ❌ Dependency conflicts with `yt-dlp`
- ❌ No Docker support

## Best Deployment Options

### 🥇 Option 1: Hugging Face Spaces (Recommended - Easiest)

**Why it's best:**
- ✅ Free tier with good resources
- ✅ Built-in Docker support
- ✅ Easy setup
- ✅ Automatic HTTPS
- ✅ You already have a Space configured!

**Steps:**

1. **Update your Space configuration:**
   ```bash
   # In your HF Space, use Dockerfile.hf
   # Or create a README.md in your Space with:
   ```

2. **Create `README.md` in your HF Space:**
   ```yaml
   ---
   title: YouTube Downloader
   emoji: 🎥
   colorFrom: blue
   colorTo: purple
   sdk: docker
   app_file: Dockerfile.hf
   pinned: false
   ---
   ```

3. **Push to Hugging Face:**
   ```bash
   git add .
   git commit -m "Add HF deployment config"
   git push hf main
   ```

4. **Or use the web interface:**
   - Go to https://huggingface.co/spaces/MrKunveng/YouTube_downloader
   - Upload files via web UI
   - Use `Dockerfile.hf` as your Dockerfile

**Files needed:**
- `Dockerfile.hf`
- `downloader.py`
- `requirements.txt`
- `README.md` (with HF metadata)

---

### 🥈 Option 2: Railway (Best for Production)

**Why it's great:**
- ✅ Free tier ($5 credit/month)
- ✅ Excellent Docker support
- ✅ Auto-deploy from GitHub
- ✅ Easy scaling
- ✅ Great for production apps

**Steps:**

1. **Sign up at [railway.app](https://railway.app)**

2. **Connect your GitHub repo**

3. **Railway will auto-detect the Dockerfile**

4. **Set environment variables (if needed):**
   - Railway handles everything automatically

5. **Deploy!**

**Files needed:**
- `Dockerfile`
- `railway.json` (optional, for custom config)
- `downloader.py`
- `requirements.txt`

**Cost:** Free tier with $5 credit/month, then pay-as-you-go

---

### 🥉 Option 3: Render (Good Free Option)

**Why it's good:**
- ✅ Free tier available
- ✅ Docker support
- ✅ Auto-deploy from GitHub
- ✅ Good documentation

**Steps:**

1. **Sign up at [render.com](https://render.com)**

2. **Create a new Web Service**

3. **Connect your GitHub repo**

4. **Configure:**
   - Build Command: `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`
   - Start Command: `streamlit run downloader.py --server.port=$PORT --server.address=0.0.0.0`

5. **Or use `render.yaml` (already created)**

**Files needed:**
- `render.yaml`
- `downloader.py`
- `requirements.txt`

**Cost:** Free tier (spins down after inactivity), paid plans start at $7/month

---

### Option 4: Fly.io (Good for Global Distribution)

**Why it's good:**
- ✅ Free tier
- ✅ Global edge network
- ✅ Great Docker support
- ✅ Fast deployments

**Steps:**

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Create app:**
   ```bash
   fly launch
   ```

4. **Deploy:**
   ```bash
   fly deploy
   ```

**Files needed:**
- `Dockerfile`
- `fly.toml` (auto-generated)
- `downloader.py`
- `requirements.txt`

---

### Option 5: Self-Hosted VPS (Most Control)

**Best VPS Providers:**
- DigitalOcean ($6/month)
- Linode ($5/month)
- Vultr ($6/month)
- Hetzner (€4/month)

**Steps:**

1. **Create a VPS (Ubuntu 22.04 recommended)**

2. **SSH into your server:**
   ```bash
   ssh root@your-server-ip
   ```

3. **Install dependencies:**
   ```bash
   apt update
   apt install -y python3-pip ffmpeg git
   ```

4. **Clone your repo:**
   ```bash
   git clone https://github.com/MrKunveng/YouTube-Downloader.git
   cd YouTube-Downloader
   ```

5. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

6. **Run with systemd (create `/etc/systemd/system/youtube-downloader.service`):**
   ```ini
   [Unit]
   Description=YouTube Downloader Streamlit App
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/YouTube-Downloader
   ExecStart=/usr/bin/streamlit run downloader.py --server.port=8501 --server.address=0.0.0.0
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start the service:**
   ```bash
   systemctl enable youtube-downloader
   systemctl start youtube-downloader
   ```

8. **Set up Nginx reverse proxy (optional but recommended):**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

---

## Quick Comparison

| Platform | Free Tier | Docker | Ease | Best For |
|----------|-----------|--------|------|----------|
| **Hugging Face** | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐⭐ | Quick deployment |
| **Railway** | ✅ $5 credit | ✅ Yes | ⭐⭐⭐⭐ | Production apps |
| **Render** | ✅ Limited | ✅ Yes | ⭐⭐⭐⭐ | Simple deployments |
| **Fly.io** | ✅ Yes | ✅ Yes | ⭐⭐⭐ | Global distribution |
| **VPS** | ❌ No | ✅ Yes | ⭐⭐ | Full control |

---

## Recommended: Hugging Face Spaces

Since you already have a Space configured, **Hugging Face Spaces is the easiest option**. Just:

1. Use the `Dockerfile.hf` file
2. Push your code to the HF Space
3. It will auto-deploy!

## Troubleshooting

### FFmpeg not found
- Make sure your Dockerfile installs ffmpeg: `apt-get install -y ffmpeg`
- Check that the installation happens before the app runs

### Port issues
- Use `$PORT` environment variable (most platforms set this)
- Default to 8501 if `$PORT` is not set

### Memory issues
- Reduce video quality options
- Add memory limits in deployment config
- Consider upgrading your plan

### Timeout issues
- Increase timeout settings in your platform
- Optimize download code (already done in your optimized version)

---

## Need Help?

- **Hugging Face:** https://huggingface.co/docs/hub/spaces
- **Railway:** https://docs.railway.app
- **Render:** https://render.com/docs
- **Fly.io:** https://fly.io/docs
