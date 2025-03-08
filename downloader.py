import os
import streamlit as st
from pathlib import Path
import platform
import yt_dlp
import logging
import time

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
    # First check for ffmpeg
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        show_ffmpeg_instructions()
        return False

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
    
    # Add a loading message that shows while the app is waking up
    with st.spinner("🚀 App is starting up..."):
        time.sleep(0.1)  # Small delay to show the message during cold starts
    
    # Initialize session state for output directory
    default_path = str(validate_path(Path.home() / "Downloads" / "YouTube Downloads"))
    if 'output_directory' not in st.session_state:
        st.session_state['output_directory'] = default_path
    
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
    
    # Create two columns for path input and folder selection
    path_col, button_col = st.columns([3, 1])
    
    with path_col:
        # Display text input bound to session state
        user_input = st.text_input(
            "📁 Save to:",
            value=st.session_state['output_directory'],
            key="path_input"
        )
        # Validate the input path and update session state
        validated_path = str(validate_path(user_input))
        if validated_path != st.session_state['output_directory']:
            st.session_state['output_directory'] = validated_path
            # Optionally show a warning if path was adjusted
            if user_input != validated_path:
                st.warning(f"Adjusted path to: {validated_path}")
    
    with button_col:
        if st.button("📂 Choose Folder", key="choose_folder_btn"):
            folder_path = choose_folder()
            if folder_path:
                validated_folder = str(validate_path(folder_path))
                st.session_state['output_directory'] = validated_folder
                st.rerun()
    
    # Show current save location with path validation
    st.info(f"📂 Current save location: {st.session_state['output_directory']}")
    
    # Download button
    if st.button("⬇️ Download", key="main_download_btn"):
        if not youtube_url:
            st.error("⚠️ Please enter a YouTube URL")
        else:
            with st.spinner("Processing download..."):
                success = download_content(
                    youtube_url,
                    st.session_state['output_directory'],
                    download_type,
                    quality
                )
            
            if success:
                # Show open folder button
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("📂 Open Folder", key="open_folder_btn"):
                        try:
                            path = Path(st.session_state['output_directory'])
                            if platform.system() == "Windows":
                                os.startfile(str(path))  # Convert Path to string
                            elif platform.system() == "Darwin":  # macOS
                                os.system(f"open '{str(path)}'")  # Convert Path to string
                            else:  # Linux
                                os.system(f"xdg-open '{str(path)}'")  # Convert Path to string
                        except Exception as e:
                            st.error(f"Could not open folder: {e}")
                
                with col2:
                    if st.button("⬇️ Download Another", key="download_another_btn"):
                        st.rerun()

if __name__ == "__main__":
    main()
