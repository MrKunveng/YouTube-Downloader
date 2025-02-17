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
        path = Path(path).resolve()
        # Ensure path is within user's home directory
        if not str(path).startswith(str(Path.home())):
            path = Path.home() / "Downloads" / "YouTube Downloads"
        return path
    except Exception:
        return Path.home() / "Downloads" / "YouTube Downloads"

def choose_folder():
    """Open a folder selection dialog based on the operating system."""
    try:
        if platform.system() == "Windows":
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            root.wm_attributes('-topmost', 1)  # Bring the dialog to the front
            folder_path = filedialog.askdirectory(initialdir=str(Path.home() / "Downloads"))
            return folder_path
        elif platform.system() == "Darwin":  # macOS
            folder_path = os.popen('osascript -e \'tell app "Finder" to POSIX path of (choose folder)\'').read().strip()
            return folder_path
        else:  # Linux
            folder_path = os.popen('zenity --file-selection --directory --title="Select Download Folder"').read().strip()
            return folder_path
    except Exception as e:
        st.error(f"Could not open folder dialog: {e}")
        return None

def download_content(url: str, output_path: str, download_type: str = 'video', quality: int = None):
    """Download video or audio content."""
    try:
        # Convert to Path object and ensure it exists
        output_path = Path(output_path).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        downloaded_file = None

        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress': True,
            'prefer_ffmpeg': True
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
                    'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]',
                    'merge_output_format': 'mp4',
                })
            else:
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                    'merge_output_format': 'mp4',
                })

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
                status_text.text(f"✅ Completed: {filename}")
                progress_bar.progress(1.0)

        ydl_opts['progress_hooks'] = [progress_hook]

        # Perform download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            st.write(f"📥 Starting download for: {title}")
            ydl.download([url])
            
            if downloaded_file and os.path.exists(downloaded_file):
                file_size = os.path.getsize(downloaded_file) / (1024 * 1024)  # Convert to MB
                st.success(f"✅ Successfully downloaded: {os.path.basename(downloaded_file)} ({file_size:.1f} MB)")
                return True
            
        return False

    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")
        return False

def main():
    st.set_page_config(page_title="YouTube Downloader", page_icon="🎥")
    
    # Title and description
    st.title("🎥 YouTube Downloader")
    st.markdown("Download videos or extract audio from YouTube")
    
    # Input fields
    youtube_url = st.text_input("🔗 Enter YouTube URL:")
    
    # Download type and quality selection
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
    
    # Get default download path
    default_path = str(validate_path(Path.home() / "Downloads" / "YouTube Downloads"))
    
    # Create two columns for path input and folder selection
    path_col, button_col = st.columns([3, 1])
    
    with path_col:
        output_directory = st.text_input("📁 Save to:", value=default_path)
        # Validate the input path
        output_directory = str(validate_path(output_directory))
    
    with button_col:
        if st.button("📂 Choose Folder"):
            folder_path = choose_folder()
            if folder_path:
                output_directory = str(validate_path(folder_path))
                st.session_state['output_directory'] = output_directory
                st.experimental_rerun()
    
    # Use saved directory from session state if available
    if 'output_directory' in st.session_state:
        output_directory = st.session_state['output_directory']
    
    # Show current save location with path validation
    output_directory = str(validate_path(output_directory))
    st.info(f"📂 Current save location: {output_directory}")
    
    # Download button
    if st.button("⬇️ Download"):
        if not youtube_url:
            st.error("⚠️ Please enter a YouTube URL")
        else:
            with st.spinner("Processing download..."):
                success = download_content(youtube_url, output_directory, download_type, quality)
            
            if success:
                # Show open folder button
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("📂 Open Folder"):
                        try:
                            if platform.system() == "Windows":
                                os.startfile(output_directory)
                            elif platform.system() == "Darwin":  # macOS
                                os.system(f"open '{output_directory}'")
                            else:  # Linux
                                os.system(f"xdg-open '{output_directory}'")
                        except Exception as e:
                            st.error(f"Could not open folder: {e}")
                
                with col2:
                    if st.button("⬇️ Download Another"):
                        st.experimental_rerun()

if __name__ == "__main__":
    main()
