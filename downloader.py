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
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                downloads_path = winreg.QueryValueEx(key, downloads_guid)[0]
            return Path(downloads_path)
        except:
            return Path.home() / "Downloads"
    else:
        return Path.home() / "Downloads"

class YouTubeDownloader:
    def __init__(self, output_path: Optional[str] = None):
        """Initialize downloader with optional output path."""
        self.output_path = Path(output_path) if output_path else get_downloads_folder() / "YouTube Downloads"
        self._ensure_output_directory()
        # Log the actual output path
        logger.info(f"Files will be saved to: {self.output_path.absolute()}")
    
    def _ensure_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        try:
            self.output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified directory: {self.output_path}")
        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            raise
    
    def _get_ydl_opts(self, download_type: SUPPORTED_DOWNLOAD_TYPES, 
                      quality: Optional[int] = None, 
                      is_playlist: bool = False) -> dict:
        """Configure yt-dlp options based on download parameters."""
        # Create full absolute path for output
        output_path = str(self.output_path.absolute())
        
        # Define output template
        if is_playlist:
            template = os.path.join(output_path, '%(playlist_title)s', '%(title)s.%(ext)s')
        else:
            template = os.path.join(output_path, '%(title)s.%(ext)s')
        
        opts = {
            'outtmpl': template,  # Use the full path template
            'ignoreerrors': True,
            'quiet': False,
            'progress': True,
            'overwrites': True,
            'verbose': True,
            'no_warnings': False,
            'format_sort': ['res:1080'],  # Prefer 1080p when available
            'merge_output_format': 'mp4'  # Force output to mp4
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
            if quality:
                opts.update({
                    'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]',
                })
            else:
                opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                })
        
        return opts

    def download(self, url: str, download_type: SUPPORTED_DOWNLOAD_TYPES,
                quality: Optional[int] = None) -> None:
        """Download video or playlist."""
        is_playlist = "playlist" in url
        downloaded_files = []
        
        try:
            # First extract info without downloading
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
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
                elif d['status'] == 'finished':
                    if 'filename' in d:
                        file_path = Path(d['filename'])
                        downloaded_files.append(file_path)
                        st.write(f"✅ Saved: {file_path.name}")
            
            ydl_opts = self._get_ydl_opts(download_type, quality, is_playlist)
            ydl_opts['progress_hooks'] = [progress_hook]
            
            # Perform the download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([url])
                
                if error_code != 0:
                    raise Exception("Download failed with error code: " + str(error_code))
            
            progress_bar.progress(1.0)
            
            # Verify downloads and show results
            if downloaded_files:
                st.success(f"✅ Successfully downloaded: {title}")
                st.info(f"📂 Files saved to: {self.output_path.absolute()}")
                
                # Verify files exist
                existing_files = [f for f in downloaded_files if f.exists()]
                with st.expander("Show downloaded files"):
                    for file in existing_files:
                        st.write(f"- {file.name} ({self._get_file_size(file)})")
                
                if len(existing_files) != len(downloaded_files):
                    st.warning("⚠️ Some files may not have saved correctly")
            else:
                st.warning("⚠️ No files were saved")
                logger.warning(f"No files saved for URL: {url}")
        
        except Exception as e:
            logger.error(f"Download error: {e}")
            st.error(f"❌ Download failed: {str(e)}")
            raise

    def _get_file_size(self, file_path: Path) -> str:
        """Get human-readable file size."""
        size_bytes = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} GB"

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
                try:
                    downloader = YouTubeDownloader(output_directory)
                    downloader.download(youtube_url, download_type, quality)
                    st.session_state.download_completed = True
                    st.session_state.last_download_path = output_directory
                except Exception as e:
                    st.error(f"❌ Error during download: {str(e)}")
                    logger.exception("Download failed")

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
