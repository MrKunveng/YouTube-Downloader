import os
import yt_dlp
import streamlit as st
from typing import Optional, Literal
import logging
from pathlib import Path
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_DOWNLOAD_TYPES = Literal["video", "audio"]
DEFAULT_AUDIO_QUALITY = "192"
VALID_VIDEO_QUALITIES = [None, 240, 360, 480, 720, 1080, 1440, 2160]

def get_downloads_folder() -> Path:
    """Get the system's Downloads folder path."""
    if platform.system() == "Windows":
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            downloads_path = winreg.QueryValueEx(key, downloads_guid)[0]
        return Path(downloads_path)
    else:
        return Path.home() / "Downloads"

class YouTubeDownloader:
    def __init__(self, output_path: Optional[str] = None):
        """Initialize downloader with optional output path."""
        self.output_path = Path(output_path) if output_path else get_downloads_folder() / "YouTube Downloads"
        self._ensure_output_directory()
    
    def _ensure_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def _get_ydl_opts(self, download_type: SUPPORTED_DOWNLOAD_TYPES, 
                      quality: Optional[int] = None, 
                      is_playlist: bool = False) -> dict:
        """Configure yt-dlp options based on download parameters."""
        template = '%(playlist)s/%(title)s.%(ext)s' if is_playlist else '%(title)s.%(ext)s'
        opts = {
            'outtmpl': str(self.output_path / template),
            'ignoreerrors': True,
            'quiet': False,
            'progress': True
        }

        if download_type == 'audio':
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': DEFAULT_AUDIO_QUALITY,
                }],
            })
        else:  # video
            format_str = (f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
                         if quality else 'bestvideo+bestaudio/best')
            opts.update({'format': format_str})
        
        return opts

    def download(self, url: str, download_type: SUPPORTED_DOWNLOAD_TYPES,
                quality: Optional[int] = None) -> None:
        """Download video or playlist."""
        is_playlist = "playlist" in url
        try:
            with yt_dlp.YoutubeDL(self._get_ydl_opts(download_type, quality, is_playlist)) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                
                st.write(f"⏳ Downloading: {title}")
                progress_bar = st.progress(0)
                
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        try:
                            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                            downloaded = d.get('downloaded_bytes', 0)
                            if total:
                                progress = downloaded / total
                                progress_bar.progress(progress)
                        except Exception as e:
                            logger.warning(f"Progress calculation error: {e}")
                
                ydl_opts = self._get_ydl_opts(download_type, quality, is_playlist)
                ydl_opts['progress_hooks'] = [progress_hook]
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_with_progress:
                    ydl_with_progress.download([url])
                
                progress_bar.progress(1.0)
                st.success(f"✅ Successfully downloaded: {title}")
        
        except Exception as e:
            logger.error(f"Download error: {e}")
            st.error(f"❌ Download failed: {str(e)}")

def create_streamlit_ui():
    """Create the Streamlit user interface."""
    st.set_page_config(
        page_title="YouTube Downloader",
        page_icon="🎥",
        layout="wide"
    )
    
    st.title("🎥 YouTube Downloader")
    st.markdown("---")

    # Create session state for tracking download completion
    if 'download_completed' not in st.session_state:
        st.session_state.download_completed = False
        st.session_state.last_download_path = None

    with st.form("download_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            youtube_url = st.text_input("🔗 YouTube URL (video or playlist):")
            download_type = st.selectbox(
                "📥 Download Type:",
                options=["video", "audio"],
                format_func=lambda x: x.title()
            )
        
        with col2:
            # Get default downloads path
            default_path = str(get_downloads_folder() / "YouTube Downloads")
            output_directory = st.text_input(
                "📁 Output Directory:",
                value=default_path,
                help="Files will be saved in your Downloads folder by default"
            )
            quality = (st.selectbox("🎬 Video Quality:", VALID_VIDEO_QUALITIES,
                                  format_func=lambda x: f"{x}p" if x else "Best")
                      if download_type == "video" else None)
        
        # Add information about save location
        st.info(f"📂 Files will be saved to: {output_directory}")
        
        submit = st.form_submit_button("⬇️ Download")
        
        if submit:
            if not youtube_url:
                st.error("⚠️ Please enter a valid YouTube URL.")
            else:
                downloader = YouTubeDownloader(output_directory)
                downloader.download(youtube_url, download_type, quality)
                st.session_state.download_completed = True
                st.session_state.last_download_path = output_directory

    # Open folder button outside the form
    if st.session_state.download_completed:
        if st.button("📂 Open Downloads Folder"):
            try:
                output_path = st.session_state.last_download_path
                if platform.system() == "Windows":
                    os.startfile(output_path)
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open '{output_path}'")
                else:  # Linux
                    os.system(f"xdg-open '{output_path}'")
            except Exception as e:
                st.error(f"Could not open folder: {e}")

if __name__ == "__main__":
    create_streamlit_ui()
