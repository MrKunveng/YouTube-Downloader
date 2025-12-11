# 🎥 YouTube Downloader

A Streamlit web application that allows you to download YouTube videos or extract audio from YouTube videos. Built with Python, Streamlit, and yt-dlp.

## 🌟 Features

- Download YouTube videos in various qualities (240p to 1080p)
- Extract audio from YouTube videos (MP3 format)
- Custom download location selection
- Progress tracking with status updates
- Support for Windows, macOS, and Linux

## 🚀 Quick Start

1. Clone this repository:
```bash
git clone https://github.com/yourusername/youtube-downloader.git
cd youtube-downloader
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg (required for video/audio processing):

**Windows:**
- Download FFmpeg from [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)
- Extract the zip file
- Copy the `ffmpeg.exe` file from the `bin` folder to your YouTube Downloader folder

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

4. Run the application:
```bash
streamlit run downloader.py
```

## 📝 Usage

1. Enter a YouTube URL in the input field
2. Select download type (video or audio)
3. Choose video quality (for video downloads)
4. Select download location
5. Click "Download" and wait for the process to complete

## ⚠️ Important Notes

- This application requires FFmpeg to be installed on your system
- Downloads are restricted to your user's home directory for security
- Some videos might not be available in all quality options
- Please respect YouTube's terms of service and copyright laws

## 🔒 Privacy & Security

- The application only downloads from YouTube URLs
- All downloads are saved within your user's home directory
- No data is collected or shared

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚡ Powered By

- [Streamlit](https://streamlit.io/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/) 
