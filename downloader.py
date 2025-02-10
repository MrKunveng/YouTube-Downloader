import os
import yt_dlp
import streamlit as st

# Function to download a single video or audio
def download_video_or_audio(url, output_path, download_type='video', quality=None):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),  # Output file template
    }

    if download_type == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',  # Best audio format
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',  # Extract audio
                'preferredcodec': 'mp3',  # Convert to MP3
                'preferredquality': '192',  # Audio quality
            }],
        })
    elif download_type == 'video':
        if quality:
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',  # Best video and audio format
            })
    else:
        st.error("Invalid download type. Choose 'video' or 'audio'.")
        return

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            st.write(f"Downloading: {url}")
            ydl.download([url])
            st.success("Download completed successfully.")
    except Exception as e:
        st.error(f"An error occurred: {e}")


# Function to download an entire playlist
def download_playlist(url, output_path, download_type='video', quality=None):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(playlist)s/%(title)s.%(ext)s'),  # Output file template
        'ignoreerrors': True,  # Ignore errors for unavailable videos
    }

    if download_type == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif download_type == 'video':
        if quality:
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
            })
    else:
        st.error("Invalid download type. Choose 'video' or 'audio'.")
        return

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            st.write(f"Downloading playlist: {url}")
            ydl.download([url])
            st.success("Playlist download completed successfully.")
    except Exception as e:
        st.error(f"An error occurred while downloading the playlist: {e}")


# Streamlit App
st.title("YouTube Downloader")

# Input fields
youtube_url = st.text_input("Enter the YouTube video or playlist URL:")
output_directory = st.text_input("Enter the output directory path:", value=os.getcwd())
download_type = st.selectbox("Select download type:", ["video", "audio"])
quality_options = [None, 240, 360, 480, 720, 1080]
quality = st.selectbox("Select video quality (for video downloads):", quality_options) if download_type == "video" else None

# Validate and create output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Check if the URL is a playlist or a single video
is_playlist = "playlist" in youtube_url

# Display playlist-specific information
if is_playlist:
    st.write("You are downloading a playlist.")
else:
    st.write("You are downloading a single video.")

# Download button
if st.button("Download"):
    if not youtube_url:
        st.error("Please enter a valid YouTube URL.")
    elif not output_directory:
        st.error("Please specify an output directory.")
    else:
        if is_playlist:
            download_playlist(youtube_url, output_directory, download_type, quality)
        else:
            download_video_or_audio(youtube_url, output_directory, download_type, quality)