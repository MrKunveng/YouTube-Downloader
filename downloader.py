import os
import streamlit as st
from pathlib import Path
import platform
import yt_dlp
import logging

# Configure logging for cloud environment
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cloud deployment detection
# Streamlit Cloud sets STREAMLIT_SHARING_MODE or runs headless without HOME set to user dir
IS_CLOUD_DEPLOYMENT = (
    os.environ.get('STREAMLIT_SHARING_MODE') is not None or          # Streamlit Cloud
    os.environ.get('STREAMLIT_SERVER_HEADLESS', '').lower() == 'true' or
    os.environ.get('SPACE_ID') is not None or                         # Hugging Face Spaces
    os.environ.get('REPL_ID') is not None or                          # Replit
    os.environ.get('RAILWAY_ENVIRONMENT') is not None or              # Railway
    os.environ.get('RENDER') is not None                              # Render
)

# Use /tmp for cloud; temp_downloads/ locally
CLOUD_TEMP_DIR = Path("/tmp/yt_downloads")
LOCAL_TEMP_DIR = Path("temp_downloads")


# ─────────────────────────────────────────────
# Custom CSS — dark YouTube-inspired theme
# ─────────────────────────────────────────────
CUSTOM_CSS = """
<style>
/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Segoe UI', Roboto, Arial, sans-serif;
}

/* ── Page background ── */
.stApp {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 50%, #0f0f0f 100%);
    min-height: 100vh;
}

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(90deg, #ff0000 0%, #cc0000 50%, #990000 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(255, 0, 0, 0.35);
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.08) 0%, transparent 60%);
}
.hero-banner h1 {
    font-size: 2.8rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    text-shadow: 0 2px 8px rgba(0,0,0,0.4);
    letter-spacing: -0.5px;
}
.hero-banner p {
    color: rgba(255,255,255,0.85);
    font-size: 1.05rem;
    margin-top: 0.5rem;
}

/* ── Badge ── */
.mode-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.8rem;
    color: #fff;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-top: 0.75rem;
}

/* ── Section cards ── */
.section-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(6px);
    transition: border-color 0.2s;
}
.section-card:hover {
    border-color: rgba(255, 0, 0, 0.4);
}
.section-title {
    font-size: 0.9rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #ff4444;
    margin-bottom: 0.75rem;
}

/* ── Inputs ── */
input[type="text"], .stTextInput input {
    background: rgba(255,255,255,0.06) !important;
    border: 1.5px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #fff !important;
    padding: 0.6rem 1rem !important;
    transition: border-color 0.2s !important;
}
input[type="text"]:focus, .stTextInput input:focus {
    border-color: #ff4444 !important;
    box-shadow: 0 0 0 3px rgba(255, 68, 68, 0.18) !important;
}

/* ── Select boxes ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1.5px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #fff !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #ff2222, #cc0000) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.65rem 2rem !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 16px rgba(255,0,0,0.35) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #ff4444, #e60000) !important;
    box-shadow: 0 6px 24px rgba(255,0,0,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #1db954, #15803d) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 16px rgba(29,185,84,0.3) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
.stDownloadButton > button:hover {
    box-shadow: 0 6px 24px rgba(29,185,84,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── Progress bar ── */
.stProgress > div > div {
    background: linear-gradient(90deg, #ff2222, #ff6b6b) !important;
    border-radius: 6px !important;
}
.stProgress > div {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 6px !important;
}

/* ── Alert/info boxes ── */
.stAlert {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ── Metric cards ── */
.metric-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ff4444;
}
.metric-label {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.55);
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ── Divider ── */
hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 1.5rem 0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #ff3333; border-radius: 3px; }

/* ── Footer ── */
.footer {
    text-align: center;
    color: rgba(255,255,255,0.3);
    font-size: 0.78rem;
    padding: 2rem 0 1rem;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin-top: 3rem;
}
</style>
"""


def check_ffmpeg():
    """Check if ffmpeg is installed and accessible."""
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if platform.system() == "Windows":
        ffmpeg_paths = [
            Path.cwd() / "ffmpeg.exe",
            Path.cwd() / "ffmpeg" / "bin" / "ffmpeg.exe",
            Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe",
        ]
        for path in ffmpeg_paths:
            if path.exists():
                return str(path)
    return None


def show_ffmpeg_instructions():
    """Show instructions for installing ffmpeg."""
    st.error("❌ FFmpeg is required but not found on this system.")
    if IS_CLOUD_DEPLOYMENT:
        st.info("Make sure `packages.txt` contains `ffmpeg` in the repository root.")
        st.stop()

    system = platform.system()
    if system == "Windows":
        st.markdown("""
**Windows** — download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and place
`ffmpeg.exe` in this folder, or run:
```powershell
choco install ffmpeg
```
""")
    elif system == "Darwin":
        st.markdown("""
**macOS** — install via Homebrew:
```bash
brew install ffmpeg
```
""")
    else:
        st.markdown("""
**Linux** — install via package manager:
```bash
sudo apt update && sudo apt install ffmpeg   # Debian/Ubuntu
sudo dnf install ffmpeg                       # Fedora
sudo pacman -S ffmpeg                         # Arch
```
""")
    st.stop()


def select_best_format_with_audio(formats, quality=None):
    """Return the best combined (video+audio) format, optionally filtered by quality."""
    combined = [
        f for f in formats
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none'
    ]
    if not combined:
        return None
    if quality:
        filtered = [f for f in combined if (f.get('height') or 0) <= quality]
        if filtered:
            combined = filtered
    combined.sort(key=lambda x: ((x.get('height') or 0), (x.get('filesize') or 0)), reverse=True)
    return combined[0]


def get_available_browsers():
    """Return list of browsers whose cookies yt-dlp can read on this machine."""
    import subprocess
    candidates = {
        'chrome':  ['Google Chrome', 'chrome'],
        'firefox': ['Firefox', 'firefox'],
        'safari':  ['Safari'],
        'edge':    ['Microsoft Edge', 'edge'],
        'brave':   ['Brave Browser', 'brave'],
        'chromium':['Chromium', 'chromium'],
    }
    found = []
    system = platform.system()
    for browser, names in candidates.items():
        if system == 'Darwin':
            for name in names:
                app = Path(f'/Applications/{name}.app')
                if app.exists():
                    found.append(browser)
                    break
        elif system == 'Linux':
            for name in names:
                try:
                    subprocess.run(['which', name.lower()], capture_output=True, check=True)
                    found.append(browser)
                    break
                except subprocess.CalledProcessError:
                    pass
        elif system == 'Windows':
            import shutil
            for name in names:
                if shutil.which(name.lower()):
                    found.append(browser)
                    break
    return found


def download_content(url: str, download_type: str = 'video', quality: int = None,
                     download_folder: str = None, cookies_file: str = None,
                     browser_cookies: str = None):
    """Download video or audio. Returns True on success."""
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        show_ffmpeg_instructions()
        return False

    try:
        # Determine output directory
        if download_folder and os.path.isdir(download_folder) and os.access(download_folder, os.W_OK):
            temp_dir = Path(download_folder).resolve()
            is_custom_folder = True
        elif IS_CLOUD_DEPLOYMENT:
            temp_dir = CLOUD_TEMP_DIR
            is_custom_folder = False
        else:
            temp_dir = LOCAL_TEMP_DIR.resolve()
            is_custom_folder = False

        temp_dir.mkdir(parents=True, exist_ok=True)

        progress_bar = st.progress(0)
        status_text = st.empty()
        downloaded_file = None

        output_template = str(temp_dir / '%(title)s.%(ext)s')
        logger.info(f"Download dir: {temp_dir}")

        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'progress': True,
            'prefer_ffmpeg': True,
            'ignoreerrors': False,
            'nooverwrites': False,
            'skip_unavailable_fragments': True,
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retries': 3,
            'socket_timeout': 30,
            'extract_flat': False,
            # tv_embedded bypasses "sign in to confirm" bot check best
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv_embedded', 'ios', 'web'],
                }
            },
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                )
            },
        }

        # ── Cookie options (strongest bot-detection bypass) ──
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            logger.info(f"Using cookies file: {cookies_file}")
        elif browser_cookies:
            ydl_opts['cookiesfrombrowser'] = (browser_cookies,)
            logger.info(f"Using cookies from browser: {browser_cookies}")

        if ffmpeg_path != 'ffmpeg':
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        # Format selection
        if download_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            q = f'[height<={quality}]' if quality else ''
            format_selector = (
                f'best{q}[acodec!=none][vcodec!=none][ext=mp4]/'
                f'best{q}[acodec!=none][vcodec!=none]/'
                f'bestvideo{q}[vcodec!=none]+bestaudio[acodec!=none]/'
                f'bestvideo{q}[vcodec!=none]+bestaudio[acodec!=none][ext=m4a]/'
                f'best{q}[acodec!=none][vcodec!=none]'
            )
            ydl_opts.update({
                'format': format_selector,
                'merge_output_format': 'mp4',
            })

        def cleanup_temp():
            if is_custom_folder:
                return
            try:
                if downloaded_file and os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                if temp_dir.exists() and temp_dir != CLOUD_TEMP_DIR:
                    for f in temp_dir.glob('*'):
                        try:
                            f.unlink()
                        except Exception:
                            pass
                    try:
                        temp_dir.rmdir()
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")

        def progress_hook(d):
            nonlocal downloaded_file
            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    done = d.get('downloaded_bytes', 0)
                    if total:
                        pct = min(done / total, 1.0)
                        progress_bar.progress(pct)
                    fname = os.path.basename(d.get('filename', ''))
                    speed = d.get('_speed_str', '')
                    eta = d.get('_eta_str', '')
                    parts = [f"⏳ {fname}"]
                    if speed:
                        parts.append(f"🚀 {speed}")
                    if eta:
                        parts.append(f"⏱ ETA {eta}")
                    status_text.text("  |  ".join(parts))
                except Exception as e:
                    logger.warning(f"Progress hook error: {e}")
            elif d['status'] == 'finished':
                downloaded_file = d.get('filename', '')
                status_text.text(f"⚙️  Processing: {os.path.basename(downloaded_file)}")
                progress_bar.progress(1.0)

        ydl_opts['progress_hooks'] = [progress_hook]

        try:
            # ── Extract info first ──────────────────────────
            info_opts = {**ydl_opts, 'quiet': True, 'no_warnings': True}
            info = None
            info_clients = [
                ['tv_embedded', 'ios', 'web'],
                ['tv_embedded'],
                ['mweb'],
                ['ios'],
                ['web'],
            ]
            for clients in info_clients:
                try:
                    test_opts = {
                        **info_opts,
                        'extractor_args': {'youtube': {'player_client': clients}},
                    }
                    with yt_dlp.YoutubeDL(test_opts) as info_ydl:
                        info = info_ydl.extract_info(url, download=False)
                    break
                except Exception as e:
                    logger.warning(f"Info extract with {clients} failed: {e}")
                    if clients == info_clients[-1]:
                        err = str(e)
                        if 'Sign in' in err or 'bot' in err.lower():
                            st.error("🤖 YouTube is blocking this as a bot.")
                            st.warning(
                                "**Fix:** Expand **Advanced Settings** below, upload a "
                                "`cookies.txt` file exported from your browser, or pick "
                                "your browser to pass cookies automatically.\n\n"
                                "See [how to export cookies](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)."
                            )
                        else:
                            st.error(f"❌ Could not fetch video info: {e}")
                        logger.error(f"Info extraction: {e}")
                        return False

            if info is None:
                st.error("❌ Failed to fetch video information.")
                return False

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
            thumbnail = info.get('thumbnail')

            # ── Video preview card ──────────────────────────
            with st.container():
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                col_thumb, col_info = st.columns([1, 2])
                with col_thumb:
                    if thumbnail:
                        st.image(thumbnail, use_container_width=True)
                with col_info:
                    st.markdown(f"### {title}")
                    st.markdown(
                        f"**Channel:** {uploader}  \n"
                        f"**Duration:** {int(duration // 60)}:{int(duration % 60):02d}  \n"
                        f"**Type:** {'🎵 Audio (MP3)' if download_type == 'audio' else f'🎬 Video ({quality}p)' if quality else '🎬 Video (Best)'}"
                    )
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Download ────────────────────────────────────
            download_success = False
            st.markdown("**Downloading…**")

            q = f'[height<={quality}]' if quality else ''
            fallback_clients = [
                ['tv_embedded', 'ios', 'web'],
                ['tv_embedded'],
                ['android_embedded'],
                ['android_music'],
                ['mweb'],
                ['ios'],
            ]

            download_success = False
            errors = {}

            for clients in fallback_clients:
                client_name = '+'.join(clients)
                try:
                    opts = {
                        **ydl_opts,
                        'extractor_args': {'youtube': {'player_client': clients}},
                    }
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                    download_success = True
                    logger.info(f"Download succeeded with clients: {clients}")
                    break
                except Exception as e:
                    errors[client_name] = str(e)
                    logger.warning(f"Download with {client_name} failed: {e}")

            if not download_success:
                # Collect all unique error messages
                unique_errors = list(dict.fromkeys(errors.values()))
                last_error = unique_errors[-1] if unique_errors else ''
                is_bot_error = any(
                    kw in err for err in unique_errors
                    for kw in ('Sign in', 'bot', 'cookies', 'confirm your age', 'This video is unavailable')
                )

                st.error("❌ Download failed — YouTube blocked all attempts.")
                with st.expander("🔍 Show error details"):
                    for name, err in errors.items():
                        st.code(f"[{name}]  {err}", language=None)

                if is_bot_error:
                    st.warning(
                        "### 🤖 YouTube is detecting this as a bot request\n\n"
                        "This is very common on cloud/server deployments. "
                        "The fix is to provide your browser cookies:\n\n"
                        "**Step 1** — Install the "
                        "[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) "
                        "Chrome extension\n\n"
                        "**Step 2** — Go to [youtube.com](https://youtube.com) and make sure you're logged in\n\n"
                        "**Step 3** — Click the extension icon → **Export** → save as `cookies.txt`\n\n"
                        "**Step 4** — Upload that file using the **🍪 Cookies** upload above and try again"
                    )
                else:
                    st.info(f"Last error: `{last_error}`")
                    st.caption("💡 Possible fixes: check the URL is public, or update yt-dlp.")
                return False

            # ── Locate downloaded file ──────────────────────
            if not downloaded_file:
                exts = ['*.mp4', '*.webm', '*.mkv', '*.mp3', '*.m4a', '*.opus', '*.ogg', '*.flv']
                candidates = []
                for ext in exts:
                    candidates.extend(temp_dir.glob(ext))
                if not candidates:
                    candidates = [f for f in temp_dir.glob('*') if f.is_file()]
                if candidates:
                    latest = max(candidates, key=lambda p: p.stat().st_mtime)
                    downloaded_file = str(latest.resolve())

            if downloaded_file:
                downloaded_file = str(Path(downloaded_file).resolve())

            if downloaded_file and os.path.exists(downloaded_file):
                file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
                file_name = os.path.basename(downloaded_file)

                progress_bar.progress(1.0)
                status_text.empty()

                st.success(f"✅ Ready! **{file_name}** ({file_size_mb:.1f} MB)")

                with open(downloaded_file, 'rb') as fh:
                    file_data = fh.read()

                st.download_button(
                    label=f"⬇️  Save  {file_name}  ({file_size_mb:.1f} MB)",
                    data=file_data,
                    file_name=file_name,
                    mime='application/octet-stream',
                    use_container_width=True,
                )
                if is_custom_folder:
                    st.info(f"📁 Also saved to: `{os.path.dirname(downloaded_file)}`")
                return True

            if download_success:
                st.error("❌ Download finished but the file could not be located.")
            else:
                st.error("❌ Download failed.")
            return False

        finally:
            cleanup_temp()

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        logger.error(f"download_content error: {e}")
        return False


def main():
    st.set_page_config(
        page_title="YT Downloader",
        page_icon="🎥",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Inject CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Hero banner ──────────────────────────────────────────
    mode_label = "☁️ Cloud Mode" if IS_CLOUD_DEPLOYMENT else "💻 Local Mode"
    st.markdown(f"""
<div class="hero-banner">
    <h1>🎥 YouTube Downloader</h1>
    <p>Download videos or extract audio — fast & free</p>
    <span class="mode-badge">{mode_label}</span>
</div>
""", unsafe_allow_html=True)

    # ── Sidebar info ─────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ℹ️ About")
        st.markdown("""
This tool lets you download YouTube videos and audio directly from your browser.

**Supported formats**
- 🎬 MP4 Video (up to 1080p)
- 🎵 MP3 Audio (192 kbps)

**Notes**
- Large files may take a minute to process
- In cloud mode files are temporary; save them immediately after download
""")
        st.markdown("---")
        ffmpeg_ok = check_ffmpeg() is not None
        st.markdown(
            f"**FFmpeg:** {'✅ Available' if ffmpeg_ok else '❌ Not found'}"
        )
        st.markdown(
            f"**Deployment:** {'Cloud ☁️' if IS_CLOUD_DEPLOYMENT else 'Local 💻'}"
        )

    # ── Download form ─────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📥 Download Settings</div>', unsafe_allow_html=True)

    with st.form("download_form", clear_on_submit=False):
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
        )

        col1, col2 = st.columns(2)
        with col1:
            download_type = st.selectbox(
                "Type",
                ["video", "audio"],
                format_func=lambda x: "🎬 Video" if x == "video" else "🎵 Audio (MP3)",
            )
        with col2:
            if download_type == "video":
                quality_options = [None, 1080, 720, 480, 360, 240]
                quality = st.selectbox(
                    "Quality",
                    quality_options,
                    format_func=lambda x: "✨ Best available" if x is None else f"{x}p",
                )
            else:
                quality = None
                st.selectbox("Quality", ["192 kbps"], disabled=True, label_visibility="visible")

        # ── Cookies (cloud: always visible; local: in expander) ──
        st.markdown("---")
        cookies_file_upload = None
        browser_cookies = None
        download_folder = None

        if IS_CLOUD_DEPLOYMENT:
            # On cloud, cookies upload is the ONLY bypass — show it prominently
            st.markdown(
                "**🍪 YouTube Cookies** &nbsp; "
                "<span style='background:#ff4444;color:#fff;border-radius:4px;"
                "padding:2px 7px;font-size:0.75rem;font-weight:700'>REQUIRED if blocked</span>",
                unsafe_allow_html=True,
            )
            st.caption(
                "If you see a 'Sign in to confirm you're not a bot' error, "
                "export your YouTube cookies from your browser and upload the file below. "
                "Use the [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) "
                "Chrome extension or equivalent."
            )
            cookies_file_upload = st.file_uploader(
                "Upload cookies.txt (Netscape format)",
                type=["txt"],
                label_visibility="collapsed",
            )
        else:
            with st.expander("⚙️ Advanced Settings  *(fix bot errors / choose save folder)*"):
                st.markdown("**🍪 Cookies** *(needed if YouTube blocks the download)*")
                cookies_file_upload = st.file_uploader(
                    "Upload cookies.txt",
                    type=["txt"],
                    help="Export from your browser with a cookie exporter extension.",
                    label_visibility="collapsed",
                )

                available_browsers = get_available_browsers()
                if available_browsers:
                    browser_options = ["— don't use browser cookies —"] + available_browsers
                    browser_choice = st.selectbox(
                        "Or auto-read cookies from browser",
                        browser_options,
                        help="yt-dlp will read your browser's YouTube login cookies directly.",
                    )
                    if browser_choice != "— don't use browser cookies —":
                        browser_cookies = browser_choice
                else:
                    st.caption("No supported browsers detected on this machine.")

                st.markdown("**📁 Save Location**")
                download_folder_input = st.text_input(
                    "Folder path",
                    placeholder="Leave blank for temp location",
                    label_visibility="collapsed",
                )
                if download_folder_input.strip():
                    p = os.path.expanduser(download_folder_input.strip())
                    if os.path.isdir(p) and os.access(p, os.W_OK):
                        download_folder = p
                        st.caption(f"✅ Will save to: `{os.path.abspath(p)}`")
                    else:
                        st.caption("⚠️ Path not found or not writable — using temp location")

        submitted = st.form_submit_button("⬇️  Download", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Handle submission ─────────────────────────────────────
    if submitted:
        if not youtube_url.strip():
            st.warning("⚠️ Please enter a YouTube URL.")
        elif "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            st.warning("⚠️ URL does not look like a YouTube link. Please check and try again.")
        else:
            # Save uploaded cookies file to a temp path if provided
            cookies_file_path = None
            if cookies_file_upload is not None:
                cookies_tmp = Path("/tmp/yt_cookies.txt") if IS_CLOUD_DEPLOYMENT else Path("temp_cookies.txt")
                cookies_tmp.write_bytes(cookies_file_upload.read())
                cookies_file_path = str(cookies_tmp)

            with st.spinner("Fetching video info…"):
                success = download_content(
                    url=youtube_url.strip(),
                    download_type=download_type,
                    quality=quality,
                    download_folder=download_folder if not IS_CLOUD_DEPLOYMENT else None,
                    cookies_file=cookies_file_path,
                    browser_cookies=browser_cookies if not IS_CLOUD_DEPLOYMENT else None,
                )
            if success:
                st.button("🔄 Download Another", on_click=st.rerun, use_container_width=True)

    # ── Footer ───────────────────────────────────────────────
    st.markdown("""
<div class="footer">
    Built with ❤️ using <strong>Streamlit</strong> &amp; <strong>yt-dlp</strong> &nbsp;·&nbsp;
    For personal use only &nbsp;·&nbsp; Respect copyright laws
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
