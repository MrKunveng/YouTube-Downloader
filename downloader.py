import os
import yt_dlp
import streamlit as st
from typing import Optional, Literal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_DOWNLOAD_TYPES = Literal["video", "audio"]
DEFAULT_AUDIO_QUALITY = "192"
VALID_VIDEO_QUALITIES = [None, 240, 360, 480, 720, 1080, 1440, 2160]

class YouTubeDownloader:
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
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
            output_directory = st.text_input(
                "📁 Output Directory:",
                value=os.getcwd()
            )
            quality = (st.selectbox("🎬 Video Quality:", VALID_VIDEO_QUALITIES,
                                  format_func=lambda x: f"{x}p" if x else "Best")
                      if download_type == "video" else None)
        
        submit = st.form_submit_button("⬇️ Download")
        
        if submit:
            if not youtube_url:
                st.error("⚠️ Please enter a valid YouTube URL.")
                return
            
            downloader = YouTubeDownloader(output_directory)
            downloader.download(youtube_url, download_type, quality)

if __name__ == "__main__":
    create_streamlit_ui()
