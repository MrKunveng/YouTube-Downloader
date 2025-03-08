import os
import streamlit as st
from pathlib import Path
import platform
import yt_dlp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_path(path: str) -> Path:
    """Validate and return a safe path for downloads."""
    try:
        # Use a relative path instead of home directory
        return Path("downloads")
    except Exception:
        return Path("downloads")

def check_ffmpeg():
    """Check if ffmpeg is installed and accessible."""
    try:
        if platform.system() == "Windows":
            # Check in current directory and PATH
            ffmpeg_paths = [
                Path.cwd() / "ffmpeg.exe",
                Path.cwd() / "ffmpeg" / "bin" / "ffmpeg.exe",
                Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe",  # Added home directory check
            ]
            for path in ffmpeg_paths:
                if path.exists():
                    return str(path)
            
            # Check if available in PATH
            import subprocess
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                return 'ffmpeg'
            except subprocess.CalledProcessError:
                return None
        else:
            # For Linux and macOS
            import subprocess
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                return 'ffmpeg'
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None
    except Exception:
        return None

def show_ffmpeg_instructions():
    """Show instructions for installing ffmpeg."""
    st.error("❌ FFmpeg is required but not found!")
    
    system = platform.system()
    if system == "Windows":
        st.markdown("""
        ### FFmpeg Installation Instructions for Windows:
        
        **Option 1: Direct Download**
        1. Download FFmpeg from [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)
        2. Extract the zip file
        3. Copy the `ffmpeg.exe` file from the `bin` folder to your YouTube Downloader folder
        
        **Option 2: Using Chocolatey**
        ```powershell
        choco install ffmpeg
        ```
        """)
    elif system == "Darwin":  # macOS
        st.markdown("""
        ### FFmpeg Installation Instructions for macOS:
        
        **Option 1: Using Homebrew (Recommended)**
        ```bash
        brew install ffmpeg
        ```
        
        **Option 2: Using MacPorts**
        ```bash
        sudo port install ffmpeg
        ```
        """)
    else:  # Linux
        st.markdown("""
        ### FFmpeg Installation Instructions for Linux:
        
        **For Ubuntu/Debian:**
        ```bash
        sudo apt update
        sudo apt install ffmpeg
        ```
        
        **For Fedora:**
        ```bash
        sudo dnf install ffmpeg
        ```
        
        **For Arch Linux:**
        ```bash
        sudo pacman -S ffmpeg
        ```
        """)
    
    st.markdown("""
    After installing:
    1. Close this application
    2. Restart your terminal/command prompt
    3. Run the application again
    """)
    st.stop()  # Stop the app here to prevent further execution

def download_content(url: str, output_path: str, download_type: str = 'video', quality: int = None):
    """Download video or audio content."""
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        show_ffmpeg_instructions()
        return False

    try:
        # Create a temporary directory for downloads
        temp_dir = Path("temp_downloads")
        temp_dir.mkdir(exist_ok=True)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        downloaded_file = None

        # Configure yt-dlp options with temporary directory
        ydl_opts = {
            'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress': True,
            'prefer_ffmpeg': True,
        }

        # Only set ffmpeg_location if it's a specific path, not just 'ffmpeg'
        if ffmpeg_path != 'ffmpeg':
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        # Configure format based on download type
        if download_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:  # video
            if quality:
                ydl_opts.update({
                    'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
                    'merge_output_format': 'mp4',
                })
            else:
                ydl_opts.update({
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                })

        def cleanup_temp_files():
            """Clean up temporary files after download"""
            try:
                if downloaded_file and os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                if temp_dir.exists():
                    for file in temp_dir.glob('*'):
                        file.unlink()
                    temp_dir.rmdir()
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")

        def progress_hook(d):
            nonlocal downloaded_file
            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total:
                        progress = min(downloaded / total, 1.0)
                        progress_bar.progress(progress)
                        filename = os.path.basename(d.get('filename', ''))
                        status_text.text(f"⏳ Downloading: {filename}")
                except Exception as e:
                    logger.warning(f"Progress calculation error: {e}")
            elif d['status'] == 'finished':
                downloaded_file = d.get('filename', '')
                filename = os.path.basename(downloaded_file)
                status_text.text(f"✅ Processing: {filename}")
                progress_bar.progress(1.0)

        ydl_opts['progress_hooks'] = [progress_hook]

        try:
            # Perform download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                st.write(f"📥 Starting download for: {title}")
                ydl.download([url])
                
                if downloaded_file and os.path.exists(downloaded_file):
                    file_size = os.path.getsize(downloaded_file) / (1024 * 1024)  # Convert to MB
                    
                    # Create download button
                    with open(downloaded_file, 'rb') as f:
                        file_data = f.read()
                    
                    st.download_button(
                        label=f"⬇️ Download {os.path.basename(downloaded_file)} ({file_size:.1f} MB)",
                        data=file_data,
                        file_name=os.path.basename(downloaded_file),
                        mime='application/octet-stream'
                    )
                    
                    return True
            
            return False

        finally:
            # Clean up temporary files
            cleanup_temp_files()

    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")
        return False

def main():
    st.set_page_config(page_title="YouTube Downloader", page_icon="🎥")
    
    # Title and description
    st.title("🎥 YouTube Downloader")
    st.markdown("""
    Download videos or extract audio from YouTube
    
    ℹ️ Files will be downloaded directly to your device
    """)
    
    # Input fields in a clean layout
    with st.form("download_form"):
        youtube_url = st.text_input("🔗 Enter YouTube URL:")
        
        col1, col2 = st.columns(2)
        with col1:
            download_type = st.selectbox("📥 Download Type:", ["video", "audio"])
        with col2:
            if download_type == "video":
                quality_options = [None, 240, 360, 480, 720, 1080]
                quality = st.selectbox(
                    "🎬 Video Quality:", 
                    quality_options,
                    format_func=lambda x: "Best" if x is None else f"{x}p"
                )
            else:
                quality = None
        
        submit_button = st.form_submit_button("⬇️ Download")
    
    if submit_button:
        if not youtube_url:
            st.error("⚠️ Please enter a YouTube URL")
        else:
            with st.spinner("Processing download..."):
                success = download_content(
                    youtube_url,
                    "temp_downloads",
                    download_type,
                    quality
                )
            
            if success:
                st.button("🔄 Download Another", on_click=st.rerun)

if __name__ == "__main__":
    main()
