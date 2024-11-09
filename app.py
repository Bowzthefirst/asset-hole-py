import streamlit as st
import os
import yt_dlp
import logging
import sys
from datetime import datetime
from moviepy.editor import VideoFileClip
import subprocess
import tempfile

# Load custom CSS
def load_css():
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Configure page
st.set_page_config(
    page_title="Asset Hole YouTube Downloader",
    page_icon="🎥",
    layout="wide"
)

# Load CSS
load_css()

# Configure logging
log_filename = f"youtube_downloader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def download_video(url, output_path, format='mp4'):
    try:
        logger.info(f"Starting download process for URL: {url} in format: {format}")
        
        # Common options for both info extraction and download
        common_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            # Add these options to help bypass restrictions
            'nocheckcertificate': True,
            'geo_bypass': True,
            'format': 'best',
            # Add custom headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        # First, get video information
        with yt_dlp.YoutubeDL(common_opts) as ydl:
            try:
                logger.debug("Fetching video information")
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video')
                duration = info.get('duration', 0)
                
                logger.info(f"Video details - Title: {title}, Duration: {duration} seconds")
                st.info(f"Title: {title}")
                st.info(f"Length: {duration} seconds")
                
            except Exception as e:
                logger.error(f"Error fetching video info: {str(e)}", exc_info=True)
                st.error(f"Error fetching video info: {str(e)}")
                return None, None

        # Create a temporary directory for this download
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Update download options based on format
            if format == 'mp4':
                logger.info("Processing MP4 download")
                ydl_opts = {
                    **common_opts,
                    'format': 'best[ext=mp4]',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                }
            
            elif format == 'mp3':
                logger.info("Processing MP3 download")
                ydl_opts = {
                    **common_opts,
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                }

            # Download the video/audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    logger.debug("Starting download")
                    ydl.download([url])
                    
                    # After download, get the file from temp directory
                    downloaded_files = os.listdir(temp_dir)
                    if downloaded_files:
                        temp_file_path = os.path.join(temp_dir, downloaded_files[0])
                        return temp_file_path, title
                    
                    return None, None
                
                except Exception as e:
                    logger.error(f"Error during download: {str(e)}", exc_info=True)
                    st.error(f"Error during download: {str(e)}")
                    return None, None

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        return None, None

# Add after imports
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        st.error("FFmpeg is not installed. Some features may not work properly.")
        return False

# The main() function remains largely the same
def main():
    check_ffmpeg()
    # Custom header with styling
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown('<h1>Asset Hole YouTube Downloader</h1>', unsafe_allow_html=True)
    st.markdown('<p>Download YouTube videos in MP4 or MP3 format</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url = st.text_input("🔗 Enter YouTube URL:")
    
    with col2:
        format_option = st.radio("📦 Select Format:", ('MP4', 'MP3'))
    
    # Download section
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    if st.button("⬇️ Download"):
        if url:
            logger.info(f"Download requested for URL: {url} in format: {format_option}")
            with st.spinner("Processing..."):
                # Remove the "downloads" directory parameter
                file_path, title = download_video(url, None, format_option.lower())
                
                if file_path and title:
                    try:
                        with open(file_path, 'rb') as file:
                            logger.info(f"File ready for download: {file_path}")
                            st.success(f"Successfully downloaded: {title}")
                            st.download_button(
                                label=f"Download {format_option}",
                                data=file,
                                file_name=f"{title}.{format_option.lower()}",
                                mime=f"{'video/mp4' if format_option == 'MP4' else 'audio/mp3'}"
                            )
                    except Exception as e:
                        logger.error(f"Error handling the downloaded file: {str(e)}", exc_info=True)
                        st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a YouTube URL")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Usage instructions with better styling
    with st.expander("📖 How to use"):
        st.markdown("""
        <div class="usage-guide">
        1. Paste a YouTube URL (e.g., https://www.youtube.com/watch?v=...)
        2. Select your desired format (MP4 or MP3)
        3. Click the Download button
        4. Wait for processing
        5. Click the download button that appears to save your file
        </div>
        """, unsafe_allow_html=True)
    
    # Add this after your header
    st.warning("""
        ⚠️ Note: Due to YouTube's restrictions, some videos might not be downloadable. 
        If you encounter issues, try:
        - Using shorter videos
        - Using different videos
        - Checking if the video is publicly available
    """)

# Create downloads directory at startup
if not os.path.exists("downloads"):
    os.makedirs("downloads")

if __name__ == "__main__":
    main() 