import os
import yt_dlp
import streamlit as st
from pathlib import Path
import platform
import logging

# Configure logging
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
    except Exception as e:
        logger.warning(f"Could not get Downloads folder: {e}")
        return Path.home() / "Downloads"

def create_download_options(url: str, output_path: Path, download_type: str, quality: int = None) -> dict:
    """Create options for yt-dlp."""
    # Base options
    options = {
        'outtmpl': str(output_path / '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'quiet': False,
        'no_warnings': False,
        'verbose': True
    }

    # Format selection based on download type
    if download_type == 'audio':
        options.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:  # video
        if quality:
            options.update({
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]',
                'merge_output_format': 'mp4'
            })
        else:
            options.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                'merge_output_format': 'mp4'
            })

    return options

def download_content(url: str, output_path: str, download_type: str = 'video', quality: int = None):
    """Download video or audio content."""
    try:
        # Convert to Path object and create directory
        output_path = Path(output_path).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_hook(d):
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
                filename = os.path.basename(d.get('filename', ''))
                status_text.text(f"✅ Completed: {filename}")
                progress_bar.progress(1.0)

        # Get download options
        ydl_opts = create_download_options(url, output_path, download_type, quality)
        ydl_opts['progress_hooks'] = [progress_hook]

        # Perform download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First get video info
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            st.write(f"📥 Starting download for: {title}")
            
            # Then download
            error_code = ydl.download([url])
            
            if error_code != 0:
                raise Exception(f"Download failed with error code: {error_code}")

        # Verify download
        downloaded_files = list(output_path.glob(f"{title}.*"))
        if downloaded_files:
            st.success(f"✅ Successfully downloaded to: {output_path}")
            # Show file details
            with st.expander("Show file details"):
                for file in downloaded_files:
                    size = file.stat().st_size / (1024 * 1024)  # Convert to MB
                    st.write(f"📁 {file.name} ({size:.1f} MB)")
            return True
        else:
            raise Exception("No files were downloaded")

    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")
        return False

def get_folder_mac():
    """Get folder path on macOS using multiple methods."""
    try:
        # First try AppleScript
        folder_path = os.popen('osascript -e "choose folder with prompt "Select Download Folder:""').read().strip()
        if folder_path:
            # Convert macOS path format to regular path
            folder_path = folder_path.replace(':', '/')
            if folder_path.startswith('Macintosh HD/'):
                folder_path = '/' + folder_path[13:]
            return folder_path
    except:
        pass
    
    try:
        # Fallback to PyQt5
        from PyQt5.QtWidgets import QApplication, QFileDialog
        app = QApplication([])
        folder_path = QFileDialog.getExistingDirectory(
            None, 
            "Select Download Folder",
            str(Path.home()),
            QFileDialog.ShowDirsOnly
        )
        if folder_path:
            return folder_path
    except:
        pass
    
    # Final fallback to default Downloads folder
    return str(Path.home() / "Downloads")

def main():
    st.set_page_config(page_title="YouTube Downloader", page_icon="🎥")
    
    # Title and description
    st.title("🎥 YouTube Downloader")
    st.markdown("Download videos or extract audio from YouTube")
    
    # Create columns for input fields
    col1, col2 = st.columns([2, 1])
    
    with col1:
        youtube_url = st.text_input("🔗 Enter YouTube URL:")
    
    with col2:
        download_type = st.selectbox("📥 Download Type:", ["video", "audio"])
    
    # Quality selection (only for video)
    if download_type == "video":
        quality_options = [None, 240, 360, 480, 720, 1080]
        quality = st.selectbox(
            "🎬 Video Quality:", 
            quality_options,
            format_func=lambda x: "Best" if x is None else f"{x}p"
        )
    else:
        quality = None
    
    # Get default download path and add folder selection
    default_path = str(get_downloads_folder() / "YouTube Downloads")
    
    # Create two columns for path input and folder selection
    path_col, button_col = st.columns([3, 1])
    
    with path_col:
        output_directory = st.text_input("📁 Save to:", value=default_path)
    
    with button_col:
        if st.button("📂 Choose Folder"):
            try:
                if platform.system() == "Windows":
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()  # Hide the main window
                    root.wm_attributes('-topmost', 1)  # Bring the dialog to front
                    folder_path = filedialog.askdirectory()
                    if folder_path:  # If a folder was selected
                        output_directory = folder_path
                        st.session_state['output_directory'] = folder_path
                        st.experimental_rerun()
                elif platform.system() == "Darwin":  # macOS
                    folder_path = get_folder_mac()
                    if folder_path:
                        st.session_state['output_directory'] = folder_path
                        st.experimental_rerun()
                else:  # Linux
                    # Use zenity for Linux folder selection
                    folder_path = os.popen('zenity --file-selection --directory --title="Select Download Folder"').read().strip()
                    if folder_path:
                        output_directory = folder_path
                        st.session_state['output_directory'] = folder_path
                        st.experimental_rerun()
            except Exception as e:
                st.error(f"Could not open folder dialog: {e}")
    
    # Use saved directory from session state if available
    if 'output_directory' in st.session_state:
        output_directory = st.session_state['output_directory']
    
    # Show current save location
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
                if st.button("📂 Open Downloads Folder"):
                    try:
                        if platform.system() == "Windows":
                            os.startfile(output_directory)
                        elif platform.system() == "Darwin":  # macOS
                            os.system(f"open '{output_directory}'")
                        else:  # Linux
                            os.system(f"xdg-open '{output_directory}'")
                    except Exception as e:
                        st.error(f"Could not open folder: {e}")

if __name__ == "__main__":
    main()
