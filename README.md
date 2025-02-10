# YouTube Downloader App

A Streamlit-based web application for downloading YouTube videos and playlists in various formats and qualities.

![YouTube Downloader Demo](demo-screenshot.png) <!-- You can add a screenshot later -->

## Description

This application allows users to:
- Download single YouTube videos or entire playlists
- Choose between video or audio-only downloads
- Select video quality (240p to 1080p)
- Specify custom output directories
- Handle download errors gracefully

Built with Python using:
- Streamlit for the web interface
- yt-dlp for YouTube content handling
- FFmpeg for audio conversion

## Features

- 🎥 Video downloads in multiple resolutions
- 🎵 Audio extraction (MP3 format)
- 📁 Playlist support with automatic folder organization
- 🖥️ Simple user interface
- ⚙️ Customizable quality settings
- 🛠️ Error handling and input validation

## Installation
Install FFmpeg (required for audio conversion):
Windows: Download from FFmpeg Official Site
macOS: brew install ffmpeg
Linux: sudo apt install ffmpeg

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/youtube-downloader.git
   cd youtube-downloader
