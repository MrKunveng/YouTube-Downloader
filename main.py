import os
import streamlit as st
from pathlib import Path
import platform
import yt_dlp
import logging
from typing import Optional, Tuple
import time

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce logging verbosity
logger = logging.getLogger(__name__)

# Cloud deployment detection
IS_CLOUD_DEPLOYMENT = (
    os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false').lower() == 'true' or
    os.environ.get('SPACE_ID') is not None or
    os.environ.get('REPL_ID') is not None
)

# Initialize session state for caching
if 'ffmpeg_path' not in st.session_state:
    st.session_state.ffmpeg_path = None
if 'ffmpeg_checked' not in st.session_state:
    st.session_state.ffmpeg_checked = False


def check_ffmpeg() -> Optional[str]:
    """Check if ffmpeg is installed and accessible. Cached in session state."""
    if st.session_state.ffmpeg_checked:
        return st.session_state.ffmpeg_path
    
    try:
        import subprocess
        if platform.system() == "Windows":
            # Check common Windows locations
            ffmpeg_paths = [
                Path.cwd() / "ffmpeg.exe",
                Path.cwd() / "ffmpeg" / "bin" / "ffmpeg.exe",
                Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe",
            ]
            for path in ffmpeg_paths:
                if path.exists():
                    st.session_state.ffmpeg_path = str(path)
                    st.session_state.ffmpeg_checked = True
                    return st.session_state.ffmpeg_path
        
        # Check if available in PATH
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=2)
            st.session_state.ffmpeg_path = 'ffmpeg'
            st.session_state.ffmpeg_checked = True
            return st.session_state.ffmpeg_path
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
    except Exception as e:
        logger.warning(f"FFmpeg check error: {e}")
    
    st.session_state.ffmpeg_path = None
    st.session_state.ffmpeg_checked = True
    return None


def show_ffmpeg_instructions():
    """Show instructions for installing ffmpeg."""
    st.error("❌ FFmpeg is required but not found!")
    
    system = platform.system()
    if system == "Windows":
        st.markdown("""
        ### FFmpeg Installation Instructions for Windows:
        
        **Option 1: Using Chocolatey (Recommended)**
        ```powershell
        choco install ffmpeg
        ```
        
        **Option 2: Direct Download**
        1. Download from [ffmpeg.org](https://www.gyan.dev/ffmpeg/builds/)
        2. Extract and add to PATH
        """)
    elif system == "Darwin":  # macOS
        st.markdown("""
        ### FFmpeg Installation Instructions for macOS:
        
        **Using Homebrew (Recommended)**
        ```bash
        brew install ffmpeg
        ```
        """)
    else:  # Linux
        st.markdown("""
        ### FFmpeg Installation Instructions for Linux:
        
        **Ubuntu/Debian:**
        ```bash
        sudo apt update && sudo apt install ffmpeg
        ```
        
        **Fedora:**
        ```bash
        sudo dnf install ffmpeg
        ```
        
        **Arch Linux:**
        ```bash
        sudo pacman -S ffmpeg
        ```
        """)
    st.stop()


def get_download_folder(download_folder: Optional[str]) -> Tuple[Path, bool]:
    """Get and validate download folder path."""
    if download_folder and os.path.exists(download_folder) and os.access(download_folder, os.W_OK):
        return Path(download_folder).resolve(), True
    return Path("temp_downloads").resolve(), False


def build_format_selector(download_type: str, quality: Optional[int]) -> str:
    """Build optimized format selector string."""
    if download_type == 'audio':
        return 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best'
    
    # Video format selector - optimized for speed
    if quality:
        return (
            f'best[height<={quality}][acodec!=none][vcodec!=none][ext=mp4]/'
            f'best[height<={quality}][acodec!=none][vcodec!=none]/'
            f'bestvideo[height<={quality}]+bestaudio/'
            f'best[height<={quality}]'
        )
    else:
        return (
            'best[acodec!=none][vcodec!=none][ext=mp4]/'
            'best[acodec!=none][vcodec!=none]/'
            'bestvideo+bestaudio/best'
        )


def find_downloaded_file(directory: Path, extensions: list) -> Optional[Path]:
    """Efficiently find the most recently downloaded file."""
    try:
        files = []
        for ext in extensions:
            files.extend(directory.glob(ext))
        
        if files:
            return max(files, key=lambda p: p.stat().st_mtime)
        
        # Fallback: check all files
        all_files = [f for f in directory.glob('*') if f.is_file()]
        return max(all_files, key=lambda p: p.stat().st_mtime) if all_files else None
    except Exception as e:
        logger.warning(f"File search error: {e}")
        return None


def download_content(
    url: str,
    download_type: str = 'video',
    quality: Optional[int] = None,
    download_folder: Optional[str] = None
) -> bool:
    """Download video or audio content with optimized performance."""
    # Check ffmpeg once (cached)
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        show_ffmpeg_instructions()
        return False

    try:
        temp_dir, is_custom_folder = get_download_folder(download_folder)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # UI elements
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            info_placeholder = st.empty()

        downloaded_file = None
        last_update_time = time.time()

        # Optimized yt-dlp options
        ydl_opts = {
            'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
            'quiet': True,  # Reduce output for performance
            'no_warnings': True,
            'progress_hooks': [],
            'prefer_ffmpeg': True,
            'skip_unavailable_fragments': True,
            'ignore_no_formats_error': False,
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retries': 3,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                }
            },
        }

        if ffmpeg_path != 'ffmpeg':
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        # Configure format
        format_selector = build_format_selector(download_type, quality)
        
        if download_type == 'audio':
            ydl_opts.update({
                'format': format_selector,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({
                'format': format_selector,
                'merge_output_format': 'mp4',
            })

        # Progress hook - throttled updates for better performance
        def progress_hook(d):
            nonlocal downloaded_file, last_update_time
            current_time = time.time()
            
            if d['status'] == 'downloading':
                # Throttle UI updates to every 0.5 seconds
                if current_time - last_update_time < 0.5:
                    return
                last_update_time = current_time
                
                try:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total and total > 0:
                        progress = min(downloaded / total, 1.0)
                        progress_bar.progress(progress)
                        # Show speed if available
                        speed = d.get('speed', 0)
                        if speed:
                            speed_mb = speed / (1024 * 1024)
                            status_text.text(f"⏳ Downloading... {speed_mb:.1f} MB/s")
                        else:
                            status_text.text("⏳ Downloading...")
                except Exception:
                    pass
            elif d['status'] == 'finished':
                downloaded_file = d.get('filename', '')
                status_text.text("✅ Processing...")
                progress_bar.progress(1.0)

        ydl_opts['progress_hooks'] = [progress_hook]

        # Single-pass download (extract info and download in one go)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Quick info extraction for title display
                try:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Video')
                    info_placeholder.info(f"📥 **{title[:60]}...**" if len(title) > 60 else f"📥 **{title}**")
                except Exception:
                    info_placeholder.info("📥 Starting download...")
                
                # Perform download
                status_text.text("⏳ Starting download...")
                ydl.download([url])
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download error: {error_msg}")
            
            # Single optimized fallback attempt
            if "format" in error_msg.lower() or "unavailable" in error_msg.lower():
                status_text.text("🔄 Trying alternative format...")
                try:
                    fallback_opts = ydl_opts.copy()
                    fallback_opts['format'] = 'bestvideo+bestaudio/best/worst'
                    fallback_opts['ignore_no_formats_error'] = True
                    
                    with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                        fallback_ydl.download([url])
                except Exception as fallback_e:
                    st.error(f"❌ Download failed: {str(fallback_e)[:200]}")
                    return False
            else:
                st.error(f"❌ Download failed: {error_msg[:200]}")
                return False

        # Find downloaded file efficiently
        if not downloaded_file:
            extensions = ['*.mp4', '*.webm', '*.mkv', '*.mp3', '*.m4a', '*.opus']
            found_file = find_downloaded_file(temp_dir, extensions)
            if found_file:
                downloaded_file = str(found_file.resolve())

        if downloaded_file and os.path.exists(downloaded_file):
            file_size = os.path.getsize(downloaded_file) / (1024 * 1024)
            file_name = os.path.basename(downloaded_file)
            
            # Success UI
            progress_container.empty()
            st.success("✅ Download completed!")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(f"📄 **{file_name}** ({file_size:.1f} MB)")
                if is_custom_folder:
                    st.caption(f"💾 Saved to: {temp_dir}")
            
            with col2:
                # Use streaming for large files
                try:
                    with open(downloaded_file, 'rb') as f:
                        file_data = f.read()
                    st.download_button(
                        label="⬇️ Download File",
                        data=file_data,
                        file_name=file_name,
                        mime='application/octet-stream',
                        use_container_width=True
                    )
                except Exception as e:
                    logger.error(f"Download button error: {e}")
                    st.error("Could not create download button")
            
            return True
        else:
            st.error("❌ Download completed but file not found.")
            return False

    except Exception as e:
        st.error(f"❌ Download failed: {str(e)[:200]}")
        logger.error(f"Download error: {e}")
        return False


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="YouTube Downloader",
        page_icon="🎥",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stProgress > div > div > div {
        background-color: #1f77b4;
    }
    h1 {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("🎥 YouTube Downloader")
    st.markdown("---")
    
    # Mode indicator
    if IS_CLOUD_DEPLOYMENT:
        st.caption("☁️ Cloud Mode")
    else:
        st.caption("💻 Local Mode")
    
    # Download folder selection (local mode only)
    download_folder = None
    if not IS_CLOUD_DEPLOYMENT:
        with st.expander("📁 Download Settings", expanded=False):
            common_folders = {
                "📁 Downloads": os.path.expanduser("~/Downloads"),
                "🖥️ Desktop": os.path.expanduser("~/Desktop"),
                "📄 Documents": os.path.expanduser("~/Documents"),
            }
            
            # Quick select buttons
            cols = st.columns(3)
            for i, (name, path) in enumerate(common_folders.items()):
                with cols[i]:
                    if st.button(name, use_container_width=True):
                        if os.path.exists(path) and os.access(path, os.W_OK):
                            st.session_state.selected_folder = path
                            st.rerun()
            
            # Manual input
            folder_input = st.text_input(
                "Custom folder path:",
                value=st.session_state.get('selected_folder', ''),
                placeholder="Leave empty for temporary location"
            )
            
            if folder_input:
                normalized = os.path.expanduser(folder_input.strip())
                normalized = os.path.normpath(normalized)
                
                if os.path.exists(normalized) and os.path.isdir(normalized):
                    if os.access(normalized, os.W_OK):
                        download_folder = normalized
                        st.session_state.selected_folder = normalized
                        st.success(f"✅ Using: {normalized}")
                    else:
                        st.error("❌ No write permission")
                else:
                    st.error("❌ Folder does not exist")
            else:
                st.session_state.selected_folder = ""
                st.caption("💡 Files will be temporarily stored")
    
    # Main download form
    st.markdown("### Download Video or Audio")
    
    with st.form("download_form", clear_on_submit=True):
        youtube_url = st.text_input(
            "🔗 YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            download_type = st.selectbox(
                "📥 Type:",
                ["video", "audio"],
                help="Download video or extract audio only"
            )
        
        with col2:
            if download_type == "video":
                quality = st.selectbox(
                    "🎬 Quality:",
                    [None, 1080, 720, 480, 360, 240],
                    format_func=lambda x: "Best Available" if x is None else f"{x}p",
                    help="Select video quality"
                )
            else:
                quality = None
                st.caption("Audio: 192 kbps MP3")
        
        submit_button = st.form_submit_button(
            "⬇️ Download",
            use_container_width=True,
            type="primary"
        )
    
    # Handle download
    if submit_button:
        if not youtube_url or 'youtube.com' not in youtube_url and 'youtu.be' not in youtube_url:
            st.error("⚠️ Please enter a valid YouTube URL")
        else:
            with st.spinner("Initializing..."):
                success = download_content(
                    youtube_url,
                    download_type,
                    quality,
                    download_folder
                )
            
            if success:
                st.balloons()
                if st.button("🔄 Download Another", use_container_width=True):
                    st.rerun()


if __name__ == "__main__":
    main()
