import os
import streamlit as st
from pathlib import Path
import platform
import yt_dlp
import logging
import subprocess
import sys
import re

# Configure logging for cloud environment
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cloud deployment configuration
IS_CLOUD_DEPLOYMENT = os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false').lower() == 'true'

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

def check_yt_dlp_version():
    """Check if yt-dlp is up to date and warn if outdated."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'yt_dlp', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"yt-dlp version: {version}")
            # Could add version comparison here if needed
    except Exception as e:
        logger.warning(f"Could not check yt-dlp version: {e}")

def extract_video_id_from_url(url):
    """Extract video ID from various YouTube URL formats."""
    if not url:
        return None
    
    # Log the URL for debugging
    logger.info(f"Extracting video ID from URL: {url}")
    
    # Standard watch URL: https://www.youtube.com/watch?v=VIDEO_ID
    # Also handles: watch?v=VIDEO_ID&list=...
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    if match:
        video_id = match.group(1)
        logger.info(f"Found video ID (watch format): {video_id}")
        return video_id
    
    # Short URL: https://youtu.be/VIDEO_ID or https://youtu.be/VIDEO_ID?t=...
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if match:
        video_id = match.group(1)
        logger.info(f"Found video ID (short format): {video_id}")
        return video_id
    
    # Embed URL: https://www.youtube.com/embed/VIDEO_ID
    match = re.search(r'/embed/([a-zA-Z0-9_-]{11})', url)
    if match:
        video_id = match.group(1)
        logger.info(f"Found video ID (embed format): {video_id}")
        return video_id
    
    # Mobile URL: https://m.youtube.com/watch?v=VIDEO_ID
    match = re.search(r'm\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})', url)
    if match:
        video_id = match.group(1)
        logger.info(f"Found video ID (mobile format): {video_id}")
        return video_id
    
    # Playlist URL with video: https://www.youtube.com/playlist?list=...&v=VIDEO_ID
    match = re.search(r'playlist[^&]*[&]v=([a-zA-Z0-9_-]{11})', url)
    if match:
        video_id = match.group(1)
        logger.info(f"Found video ID (playlist with v param): {video_id}")
        return video_id
    
    # Try to find any 11-character alphanumeric string that looks like a video ID
    # This is a fallback for unusual URL formats
    match = re.search(r'([a-zA-Z0-9_-]{11})', url)
    if match:
        potential_id = match.group(1)
        # Basic validation: YouTube video IDs are 11 characters
        # Check if it's in a context that suggests it's a video ID
        if any(pattern in url for pattern in ['watch', 'youtu.be', 'embed', 'v=']):
            logger.info(f"Found potential video ID (fallback): {potential_id}")
            return potential_id
    
    logger.warning(f"Could not extract video ID from URL: {url}")
    return None

def download_content(url: str, output_path: str, download_type: str = 'video', quality: int = None, download_folder: str = None):
    """Download video or audio content."""
    # Enhanced logging for cloud mode debugging
    logger.info(f"Cloud mode: {IS_CLOUD_DEPLOYMENT}")
    logger.info(f"Download type: {download_type}, Quality: {quality}")
    
    # Check yt-dlp version on first download attempt
    check_yt_dlp_version()
    
    ffmpeg_path = check_ffmpeg()
    logger.info(f"ffmpeg path: {ffmpeg_path}")
    
    if not ffmpeg_path:
        show_ffmpeg_instructions()
        return False

    try:
        # In cloud mode, always use /tmp and ignore custom download folder
        if IS_CLOUD_DEPLOYMENT:
            temp_dir = Path("/tmp")
            is_custom_folder = False
            logger.info("Cloud mode: Using /tmp for downloads")
        elif download_folder and os.path.exists(download_folder) and os.access(download_folder, os.W_OK):
            # Use absolute path for download folder (local mode only)
            temp_dir = Path(download_folder).resolve()
            is_custom_folder = True
            logger.info(f"Local mode: Using custom folder: {temp_dir}")
        else:
            # Use absolute path for temp directory (local mode)
            temp_dir = Path("temp_downloads").resolve()
            is_custom_folder = False
            logger.info(f"Local mode: Using temp directory: {temp_dir}")
        
        # Ensure directory exists
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Download folder: {temp_dir}")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        downloaded_file = None

        # Configure yt-dlp options with improved settings for better compatibility
        # Use absolute path for output template
        output_template = str(temp_dir / '%(title)s.%(ext)s')
        logger.info(f"Output template: {output_template}")
        if is_custom_folder and not IS_CLOUD_DEPLOYMENT:
            st.info(f"📁 Files will be saved to: {temp_dir}")
        elif IS_CLOUD_DEPLOYMENT:
            st.info("☁️ Cloud mode: Files will be temporarily stored in /tmp")
        
        # Check for cookies file (optional but recommended for cloud)
        cookies_file = None
        if os.path.exists('cookies.txt'):
            cookies_file = 'cookies.txt'
            logger.info("Found cookies.txt - will use for authentication")
        elif os.path.exists('.streamlit/cookies.txt'):
            cookies_file = '.streamlit/cookies.txt'
            logger.info("Found cookies.txt in .streamlit folder")
        
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
            'extractor_retries': 10,
            'fragment_retries': 10,
            'retries': 10,
            'socket_timeout': 60,
            'file_access_retries': 3,
            'extract_flat': False,
            # Use multiple clients to get best format availability and avoid 403 errors
            # Try mweb (mobile web) first as it's less likely to be blocked
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'ios', 'android', 'web'],  # Try mweb first (mobile web - less restrictions)
                    'player_skip': ['webpage', 'configs'],
                    'skip': ['dash', 'hls'],  # Skip problematic formats
                }
            },
            # Add sleep interval to avoid rate limiting
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            # Comprehensive headers to avoid 403 errors - mimic real browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.youtube.com/',
            },
            # Don't force external downloader - let yt-dlp handle merging properly
            # Only use ffmpeg for HLS streams if needed
            'external_downloader_args': {
                'ffmpeg': ['-timeout', '30000000']  # 30 second timeout
            }
        }
        
        # Add cookies if available (helps with cloud IP blocking)
        if cookies_file:
            ydl_opts['cookiefile'] = cookies_file
            logger.info(f"Using cookies file: {cookies_file}")

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
            
            # Extract video ID FIRST before any extraction attempts to avoid playlist JSON errors
            is_playlist = 'list=' in url.lower() or '/playlist' in url.lower()
            original_url = url
            
            # If it's a playlist URL, extract video ID and use direct video URL immediately
            video_id = None
            if is_playlist:
                st.info("📋 Playlist detected. Extracting video ID...")
                video_id = extract_video_id_from_url(url)
                if video_id:
                    # Use direct video URL to completely bypass playlist extraction
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    st.success(f"✅ Extracted video ID: {video_id}")
                    st.info(f"🔄 Using direct video URL to avoid playlist parsing errors")
                    # Ensure noplaylist is set
                    info_opts['noplaylist'] = True
                else:
                    st.warning("⚠️ Could not extract video ID from playlist URL.")
                    st.info("💡 Trying alternative extraction methods...")
                    
                    # Try to extract from URL parameters more aggressively
                    # Sometimes video ID might be in different parameter positions
                    url_parts = url.split('&')
                    for part in url_parts:
                        if 'v=' in part:
                            potential_id = part.split('v=')[-1].split('&')[0].split('?')[0].strip()
                            if len(potential_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', potential_id):
                                video_id = potential_id
                                url = f"https://www.youtube.com/watch?v={video_id}"
                                st.success(f"✅ Found video ID in URL parameters: {video_id}")
                                st.info(f"🔄 Using direct video URL")
                                info_opts['noplaylist'] = True
                                break
                    
                    if not video_id:
                        st.warning("⚠️ Will try with noplaylist flag (may still fail if playlist parsing is required)...")
                        info_opts['noplaylist'] = True
            
            with yt_dlp.YoutubeDL(info_opts) as info_ydl:
                try:
                    
                    # Now extract info using the direct video URL (or original if not playlist)
                    info = info_ydl.extract_info(url, download=False)
                    
                    # Check if it's still a playlist entry (shouldn't happen with direct URL, but just in case)
                    if info.get('_type') == 'playlist':
                        st.warning("⚠️ Still detected as playlist. Extracting first video...")
                        entries = info.get('entries', [])
                        if entries:
                            # Get first video from playlist
                            first_video = entries[0]
                            if first_video:
                                info = first_video
                                # Try to get video URL from entry
                                if first_video.get('id'):
                                    url = f"https://www.youtube.com/watch?v={first_video.get('id')}"
                                elif first_video.get('url'):
                                    url = first_video.get('url')
                                st.info(f"📹 Extracted video: {info.get('title', 'Unknown')}")
                        else:
                            st.error("❌ Playlist has no entries available")
                            return False
                    
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
                            st.success(f"  ✅ Selected format {format_id} ({height}p, {ext}) - has video and audio")
                            # Override format selector to use this specific format
                            ydl_opts['format'] = format_id
                        else:
                            st.warning("  ⚠️ Could not find combined format, will use format selector (may need merging)")
                    
                except Exception as e:
                    error_str = str(e)
                    logger.error(f"Info extraction error: {e}")
                    
                    # Check if it's a playlist JSON error
                    if 'playlist' in error_str.lower() or 'PLY_' in error_str or 'JSONDecodeError' in error_str:
                        st.warning("⚠️ Playlist extraction failed. Extracting video ID and trying direct URL...")
                        try:
                            # Extract video ID from original URL (before any modifications)
                            video_id = extract_video_id_from_url(original_url if 'original_url' in locals() else url)
                            
                            # If still no video ID, try more aggressive extraction
                            if not video_id:
                                st.info("🔍 Trying alternative extraction methods...")
                                # Try parsing URL manually
                                url_to_parse = original_url if 'original_url' in locals() else url
                                
                                # Method 1: Split by & and look for v= parameter
                                for param in url_to_parse.split('&'):
                                    if 'v=' in param:
                                        potential_id = param.split('v=')[-1].split('?')[0].strip()
                                        if len(potential_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', potential_id):
                                            video_id = potential_id
                                            st.info(f"✅ Found video ID using parameter parsing: {video_id}")
                                            break
                                
                                # Method 2: Look for 11-character alphanumeric strings after common patterns
                                if not video_id:
                                    patterns = [
                                        r'watch\?[^&]*v=([a-zA-Z0-9_-]{11})',
                                        r'youtu\.be/([a-zA-Z0-9_-]{11})',
                                        r'/v/([a-zA-Z0-9_-]{11})',
                                        r'video_id=([a-zA-Z0-9_-]{11})',
                                    ]
                                    for pattern in patterns:
                                        match = re.search(pattern, url_to_parse)
                                        if match:
                                            video_id = match.group(1)
                                            st.info(f"✅ Found video ID using pattern matching: {video_id}")
                                            break
                            
                            if video_id:
                                # Use direct video URL with noplaylist
                                direct_video_url = f"https://www.youtube.com/watch?v={video_id}"
                                st.info(f"🔄 Trying direct video URL: {direct_video_url}")
                                
                                # Force single video extraction with simpler options
                                retry_opts = info_opts.copy()
                                retry_opts['noplaylist'] = True
                                retry_opts['extract_flat'] = False
                                retry_opts['extractor_args'] = {
                                    'youtube': {
                                        'player_client': ['mweb'],
                                    }
                                }
                                
                                with yt_dlp.YoutubeDL(retry_opts) as retry_ydl:
                                    info = retry_ydl.extract_info(direct_video_url, download=False)
                                    url = direct_video_url  # Update URL for download
                                    title = info.get('title', 'Unknown')
                                    st.write(f"📥 Starting download for: {title}")
                            else:
                                st.error("❌ Could not extract video ID from URL")
                                st.error(f"**URL provided:** {original_url if 'original_url' in locals() else url}")
                                st.error("""
                                **Troubleshooting steps:**
                                1. **Copy the direct video URL** from YouTube (not playlist URL)
                                   - Right-click the video → Copy video URL
                                   - Format: `https://www.youtube.com/watch?v=VIDEO_ID`
                                2. **Update yt-dlp**: `pip install --upgrade yt-dlp`
                                3. **Check if the video is available** and not restricted
                                4. **Wait a few minutes** and try again (rate limiting)
                                5. **Try a different video** to see if the issue is specific to this video
                                """)
                                return False
                        except Exception as retry_e:
                            st.error(f"❌ Error extracting video info: {str(retry_e)}")
                            st.error("""
                            **Troubleshooting steps:**
                            1. **Update yt-dlp**: `pip install --upgrade yt-dlp`
                            2. **Try a direct video URL** instead of playlist URL: `https://www.youtube.com/watch?v=VIDEO_ID`
                            3. **Check if the video is available** and not restricted
                            4. **Wait a few minutes** and try again (rate limiting)
                            """)
                            logger.error(f"Retry extraction error: {retry_e}")
                            return False
                    else:
                        st.error(f"❌ Error extracting video info: {error_str}")
                        st.info("💡 Try updating yt-dlp: `pip install --upgrade yt-dlp`")
                        return False
            
            # Now perform the actual download with the selected format
            # Make sure we use the updated URL (direct video URL if it was a playlist)
            ydl_opts['noplaylist'] = True  # Ensure we don't try to download playlist
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
                    
                    # Enhanced headers for fallback methods
                    enhanced_headers = {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Referer': 'https://www.youtube.com/',
                        'Origin': 'https://www.youtube.com',
                    }
                    
                    fallback_methods = [
                        {
                            'name': 'Mobile Web client (mweb)',
                            'opts': {
                                'extractor_args': {
                                    'youtube': {
                                        'player_client': ['mweb'],
                                    }
                                },
                                'format': fallback_format,
                                'merge_output_format': 'mp4',
                                'http_headers': enhanced_headers,
                                'sleep_interval': 2,
                                'external_downloader': None,
                            }
                        },
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
                                'http_headers': enhanced_headers,
                                'sleep_interval': 2,
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
                                'http_headers': enhanced_headers,
                                'sleep_interval': 2,
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
                                'http_headers': enhanced_headers,
                                'sleep_interval': 2,
                                'external_downloader': None,
                            }
                        },
                        {
                            'name': 'Any available format with audio',
                            'opts': {
                                'format': 'bestvideo+bestaudio/best/worst',
                                'merge_output_format': 'mp4',
                                'http_headers': enhanced_headers,
                                'sleep_interval': 3,
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
                            error_str = str(fallback_e)
                            logger.warning(f"Fallback method {i+1} failed: {fallback_e}")
                            
                            # Check if it's a 403 error specifically
                            if '403' in error_str or 'Forbidden' in error_str:
                                if i == len(fallback_methods) - 1:
                                    st.error("❌ All download methods failed due to HTTP 403 Forbidden error.")
                                    st.warning("""
                                    **Possible solutions:**
                                    1. **Update yt-dlp** to the latest version:
                                       ```bash
                                       pip install --upgrade yt-dlp
                                       ```
                                    2. **Cloud environment limitations**: YouTube may be blocking requests from cloud IPs.
                                       Try running locally instead.
                                    3. **Rate limiting**: Wait a few minutes and try again.
                                    4. **Video restrictions**: Some videos may have download restrictions.
                                    """)
                                    return False
                            elif i == len(fallback_methods) - 1:
                                st.error(f"❌ All download methods failed. Last error: {error_str}")
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
