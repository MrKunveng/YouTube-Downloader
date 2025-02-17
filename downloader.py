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
            # Ensure we're using the user's home directory Downloads folder
            return Path.home() / "Downloads" / "YouTube Downloads"
    except Exception as e:
        logger.warning(f"Could not get Downloads folder: {e}")
        return Path.home() / "Downloads" / "YouTube Downloads"

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
        # Convert to Path object and ensure it's absolute
        output_path = Path(output_path).expanduser().resolve()
        
        # Create directory with proper permissions
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {output_path}")
        except Exception as e:
            # If we can't create the specified directory, use Downloads folder
            output_path = Path.home() / "Downloads" / "YouTube Downloads"
            output_path.mkdir(parents=True, exist_ok=True)
            st.warning(f"⚠️ Using alternative location: {output_path}")
            logger.warning(f"Using alternative directory: {output_path}, Original error: {e}")

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best' if download_type == 'audio' else 'best',
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress': True,
            'prefer_ffmpeg': True,
            'ffmpeg_location': 'ffmpeg',  # Ensure ffmpeg is in PATH
        }

        # Add format-specific options
        if download_type == 'audio':
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif quality:
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]',
                'merge_output_format': 'mp4',
            })

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        downloaded_file = None

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
            try:
                # Get video info first
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                st.write(f"📥 Starting download for: {title}")
                
                # Perform the download
                ydl.download([url])
                
                # Verify the download
                if downloaded_file and os.path.exists(downloaded_file):
                    file_size = os.path.getsize(downloaded_file) / (1024 * 1024)  # Convert to MB
                    st.success(f"✅ Successfully downloaded: {os.path.basename(downloaded_file)} ({file_size:.1f} MB)")
                    st.info(f"📂 Saved to: {output_path}")
                    return True
                else:
                    raise Exception("File was not saved correctly")

            except Exception as e:
                logger.error(f"Download error: {e}")
                raise

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
    default_path = str(get_downloads_folder())
    
    # Create two columns for path input and folder selection
    path_col, button_col = st.columns([3, 1])
    
    with path_col:
        output_directory = st.text_input("📁 Save to:", value=default_path)
        # Validate the input path
        output_directory = str(validate_path(output_directory))
    
    with button_col:
        if st.button("📂 Choose Folder"):
            try:
                if platform.system() == "Windows":
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.wm_attributes('-topmost', 1)
                    folder_path = filedialog.askdirectory(
                        initialdir=str(Path.home() / "Downloads")
                    )
                    if folder_path:
                        output_directory = str(validate_path(folder_path))
                        st.session_state['output_directory'] = output_directory
                        st.experimental_rerun()
                elif platform.system() == "Darwin":  # macOS
                    folder_path = get_folder_mac()
                    if folder_path:
                        output_directory = str(validate_path(folder_path))
                        st.session_state['output_directory'] = output_directory
                        st.experimental_rerun()
                else:  # Linux
                    folder_path = os.popen('zenity --file-selection --directory --title="Select Download Folder"').read().strip()
                    if folder_path:
                        output_directory = str(validate_path(folder_path))
                        st.session_state['output_directory'] = output_directory
                        st.experimental_rerun()
            except Exception as e:
                st.error(f"Could not open folder dialog: {e}")
                logger.error(f"Folder dialog error: {e}")
    
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
            try:
                with st.spinner("Processing download..."):
                    success = download_content(youtube_url, output_directory, download_type, quality)
                
                if success:
                    # Show open folder button in a new container
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
                    
                    # Add download another button
                    with col2:
                        if st.button("⬇️ Download Another"):
                            st.experimental_rerun()
            
            except Exception as e:
                st.error(f"❌ Download failed: {str(e)}")
                logger.error(f"Download error: {e}")

if __name__ == "__main__":
    main()
