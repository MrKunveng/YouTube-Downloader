import os
import yt_dlp
import streamlit as st
from pathlib import Path
import platform

# Configure basic logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_downloads_folder() -> Path:
    """Get the system's Downloads folder path."""
    try:
        if platform.system() == "Windows":
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                downloads_path = winreg.QueryValueEx(key, downloads_guid)[0]
            return Path(downloads_path)
        else:
            return Path.home() / "Downloads"
    except:
        return Path.home() / "Downloads"

def download_content(url: str, output_path: str, download_type: str = 'video', quality: int = None):
    """Download video or audio content."""
    try:
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'quiet': False
        }

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
                })
            else:
                ydl_opts.update({
                    'format': 'bestvideo+bestaudio/best',
                })

        # Add progress hook
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total:
                        progress = downloaded / total
                        progress_bar.progress(progress)
                        status_text.text(f"Downloading: {d.get('filename', '').split('/')[-1]}")
                except:
                    pass
            elif d['status'] == 'finished':
                status_text.text(f"Download completed: {d.get('filename', '').split('/')[-1]}")
                progress_bar.progress(1.0)

        ydl_opts['progress_hooks'] = [progress_hook]

        # Perform download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            st.write(f"Starting download for: {title}")
            ydl.download([url])
            
        st.success(f"✅ Successfully downloaded to: {output_path}")
        return True

    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")
        return False

# Streamlit UI
st.set_page_config(page_title="YouTube Downloader", page_icon="🎥")
st.title("🎥 YouTube Downloader")

# Input fields
youtube_url = st.text_input("Enter YouTube URL:")
download_type = st.selectbox("Select Type:", ["video", "audio"])
quality_options = [None, 240, 360, 480, 720, 1080]
quality = st.selectbox("Select Quality:", quality_options, 
                      format_func=lambda x: "Best" if x is None else f"{x}p") if download_type == "video" else None

# Get default download path
default_path = str(get_downloads_folder() / "YouTube Downloads")
output_directory = st.text_input("Save to:", value=default_path)

# Download button
if st.button("Download"):
    if not youtube_url:
        st.error("Please enter a YouTube URL")
    else:
        success = download_content(youtube_url, output_directory, download_type, quality)
        if success and platform.system() == "Windows":
            if st.button("Open Downloads Folder"):
                try:
                    os.startfile(output_directory)
                except Exception as e:
                    st.error(f"Could not open folder: {e}")
