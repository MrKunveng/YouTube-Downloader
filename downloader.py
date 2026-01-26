import os
import streamlit as st
from pathlib import Path
import platform
import yt_dlp
import logging

# Configure logging for cloud environment
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cloud deployment configuration
# Detects if running in cloud (Streamlit Cloud, Hugging Face Spaces, Replit, etc.)
IS_CLOUD_DEPLOYMENT = (
    os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false').lower() == 'true' or
    os.environ.get('SPACE_ID') is not None or  # Hugging Face Spaces
    os.environ.get('REPL_ID') is not None  # Replit
)

def validate_path(path: str) -> Path:
    """Validate and return a safe path for downloads."""
    try:
        # In cloud environment, always use temp directory
        if IS_CLOUD_DEPLOYMENT:
            return Path("/tmp")
        # Use a relative path instead of home directory for local
        return Path("downloads")
    except Exception:
        return Path("downloads")

def check_ffmpeg():
    """Check if ffmpeg is installed and accessible."""
    try:
        # In cloud environment, ffmpeg should be available via packages.txt
        if IS_CLOUD_DEPLOYMENT:
            import subprocess
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                return 'ffmpeg'
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None
        
        # Local environment checks
        if platform.system() == "Windows":
            # Check in current directory and PATH
            ffmpeg_paths = [
                Path.cwd() / "ffmpeg.exe",
                Path.cwd() / "ffmpeg" / "bin" / "ffmpeg.exe",
                Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe",
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
    if IS_CLOUD_DEPLOYMENT:
        st.error("❌ FFmpeg is not available in the cloud environment. Please contact support.")
        return
    
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

def select_best_format_with_audio(formats, quality=None):
    """Manually select the best format that has both video and audio."""
    # Filter formats that have both video and audio
    combined_formats = [
        f for f in formats 
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none'
    ]
    
    if not combined_formats:
        return None
    
    # Filter by quality if specified
    if quality:
        quality_formats = [
            f for f in combined_formats 
            if f.get('height') and f.get('height') <= quality
        ]
        if quality_formats:
            combined_formats = quality_formats
    
    # Sort by height (quality) descending, then by filesize
    combined_formats.sort(
        key=lambda x: (
            x.get('height', 0) or 0,
            x.get('filesize', 0) or 0
        ),
        reverse=True
    )
    
    return combined_formats[0] if combined_formats else None

def download_content(url: str, output_path: str, download_type: str = 'video', quality: int = None, download_folder: str = None):
    """Download video or audio content."""
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        show_ffmpeg_instructions()
        return False

    try:
        # Use selected download folder or default to temp_downloads
        if download_folder and os.path.exists(download_folder) and os.access(download_folder, os.W_OK):
            # Use absolute path for download folder
            temp_dir = Path(download_folder).resolve()
            is_custom_folder = True
        else:
            # Use absolute path for temp directory
            temp_dir = Path("temp_downloads").resolve()
            is_custom_folder = False
        
        # Ensure directory exists
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        downloaded_file = None

        # Configure yt-dlp options with improved settings for better compatibility
        # Use absolute path for output template
        output_template = str(temp_dir / '%(title)s.%(ext)s')
        logger.info(f"Download location: {temp_dir}")
        logger.info(f"Output template: {output_template}")
        if is_custom_folder:
            st.info(f"📁 Files will be saved to: {temp_dir}")
        
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'progress': True,
            'prefer_ffmpeg': True,
            'ignoreerrors': False,
            'nooverwrites': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'skip_unavailable_fragments': True,
            'ignore_no_formats_error': False,  # Changed to False to catch errors properly
            'extractor_retries': 5,
            'fragment_retries': 5,
            'retries': 5,
            'socket_timeout': 30,
            'extract_flat': False,
            # Use multiple clients to get best format availability
            # iOS and Android clients often have better format options
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],  # Try ios first (best formats), then android, then web
                    'player_skip': ['webpage', 'configs'],
                }
            },
            # Add user agent and cookies to avoid 403 errors
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            # Don't force external downloader - let yt-dlp handle merging properly
            # Only use ffmpeg for HLS streams if needed
            'external_downloader_args': {
                'ffmpeg': ['-timeout', '30000000']  # 30 second timeout
            }
        }

        # Only set ffmpeg_location if it's a specific path, not just 'ffmpeg'
        if ffmpeg_path != 'ffmpeg':
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        # Configure format based on download type with more robust selection
        if download_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:  # video
            # CRITICAL: Use format selector that EXPLICITLY requires audio
            # Format syntax: acodec!=none means format MUST have audio
            if quality:
                # Prioritize combined formats with audio at specified quality
                format_selector = (
                    f'best[height<={quality}][acodec!=none][vcodec!=none][ext=mp4]/'  # Best combined mp4 with audio
                    f'best[height<={quality}][acodec!=none][vcodec!=none]/'  # Best combined with audio (any ext)
                    f'bestvideo[height<={quality}][vcodec!=none]+bestaudio[acodec!=none]/'  # Merge video + audio
                    f'bestvideo[height<={quality}][vcodec!=none]+bestaudio[acodec!=none][ext=m4a]/'  # Merge with m4a
                    f'bestvideo[height<={quality}][vcodec!=none]+bestaudio[acodec!=none][ext=webm]/'  # Merge with webm
                    f'worst[height<={quality}][acodec!=none][vcodec!=none]'  # Worst but with audio
                )
            else:
                # For best quality: explicitly require audio in all formats
                format_selector = (
                    'best[acodec!=none][vcodec!=none][ext=mp4]/'  # Best combined mp4 with audio
                    'best[acodec!=none][vcodec!=none]/'  # Best combined with audio (any ext)
                    'bestvideo[vcodec!=none]+bestaudio[acodec!=none]/'  # Merge best video + best audio
                    'bestvideo[vcodec!=none][ext=mp4]+bestaudio[acodec!=none][ext=m4a]/'  # Merge mp4 + m4a
                    'bestvideo[vcodec!=none]+bestaudio[acodec!=none][ext=m4a]/'  # Best video + m4a audio
                    'bestvideo[vcodec!=none]+bestaudio[acodec!=none][ext=webm]/'  # Best video + webm audio
                    'best[acodec!=none][vcodec!=none]'  # Final fallback with audio
                )
            
            # Configure format and ensure proper merging
            ydl_opts.update({
                'format': format_selector,
                'merge_output_format': 'mp4',
            })

        def cleanup_temp_files():
            """Clean up temporary files after download"""
            try:
                # Only cleanup if using default temp directory (not custom folder)
                if not is_custom_folder:
                    if downloaded_file and os.path.exists(downloaded_file):
                        os.remove(downloaded_file)
                    if temp_dir.exists() and temp_dir.name == "temp_downloads":
                        for file in temp_dir.glob('*'):
                            try:
                                file.unlink()
                            except Exception:
                                pass
                        try:
                            temp_dir.rmdir()
                        except Exception:
                            pass
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
            # First, extract info to validate URL and select best format
            info_opts = ydl_opts.copy()
            info_opts['quiet'] = True
            info_opts['no_warnings'] = True
            
            with yt_dlp.YoutubeDL(info_opts) as info_ydl:
                try:
                    info = info_ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown')
                    st.write(f"📥 Starting download for: {title}")
                    
                    # Check available formats and log them for debugging
                    formats = info.get('formats', [])
                    if formats:
                        st.info(f"📊 Found {len(formats)} available formats")
                        # Show formats with audio info
                        video_formats = [f for f in formats if f.get('vcodec') != 'none']
                        audio_formats = [f for f in formats if f.get('acodec') != 'none']
                        combined_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                        
                        st.write(f"  📹 Video-only: {len(video_formats)} | 🎵 Audio-only: {len(audio_formats)} | 🎬 Video+Audio: {len(combined_formats)}")
                        
                        # Show best combined formats available
                        if combined_formats:
                            best_combined = sorted(combined_formats, key=lambda x: x.get('height', 0) or 0, reverse=True)[:3]
                            st.write("  🎯 Best combined formats available:")
                            for fmt in best_combined:
                                res = fmt.get('resolution', fmt.get('height', 'N/A'))
                                ext = fmt.get('ext', 'N/A')
                                st.write(f"    - {fmt.get('format_id', 'N/A')}: {res} ({ext})")
                        
                        # Manually select best format with audio if available
                        # This ensures we always get a format with audio
                        best_format = select_best_format_with_audio(formats, quality)
                        if best_format:
                            format_id = best_format.get('format_id')
                            height = best_format.get('height', 'N/A')
                            ext = best_format.get('ext', 'mp4')
                            st.success(f"  ✅ Found best format: {format_id} ({height}p, {ext}) - has video and audio")
                            # Don't override format selector - let yt-dlp handle format selection
                            # The format selector will naturally pick this format if available
                            # Overriding with specific format ID can cause "format not available" errors
                        else:
                            st.warning("  ⚠️ Could not find combined format, will use format selector (may need merging)")
                    
                except Exception as e:
                    st.error(f"❌ Error extracting video info: {str(e)}")
                    logger.error(f"Info extraction error: {e}")
                    return False
            
            # Now perform the actual download with the selected format
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                
                # Perform the actual download
                download_success = False
                try:
                    ydl.download([url])
                    download_success = True
                except Exception as e:
                    error_msg = str(e)
                    st.warning(f"⚠️ Initial download attempt failed: {error_msg}")
                    logger.warning(f"Download error: {e}")
                    
                    # Try multiple fallback approaches - all ensure video with audio
                    # Build quality-aware format selector for fallbacks with explicit audio requirement
                    quality_suffix = f'[height<={quality}]' if quality else ''
                    fallback_format = (
                        f'best{quality_suffix}[acodec!=none][vcodec!=none][ext=mp4]/'  # Best combined mp4 with audio
                        f'best{quality_suffix}[acodec!=none][vcodec!=none]/'  # Best combined with audio
                        f'bestvideo{quality_suffix}[vcodec!=none]+bestaudio[acodec!=none]/'  # Merge video+audio
                        f'bestvideo{quality_suffix}[vcodec!=none]+bestaudio[acodec!=none][ext=m4a]/'  # Merge with m4a
                        'bestvideo[vcodec!=none]+bestaudio[acodec!=none]/best[acodec!=none][vcodec!=none]'  # Final fallbacks
                    )
                    
                    fallback_methods = [
                        {
                            'name': 'iOS client with video+audio',
                            'opts': {
                                'extractor_args': {
                                    'youtube': {
                                        'player_client': ['ios'],
                                    }
                                },
                                'format': fallback_format,
                                'merge_output_format': 'mp4',
                                'external_downloader': None,
                            }
                        },
                        {
                            'name': 'Android client with video+audio',
                            'opts': {
                                'extractor_args': {
                                    'youtube': {
                                        'player_client': ['android'],
                                    }
                                },
                                'format': fallback_format,
                                'merge_output_format': 'mp4',
                                'external_downloader': None,
                            }
                        },
                        {
                            'name': 'Web client with video+audio',
                            'opts': {
                                'extractor_args': {
                                    'youtube': {
                                        'player_client': ['web'],
                                    }
                                },
                                'format': fallback_format,
                                'merge_output_format': 'mp4',
                                'external_downloader': None,
                            }
                        },
                        {
                            'name': 'Any available format with audio',
                            'opts': {
                                'format': 'bestvideo+bestaudio/best/worst',
                                'merge_output_format': 'mp4',
                                'ignore_no_formats_error': True,
                                'external_downloader': None,
                            }
                        }
                    ]
                    
                    for i, method in enumerate(fallback_methods):
                        try:
                            st.info(f"🔄 Trying fallback method {i+1}/{len(fallback_methods)}: {method['name']}...")
                            fallback_opts = ydl_opts.copy()
                            fallback_opts.update(method['opts'])
                            
                            with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                                fallback_ydl.download([url])
                            download_success = True
                            st.success(f"✅ Success with fallback method: {method['name']}")
                            break
                        except Exception as fallback_e:
                            logger.warning(f"Fallback method {i+1} failed: {fallback_e}")
                            if i == len(fallback_methods) - 1:
                                st.error(f"❌ All download methods failed. Last error: {str(fallback_e)}")
                                st.info("💡 Try updating yt-dlp: `pip install --upgrade yt-dlp`")
                                return False
                
                # Check for downloaded file in download directory
                if not downloaded_file:
                    # Try to find the most recently created file in temp_dir
                    try:
                        # Look for video/audio files (common extensions)
                        video_extensions = ['*.mp4', '*.webm', '*.mkv', '*.flv', '*.avi', '*.mov', '*.mp3', '*.m4a', '*.opus', '*.ogg']
                        files = []
                        for ext in video_extensions:
                            files.extend(temp_dir.glob(ext))
                        
                        if files:
                            # Get the most recently modified file
                            downloaded_file = max(files, key=lambda p: p.stat().st_mtime)
                            downloaded_file = str(downloaded_file.resolve())
                        else:
                            # Fallback: check all files
                            all_files = [f for f in temp_dir.glob('*') if f.is_file()]
                            if all_files:
                                downloaded_file = max(all_files, key=lambda p: p.stat().st_mtime)
                                downloaded_file = str(downloaded_file.resolve())
                    except Exception as e:
                        logger.warning(f"Could not find downloaded file: {e}")
                
                # Resolve file path to absolute
                if downloaded_file:
                    downloaded_file = str(Path(downloaded_file).resolve())
                
                if downloaded_file and os.path.exists(downloaded_file):
                    file_size = os.path.getsize(downloaded_file) / (1024 * 1024)  # Convert to MB
                    file_name = os.path.basename(downloaded_file)
                    file_path = str(Path(downloaded_file).parent)
                    
                    # Show success message with file location
                    if is_custom_folder:
                        st.success(f"✅ Download completed! File saved to:")
                        st.info(f"📁 Location: {file_path}")
                        st.info(f"📄 File: {file_name} ({file_size:.1f} MB)")
                        # Also provide download button for convenience
                        try:
                            with open(downloaded_file, 'rb') as f:
                                file_data = f.read()
                            st.download_button(
                                label=f"⬇️ Download {file_name} ({file_size:.1f} MB)",
                                data=file_data,
                                file_name=file_name,
                                mime='application/octet-stream'
                            )
                        except Exception as e:
                            logger.warning(f"Could not create download button: {e}")
                    else:
                        # Create download button for temp files
                        with open(downloaded_file, 'rb') as f:
                            file_data = f.read()
                        
                        st.download_button(
                            label=f"⬇️ Download {file_name} ({file_size:.1f} MB)",
                            data=file_data,
                            file_name=file_name,
                            mime='application/octet-stream'
                        )
                        st.info(f"💡 File temporarily saved to: {file_path}")
                    
                    return True
                elif download_success:
                    # Download reported success but file not found - search more thoroughly
                    st.warning("⚠️ Download reported success but file location unclear. Searching...")
                    try:
                        # Search for video/audio files
                        video_extensions = ['*.mp4', '*.webm', '*.mkv', '*.flv', '*.avi', '*.mov', '*.mp3', '*.m4a', '*.opus', '*.ogg']
                        files = []
                        for ext in video_extensions:
                            files.extend(temp_dir.glob(ext))
                        
                        if not files:
                            # Check all files
                            files = [f for f in temp_dir.glob('*') if f.is_file()]
                        
                        if files:
                            latest_file = max(files, key=lambda p: p.stat().st_mtime)
                            file_size = latest_file.stat().st_size / (1024 * 1024)
                            file_path = str(latest_file.resolve())
                            
                            if is_custom_folder:
                                st.success(f"✅ File found!")
                                st.info(f"📁 Location: {str(latest_file.parent)}")
                                st.info(f"📄 File: {latest_file.name} ({file_size:.1f} MB)")
                                try:
                                    with open(latest_file, 'rb') as f:
                                        file_data = f.read()
                                    st.download_button(
                                        label=f"⬇️ Download {latest_file.name} ({file_size:.1f} MB)",
                                        data=file_data,
                                        file_name=latest_file.name,
                                        mime='application/octet-stream'
                                    )
                                except Exception:
                                    pass
                            else:
                                with open(latest_file, 'rb') as f:
                                    file_data = f.read()
                                st.download_button(
                                    label=f"⬇️ Download {latest_file.name} ({file_size:.1f} MB)",
                                    data=file_data,
                                    file_name=latest_file.name,
                                    mime='application/octet-stream'
                                )
                            return True
                    except Exception as e:
                        logger.error(f"Error finding file: {e}")
                        st.error(f"❌ Could not locate downloaded file. Error: {str(e)}")
                
                st.error("❌ Download completed but file not found. This might be due to format issues.")
                return False
            
            return False

        finally:
            # Clean up temporary files only if not using custom folder
            if not is_custom_folder:
                cleanup_temp_files()

    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")
        return False

def main():
    st.set_page_config(
        page_title="YouTube Downloader", 
        page_icon="🎥",
        layout="wide"
    )
    
    # Title and description
    st.title("🎥 YouTube Downloader")
    
    if IS_CLOUD_DEPLOYMENT:
        st.markdown("""
        Download videos or extract audio from YouTube
        
        ☁️ **Cloud Deployment Mode** - Files will be temporarily stored and available for download
        """)
    else:
        st.markdown("""
        Download videos or extract audio from YouTube
        
        💻 **Local Mode** - Choose a download folder or use the default temporary location
        """)
    
    # Download folder selection (only show in local mode)
    if not IS_CLOUD_DEPLOYMENT:
        st.subheader("📁 Download Folder Selection")
        
        # Show common download locations
        common_folders = {
            "Downloads": os.path.expanduser("~/Downloads"),
            "Desktop": os.path.expanduser("~/Desktop"),
            "Documents": os.path.expanduser("~/Documents"),
            "Custom Path": ""
        }
        
        # Initialize session state with Downloads folder as default
        if 'selected_folder' not in st.session_state:
            # Set default to Downloads folder if it exists, otherwise empty
            default_downloads = common_folders["Downloads"]
            if os.path.exists(default_downloads) and os.path.isdir(default_downloads) and os.access(default_downloads, os.W_OK):
                st.session_state.selected_folder = os.path.abspath(default_downloads)
            else:
                st.session_state.selected_folder = ""
        
        # Quick selection buttons
        st.write("**Quick Select:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📁 Downloads"):
                st.session_state.selected_folder = common_folders["Downloads"]
                st.rerun()
        
        with col2:
            if st.button("🖥️ Desktop"):
                st.session_state.selected_folder = common_folders["Desktop"]
                st.rerun()
        
        with col3:
            if st.button("📄 Documents"):
                st.session_state.selected_folder = common_folders["Documents"]
                st.rerun()
        
        with col4:
            if st.button("🗂️ Custom"):
                st.session_state.selected_folder = ""
                st.rerun()
        
        # Manual path input
        download_folder_input = st.text_input(
            "📂 Download Folder Path:",
            value=st.session_state.selected_folder,
            placeholder="Enter full path (e.g., /Users/username/Downloads) or leave empty for temporary location",
            help="Enter the full path to your desired download folder"
        )
        
        # Normalize and validate folder path
        download_folder = None
        
        # Use input if provided, otherwise use session state (which has default Downloads)
        folder_to_validate = download_folder_input.strip() if download_folder_input else st.session_state.selected_folder
        
        if folder_to_validate:
            # Normalize the path (remove trailing slashes, expand user, etc.)
            normalized_path = os.path.expanduser(folder_to_validate.strip())
            normalized_path = os.path.normpath(normalized_path)
            
            # Validate folder path
            if not os.path.exists(normalized_path):
                st.error(f"❌ Selected folder does not exist: {normalized_path}")
                st.info("💡 Try using the quick select buttons above, or leave empty to use temporary location")
                # Reset to default if current selection is invalid
                if normalized_path == st.session_state.selected_folder:
                    default_downloads = common_folders["Downloads"]
                    if os.path.exists(default_downloads) and os.path.isdir(default_downloads) and os.access(default_downloads, os.W_OK):
                        st.session_state.selected_folder = os.path.abspath(default_downloads)
                    else:
                        st.session_state.selected_folder = ""
            elif not os.path.isdir(normalized_path):
                st.error(f"❌ Path is not a directory: {normalized_path}")
            elif not os.access(normalized_path, os.W_OK):
                st.error(f"❌ No write permission for selected folder: {normalized_path}")
            else:
                # Path is valid - use it
                download_folder = normalized_path
                abs_path = os.path.abspath(download_folder)
                st.success(f"✅ Using folder: {abs_path}")
                st.info("💡 Files will be saved directly to this folder and preserved.")
                # Update session state with valid normalized path
                st.session_state.selected_folder = abs_path
        else:
            st.info("💡 Files will be saved to a temporary location and can be downloaded via the download button.")
            # Clear session state if empty
            if st.session_state.selected_folder:
                st.session_state.selected_folder = ""
    else:
        # Cloud mode - always use temp directory
        download_folder = None
        st.info("☁️ Cloud mode: Files will be temporarily stored and available for download")
    
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
                    quality,
                    download_folder
                )
            
            if success:
                st.button("🔄 Download Another", on_click=st.rerun)

if __name__ == "__main__":
    main()
