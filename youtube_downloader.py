import yt_dlp
import logging
import os
import tempfile
from datetime import datetime
    
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_video(url, format='mp4', quality='normal', output_dir='downloads'):
    """
    Download a video from YouTube
    
    Args:
        url (str): YouTube URL
        format (str): 'mp4' or 'mp3'
        quality (str): 'normal', 'medium', or 'high'
        output_dir (str): Directory to save the downloaded file
    
    Returns:
        str: Path to the downloaded file or None if download fails
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Common options
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    
    # Set format string based on quality and format
    if format == 'mp4':
        if quality == 'high':
            format_string = 'bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == 'medium':
            format_string = 'bestvideo[ext=mp4][height>=720][height<1080]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:  # normal
            format_string = 'best[ext=mp4]'
    else:  # mp3
        format_string = 'bestaudio/best'

    # Configure yt-dlp options
    ydl_opts = {
        **common_opts,
        'format': format_string,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    }

    # Add MP3 conversion if format is mp3
    if format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320' if quality == 'high' else '192',
        }]

    try:
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            logger.info(f"Downloading: {title}")
            
            # Perform the download
            ydl.download([url])
            
            # Get the output filename
            if format == 'mp3':
                filename = f"{title}.mp3"
            else:
                filename = f"{title}.mp4"
            
            output_path = os.path.join(output_dir, filename)
            logger.info(f"Download completed: {output_path}")
            return output_path
            
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download YouTube videos')
    parser.add_argument('url', help='YouTube URL')
    parser.add_argument('--format', choices=['mp4', 'mp3'], default='mp4', help='Output format (mp4 or mp3)')
    parser.add_argument('--quality', choices=['normal', 'medium', 'high'], default='normal', help='Video quality')
    parser.add_argument('--output', default='downloads', help='Output directory')
    
    args = parser.parse_args()
    
    output_path = download_video(args.url, args.format, args.quality, args.output)
    if output_path:
        print(f"Successfully downloaded to: {output_path}") 