import os
import time
from html import escape
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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

:root {
    --ink: #0E1116;          /* base — cool graphite, not pure black */
    --panel: #161A21;        /* raised surface */
    --panel-2: #1B212A;
    --line: #262C36;         /* hairline */
    --text: #E6E9EF;
    --muted: #8A93A2;
    --signal: #22C55E;       /* progress · ready · go */
    --signal-dim: #16A34A;
    --signal-glow: rgba(34, 197, 94, 0.25);
    --brand: #FF3B30;        /* YouTube mark and blocked states only */
    --warn: #F5A524;
    --sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    --display: 'Space Grotesk', 'IBM Plex Sans', sans-serif;
}

/* ── Base ── */
.stApp { background: var(--ink); }
html, body, [class*="css"] { font-family: var(--sans); color: var(--text); }
[data-testid="stMainBlockContainer"] { max-width: 800px; padding-top: 2rem; padding-bottom: 4rem; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"] { display: none; }

/* ── Header rail ── */
.rail {
    display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;
    padding: 0.8rem 1rem;
    border: 1px solid var(--line); border-radius: 12px;
    background: linear-gradient(180deg, var(--panel-2), var(--panel));
    margin-bottom: 1rem;
}
.rail-mark {
    width: 28px; height: 20px; border-radius: 6px;
    background: var(--brand); position: relative; flex: none;
}
.rail-mark::after {
    content: ''; position: absolute; left: 10px; top: 5px;
    border-left: 8px solid #fff;
    border-top: 5px solid transparent; border-bottom: 5px solid transparent;
}
.rail-name { font-family: var(--display); font-weight: 700; font-size: 1.05rem; letter-spacing: -0.01em; }
.rail-chips { margin-left: auto; display: flex; gap: 0.35rem; flex-wrap: wrap; }
.chip {
    font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.03em;
    color: var(--muted); border: 1px solid var(--line);
    border-radius: 999px; padding: 3px 9px; white-space: nowrap;
}
.chip-ok { color: var(--signal); border-color: rgba(34, 197, 94, 0.3); }
.chip-warn { color: var(--warn); border-color: rgba(245, 165, 36, 0.3); }
.chip-bad { color: var(--brand); border-color: rgba(255, 59, 48, 0.35); }

/* ── Stage cards: bordered containers holding an .eyebrow ── */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .eyebrow) {
    background: var(--panel);
    border: 1px solid var(--line) !important;
    border-radius: 12px;
    padding: 1.05rem 1.15rem 0.9rem;
}
.eyebrow {
    font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.16em;
    text-transform: uppercase; color: var(--muted);
    display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.15rem;
}
.eyebrow::after { content: ''; height: 1px; flex: 1; background: var(--line); }
.eyebrow-note { text-transform: none; letter-spacing: 0.02em; color: #6B7480; }

/* the form is the card — its inner block must not draw a second box */
[data-testid="stForm"] {
    background: var(--panel);
    border: 1px solid var(--line) !important;
    border-radius: 12px;
    padding: 1.05rem 1.15rem 0.9rem;
}
[data-testid="stForm"] [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .eyebrow) {
    background: transparent; border: none !important; padding: 0;
}

/* ── Inputs ── */
[data-testid="stTextInputRootElement"] {
    background: #0A0D12 !important;
    border: 1px solid var(--line) !important;
    border-radius: 9px !important;
}
[data-testid="stTextInputRootElement"]:focus-within {
    border-color: var(--signal) !important;
    box-shadow: 0 0 0 3px var(--signal-glow) !important;
}
[data-testid="stTextInputField"] { color: var(--text) !important; font-family: var(--mono) !important; font-size: 0.88rem !important; }
[data-testid="stTextInputField"]::placeholder { color: #5A626F !important; }

[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: #0A0D12 !important;
    border: 1px solid var(--line) !important;
    border-radius: 9px !important;
    color: var(--text) !important;
    font-size: 0.88rem !important;
}
[data-testid="stWidgetLabel"] p {
    font-family: var(--mono) !important; font-size: 0.7rem !important;
    letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted) !important;
}

/* ── Buttons ── */
[data-testid="stBaseButton-primaryFormSubmit"],
[data-testid="stBaseButton-primary"] {
    background: var(--signal) !important; color: #08130C !important;
    border: none !important; border-radius: 9px !important;
    font-family: var(--sans) !important; font-weight: 600 !important;
    letter-spacing: 0.01em !important; padding: 0.6rem 1.4rem !important;
    transition: background 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stBaseButton-primaryFormSubmit"]:hover,
[data-testid="stBaseButton-primary"]:hover {
    background: #2DD46B !important; box-shadow: 0 0 0 4px var(--signal-glow) !important;
}
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"],
.stDownloadButton button {
    background: transparent !important; color: var(--text) !important;
    border: 1px solid var(--line) !important; border-radius: 9px !important;
    font-weight: 500 !important; transition: border-color 0.15s ease;
}
[data-testid="stBaseButton-secondary"]:hover,
.stDownloadButton button:hover { border-color: var(--signal) !important; color: var(--signal) !important; }

/* ── Level meter (the signature element) ── */
[data-testid="stProgressBarTrack"] {
    background: #080A0E !important;
    border: 1px solid var(--line);
    border-radius: 5px; height: 12px !important;
    overflow: hidden; position: relative;
}
[data-testid="stProgressBarTrack"] > div {
    background: linear-gradient(90deg, var(--signal-dim), var(--signal)) !important;
    box-shadow: 0 0 14px var(--signal-glow);
    transition: transform 0.25s ease;
}
/* fixed segment gaps, so the fill reads as a level meter rather than a bar */
[data-testid="stProgressBarTrack"]::after {
    content: ''; position: absolute; inset: 0; pointer-events: none;
    background: repeating-linear-gradient(90deg, transparent 0 7px, var(--ink) 7px 9px);
}
[data-testid="stProgress"] [data-testid="stMarkdownContainer"] p {
    font-family: var(--mono) !important; font-size: 0.72rem !important;
    letter-spacing: 0.08em; color: var(--signal) !important; margin-bottom: 0.3rem !important;
}

/* ── Telemetry + data rows ── */
.telemetry {
    font-family: var(--mono); font-size: 0.72rem; color: var(--muted);
    letter-spacing: 0.02em; padding-top: 0.35rem;
}
.datarow { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.55rem; }
.data { font-family: var(--mono); font-size: 0.7rem; color: var(--muted);
        border: 1px solid var(--line); border-radius: 6px; padding: 3px 8px; }
.path-chip {
    font-family: var(--mono); font-size: 0.72rem; color: var(--signal);
    background: rgba(34, 197, 94, 0.07); border: 1px solid rgba(34, 197, 94, 0.22);
    border-radius: 6px; padding: 4px 9px; display: inline-block;
    word-break: break-all; margin-top: 0.5rem;
}
.title-lg { font-family: var(--display); font-weight: 700; font-size: 1.15rem; line-height: 1.3; margin: 0.15rem 0 0.1rem; }
.subtle { color: var(--muted); font-size: 0.85rem; }

/* ── Result card ── */
.result {
    border: 1px solid rgba(34, 197, 94, 0.3); border-left: 3px solid var(--signal);
    border-radius: 10px; background: rgba(34, 197, 94, 0.05);
    padding: 0.9rem 1rem; margin: 0.4rem 0 0.7rem;
}
.result-name { font-family: var(--display); font-weight: 600; font-size: 1rem; }

/* ── Expander ── */
[data-testid="stExpander"] details {
    background: transparent; border: 1px solid var(--line) !important; border-radius: 10px !important;
}
[data-testid="stExpander"] summary { font-family: var(--mono) !important; font-size: 0.75rem !important;
    letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted) !important; }

/* ── Alerts ── */
[data-testid="stAlertContainer"] { border-radius: 10px !important; font-size: 0.88rem; }

/* ── Images ── */
[data-testid="stImage"] img { border-radius: 8px; border: 1px solid var(--line); }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }

/* ── Focus + motion floor ── */
:focus-visible { outline: 2px solid var(--signal) !important; outline-offset: 2px !important; }
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
}

/* ── Footer ── */
.footer {
    font-family: var(--mono); font-size: 0.68rem; color: #5A626F;
    letter-spacing: 0.04em; text-align: center;
    padding-top: 1.6rem; margin-top: 2rem; border-top: 1px solid var(--line);
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--ink); }
::-webkit-scrollbar-thumb { background: var(--line); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #37404E; }
</style>
"""


def timecode(seconds):
    """Duration as m:ss, or h:mm:ss past an hour."""
    seconds = int(seconds or 0)
    h, m, sec = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def megabytes(n_bytes):
    return f"{n_bytes / 1048576:.1f} MB"


def telemetry(slot, text):
    """Monospace readout under the meter."""
    slot.markdown(f'<div class="telemetry">{escape(text)}</div>', unsafe_allow_html=True)


def eyebrow_html(label, note=""):
    suffix = f'<span class="eyebrow-note">{escape(note)}</span>' if note else ""
    return f'<div class="eyebrow">{escape(label)}{suffix}</div>'


def eyebrow(label, note=""):
    """Section label. Its presence also styles the container as a stage card."""
    st.markdown(eyebrow_html(label, note), unsafe_allow_html=True)


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

        progress_bar = None
        status_text = None
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
            # Let yt-dlp choose the best available client automatically
            # (older hardcoded clients like tv_embedded are removed in yt-dlp 2026+)
        }

        # ── Cookie options (strongest bot-detection bypass) ──
        # Priority: uploaded file → Streamlit secret (base64) → local file → browser
        resolved_cookies_file = None

        if cookies_file and os.path.exists(cookies_file):
            resolved_cookies_file = cookies_file
            logger.info("Using uploaded cookies file")
        else:
            # Try Streamlit secrets (base64-encoded)
            try:
                import base64
                encoded = st.secrets["YOUTUBE_COOKIES"]
                if encoded and encoded.strip():
                    secret_path = Path("/tmp/yt_secret_cookies.txt")
                    secret_path.write_bytes(base64.b64decode(encoded.strip()))
                    resolved_cookies_file = str(secret_path)
                    logger.info("Using cookies from Streamlit secrets (base64)")
            except Exception:
                pass

            # Fallback: local cookies.txt
            if not resolved_cookies_file:
                auto_cookies = Path("cookies.txt")
                if auto_cookies.exists():
                    resolved_cookies_file = str(auto_cookies.resolve())
                    logger.info("Auto-loaded local cookies.txt")

        if resolved_cookies_file:
            ydl_opts['cookiefile'] = resolved_cookies_file
        elif browser_cookies:
            ydl_opts['cookiesfrombrowser'] = (browser_cookies,)
            logger.info(f"Using browser cookies: {browser_cookies}")

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

        def stream_label(d):
            """Name the stream being fetched — a merged download pulls two."""
            info = d.get('info_dict') or {}
            vcodec, acodec = info.get('vcodec'), info.get('acodec')
            has_v = bool(vcodec) and vcodec != 'none'
            has_a = bool(acodec) and acodec != 'none'
            if has_v and not has_a:
                return '🎬 Video stream'
            if has_a and not has_v:
                return '🎵 Audio stream'
            return os.path.basename(d.get('filename', '')) or 'Media'

        def progress_hook(d):
            nonlocal downloaded_file
            if progress_bar is None:
                return
            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    done = d.get('downloaded_bytes', 0)
                    frag_i, frag_n = d.get('fragment_index'), d.get('fragment_count')
                    if total:
                        pct = min(done / total, 1.0)
                    elif frag_i and frag_n:
                        # Fragmented stream (DASH/HLS): no byte total, so count fragments
                        pct = min(frag_i / frag_n, 1.0)
                    else:
                        pct = 0.0

                    progress_bar.progress(pct, text=f"{stream_label(d)}  {pct * 100:.0f}%")

                    parts = []
                    if total:
                        parts.append(f"{done / 1048576:.1f} / {total / 1048576:.1f} MB")
                    elif frag_n:
                        parts.append(f"fragment {frag_i} of {frag_n}")
                    speed = d.get('_speed_str', '')
                    eta = d.get('_eta_str', '')
                    if speed:
                        parts.append(str(speed).strip())
                    if eta:
                        parts.append(f"ETA {str(eta).strip()}")
                    telemetry(status_text, "   ·   ".join(parts))
                except Exception as e:
                    logger.warning(f"Progress hook error: {e}")
            elif d['status'] == 'finished':
                downloaded_file = d.get('filename', '')
                progress_bar.progress(1.0, text=f"{stream_label(d)}  100%")
                telemetry(status_text, "stream complete")

        final_file = None

        def postprocessor_hook(d):
            # Fires after merge / mp3 extraction, so this is the path that survives.
            nonlocal final_file
            pp = d.get('postprocessor') or ''
            if d.get('status') == 'started' and status_text is not None:
                if 'Merger' in pp:
                    telemetry(status_text, "merging video + audio")
                elif 'ExtractAudio' in pp:
                    telemetry(status_text, "converting to MP3")
                else:
                    telemetry(status_text, (pp or 'processing').lower())
            if d.get('status') == 'finished':
                path = (d.get('info_dict') or {}).get('filepath')
                if path:
                    final_file = path

        ydl_opts['progress_hooks'] = [progress_hook]
        ydl_opts['postprocessor_hooks'] = [postprocessor_hook]

        try:
            # ── Extract info first ──────────────────────────
            info_opts = {**ydl_opts, 'quiet': True, 'no_warnings': True}
            info = None
            try:
                with st.spinner("Reading video details…"):
                    with yt_dlp.YoutubeDL(info_opts) as info_ydl:
                        info = info_ydl.extract_info(url, download=False)
            except Exception as e:
                err = str(e)
                logger.error(f"Info extraction failed: {e}")
                if 'Sign in' in err or 'bot' in err.lower() or 'cookies' in err.lower():
                    st.error("🤖 YouTube is blocking this request.")
                    st.warning(
                        "**Fix:** put a `cookies.txt` file next to the app, or pick your "
                        "browser under **⚙️ Advanced → Read cookies from browser**.\n\n"
                        "Export cookies with the "
                        "[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) "
                        "extension while logged into YouTube."
                    )
                else:
                    st.error(f"❌ Could not fetch video info: {e}")
                return False

            if info is None:
                st.error("❌ Failed to fetch video information.")
                return False

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
            thumbnail = info.get('thumbnail')

            # ── Video preview card ──────────────────────────
            if download_type == 'audio':
                target = 'MP3 · 192 kbps'
            else:
                target = f'MP4 · {quality}p' if quality else 'MP4 · best available'

            job = st.container(border=True)
            with job:
                stage_slot = st.empty()
            stage_slot.markdown(eyebrow_html("Downloading"), unsafe_allow_html=True)
            with job:
                col_thumb, col_info = st.columns([1, 2])
                with col_thumb:
                    if thumbnail:
                        st.image(thumbnail, width="stretch")
                with col_info:
                    st.markdown(
                        f'<div class="title-lg">{escape(title)}</div>'
                        f'<div class="subtle">{escape(uploader)}</div>'
                        f'<div class="datarow">'
                        f'<span class="data">{timecode(duration)}</span>'
                        f'<span class="data">{escape(target)}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # ── Download ────────────────────────────────────
            progress_bar = job.progress(0.0, text="starting…")
            status_text = job.empty()

            download_success = False
            download_error = ''
            started_at = time.time()
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(url, download=True)
                for req in (result or {}).get('requested_downloads') or []:
                    path = req.get('filepath') or req.get('_filename')
                    if path:
                        final_file = path
                        break
                download_success = True
            except Exception as e:
                download_error = str(e)
                logger.error(f"Download failed: {e}")

            if not download_success:
                is_bot_error = any(kw in download_error for kw in (
                    'Sign in', 'bot', 'cookies', 'confirm your age',
                ))
                stage_slot.markdown(eyebrow_html("Stopped"), unsafe_allow_html=True)
                st.error("Download failed.")
                with st.expander("Error details"):
                    st.code(download_error, language=None)
                if is_bot_error:
                    st.warning(
                        "🤖 YouTube is blocking this request.\n\n"
                        "**Fix:** put a `cookies.txt` file next to the app, or pick your "
                        "browser under **⚙️ Advanced → Read cookies from browser**."
                    )
                else:
                    st.caption("💡 Check the URL is public, or try a different video.")
                return False

            # ── Locate downloaded file ──────────────────────
            # The progress hook only sees the pre-merge / pre-transcode file, which
            # yt-dlp deletes; the postprocessor path is the one that survives.
            if final_file and os.path.exists(final_file):
                downloaded_file = final_file

            if not downloaded_file or not os.path.exists(downloaded_file):
                exts = ['*.mp4', '*.webm', '*.mkv', '*.mp3', '*.m4a', '*.opus', '*.ogg', '*.flv']
                skip = ('.part', '.ytdl', '.temp')
                candidates = []
                for ext in exts:
                    candidates.extend(temp_dir.glob(ext))
                if not candidates:
                    candidates = [f for f in temp_dir.glob('*') if f.is_file()]
                candidates = [
                    f for f in candidates
                    if f.is_file() and not f.name.endswith(skip)
                    and f.stat().st_mtime >= started_at - 1
                ]
                if candidates:
                    latest = max(candidates, key=lambda p: p.stat().st_mtime)
                    downloaded_file = str(latest.resolve())
                    logger.info(f"Located file via fallback scan: {downloaded_file}")

            if downloaded_file:
                downloaded_file = str(Path(downloaded_file).resolve())

            if downloaded_file and os.path.exists(downloaded_file):
                file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
                file_name = os.path.basename(downloaded_file)

                stage_slot.markdown(eyebrow_html("Downloaded"), unsafe_allow_html=True)
                progress_bar.progress(1.0, text="Downloaded  100%")
                status_text.empty()

                if is_custom_folder:
                    where = (f'<div class="path-chip">{escape(os.path.dirname(downloaded_file))}'
                             f'</div>')
                else:
                    where = ('<div class="subtle" style="margin-top:.5rem">'
                             'Held in a temporary folder — save it now to keep it.</div>')

                st.markdown(
                    f'<div class="result">'
                    f'<div class="result-name">{escape(file_name)}</div>'
                    f'<div class="datarow"><span class="data">{file_size_mb:.1f} MB</span>'
                    f'<span class="data">{escape(Path(file_name).suffix.lstrip(".").upper())}'
                    f'</span></div>{where}</div>',
                    unsafe_allow_html=True,
                )

                with open(downloaded_file, 'rb') as fh:
                    file_data = fh.read()

                st.download_button(
                    label="Save a copy…",
                    data=file_data,
                    file_name=file_name,
                    mime='application/octet-stream',
                    width="stretch",
                )
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


# ─────────────────────────────────────────────
# Save location
# ─────────────────────────────────────────────
def common_folders():
    """Standard destinations that exist on this machine."""
    home = Path.home()
    candidates = [
        ("Downloads", home / "Downloads"),
        ("Desktop", home / "Desktop"),
        ("Movies", home / "Movies"),
        ("Music", home / "Music"),
        ("Home", home),
    ]
    return [(label, str(path)) for label, path in candidates if path.is_dir()]


def pick_folder_dialog():
    """Open the OS's native folder picker. Returns a path, or None if cancelled."""
    import subprocess
    import shutil
    system = platform.system()
    try:
        if system == "Darwin":
            # `activate` pulls the dialog in front of the browser window
            result = subprocess.run(
                ["osascript", "-e", "activate", "-e",
                 'POSIX path of (choose folder with prompt "Choose download folder")'],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        elif system == "Windows":
            ps = ('Add-Type -AssemblyName System.Windows.Forms;'
                  '$d = New-Object System.Windows.Forms.FolderBrowserDialog;'
                  'if ($d.ShowDialog() -eq "OK") { $d.SelectedPath }')
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        else:
            for cmd in (["zenity", "--file-selection", "--directory"],
                        ["kdialog", "--getexistingdirectory", str(Path.home())]):
                if shutil.which(cmd[0]):
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                    break
    except Exception as e:
        logger.warning(f"Folder picker failed: {e}")
    return None


def render_save_location():
    """Save-location card. Returns the chosen folder, or None to use a temp dir."""
    folders = common_folders()
    paths = dict(folders)
    CUSTOM = "Custom folder…"
    options = [label for label, _ in folders] + [CUSTOM]

    if "save_folder" not in st.session_state:
        default = Path.home() / "Downloads"
        st.session_state.save_folder = str(default if default.is_dir() else Path.home())
    if "folder_choice" not in st.session_state:
        st.session_state.folder_choice = next(
            (lbl for lbl, path in folders if path == st.session_state.save_folder), CUSTOM
        )

    card = st.container(border=True)
    with card:
        eyebrow("Destination", "where files land")

    col_select, col_browse = card.columns([3, 1])

    # Browse is handled before the other widgets render: widget-backed session
    # state can't be written once its widget exists this run.
    with col_browse:
        browse = st.button("Browse…", width="stretch",
                           help="Open your system's folder picker")
    if browse:
        picked = pick_folder_dialog()
        if picked:
            picked = picked.rstrip(os.sep) or picked
            st.session_state.save_folder = picked
            st.session_state.folder_choice = next(
                (lbl for lbl, path in folders if path == picked), CUSTOM
            )
            st.session_state.custom_folder = picked
        else:
            st.toast("No folder selected")

    st.session_state.setdefault("custom_folder", st.session_state.save_folder)

    with col_select:
        choice = st.selectbox("Folder", options, key="folder_choice",
                              label_visibility="collapsed")

    if choice == CUSTOM:
        typed = card.text_input(
            "Folder path", key="custom_folder",
            placeholder=str(Path.home() / "Videos"), label_visibility="collapsed",
        )
        if typed.strip():
            st.session_state.save_folder = os.path.expanduser(typed.strip())
    else:
        st.session_state.save_folder = paths[choice]

    folder = st.session_state.save_folder
    if os.path.isdir(folder) and os.access(folder, os.W_OK):
        card.markdown(f'<div class="path-chip">{escape(folder)}</div>',
                      unsafe_allow_html=True)
    else:
        card.warning(f"{folder} isn't a writable folder. Files will go to a temp "
                     f"folder until you pick another one.")
        folder = None

    return folder


def main():
    st.set_page_config(
        page_title="YT Downloader",
        page_icon="🎥",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Inject CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Header rail: identity plus the status that used to hide in the sidebar ──
    ffmpeg_ok = check_ffmpeg() is not None
    try:
        has_secret = bool(st.secrets.get("YOUTUBE_COOKIES", "").strip())
    except Exception:
        has_secret = False
    has_cookies = has_secret or Path("cookies.txt").exists()

    chips = [
        ('chip-ok', 'ffmpeg ready') if ffmpeg_ok else ('chip-bad', 'ffmpeg missing'),
        ('chip-ok', 'cookies on') if has_cookies else ('chip-warn', 'no cookies'),
        ('chip', f'yt-dlp {yt_dlp.version.__version__}'),
        ('chip', 'cloud' if IS_CLOUD_DEPLOYMENT else 'local'),
    ]
    chip_html = "".join(
        f'<span class="chip {cls if cls != "chip" else ""}">{escape(text)}</span>'
        for cls, text in chips
    )
    st.markdown(
        f'<div class="rail"><span class="rail-mark"></span>'
        f'<span class="rail-name">YouTube Downloader</span>'
        f'<span class="rail-chips">{chip_html}</span></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### About")
        st.markdown(
            "Paste a link, pick a format, choose where it lands.\n\n"
            "Video saves as MP4, audio as 192 kbps MP3. "
            "Long videos take a moment to merge after the download finishes."
        )

    # ── Destination: a sticky preference, so it sits above the per-download inputs ──
    download_folder = render_save_location() if not IS_CLOUD_DEPLOYMENT else None

    # ── Source + output ───────────────────────────────────────
    with st.form("download_form", clear_on_submit=False, border=True):
        eyebrow("Source")
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=…",
            label_visibility="collapsed",
        )

        eyebrow("Output")
        col1, col2 = st.columns(2)
        with col1:
            download_type = st.selectbox(
                "Format",
                ["video", "audio"],
                format_func=lambda x: "Video · MP4" if x == "video" else "Audio · MP3",
            )
        with col2:
            if download_type == "video":
                quality = st.selectbox(
                    "Quality",
                    [None, 1080, 720, 480, 360, 240],
                    format_func=lambda x: "Best available" if x is None else f"{x}p",
                )
            else:
                quality = None
                st.markdown(
                    '<div style="padding-top:1.85rem">'
                    '<span class="data">192 kbps · fixed</span></div>',
                    unsafe_allow_html=True,
                )

        st.write("")
        submitted = st.form_submit_button("Download", type="primary", width="stretch")

    # ── Cookie source: only surfaces when YouTube blocks something ──
    browser_cookies = None
    if IS_CLOUD_DEPLOYMENT:
        st.caption("Cookies are configured on the server.")
    else:
        with st.expander("Advanced — cookie source"):
            st.caption(
                "A cookies.txt next to the app is picked up automatically. "
                "Reading from a signed-in browser works too, and only matters "
                "when YouTube blocks a download."
            )
            available_browsers = get_available_browsers()
            if available_browsers:
                browser_choice = st.selectbox(
                    "Read cookies from browser",
                    ["Off"] + available_browsers,
                )
                if browser_choice != "Off":
                    browser_cookies = browser_choice
            else:
                st.caption("No supported browsers found on this machine.")

    # ── Handle submission ─────────────────────────────────────
    if submitted:
        if not youtube_url.strip():
            st.warning("Paste a YouTube link to start.")
        elif "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            st.warning("That doesn't look like a YouTube link. Check the URL and try again.")
        else:
            success = download_content(
                url=youtube_url.strip(),
                download_type=download_type,
                quality=quality,
                download_folder=download_folder,
                cookies_file=None,
                browser_cookies=browser_cookies if not IS_CLOUD_DEPLOYMENT else None,
            )
            if success:
                st.button("Download another", on_click=st.rerun, width="stretch")

    # ── Footer ───────────────────────────────────────────────
    st.markdown(
        '<div class="footer">streamlit + yt-dlp · personal use · respect copyright</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
