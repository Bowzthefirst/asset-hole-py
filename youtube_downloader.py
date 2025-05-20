import yt_dlp
import logging
import os
import tempfile
from datetime import datetime
import http.client


# 


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
requests_log = logging.getLogger("urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

def download_video(url, format='mp4', quality='normal', output_dir='downloads', list_formats=False, format_id=None):
    """
    Download a video from YouTube with detailed request logging
    
    Args:
        url (str): YouTube URL
        format (str): 'mp4' or 'mp3'
        quality (str): 'normal', 'medium', or 'high'
        output_dir (str): Directory to save the downloaded file
        list_formats (bool): Only list available formats without downloading
        format_id (str): Specific format ID to download
    
    Returns:
        str: Path to the downloaded file or None if download fails
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Add debug logging for network requests
    logger.info(f"Starting download request for URL: {url}")
    
    # Common options with detailed debugging
    common_opts = {
        'quiet': False,
        'verbose': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'ignoreerrors': True,  # Continue despite errors
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }
    
    # Set format string or use specific format_id if provided
    if format_id:
        format_string = format_id
    elif format == 'mp4':
        format_string = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    else:  # mp3
        format_string = 'bestaudio'

    # Configure yt-dlp options
    ydl_opts = {
        **common_opts,
        'format': format_string,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4' if format == 'mp4' else None,
        'force_generic_extractor': False,  # Try to use the native extractor
    }

    # If only listing formats
    if list_formats:
        ydl_opts['listformats'] = True

    # Add MP3 conversion if format is mp3
    if format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320' if quality == 'high' else '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Log the full options being used
            logger.debug(f"YouTube-DL Options: {ydl_opts}")
            
            # If only listing formats, don't download
            if list_formats:
                ydl.extract_info(url, download=False)
                return None
            
            # Get video info first
            logger.info("Extracting video information...")
            info = ydl.extract_info(url, download=False)
            
            if not info:
                logger.error("Could not retrieve video information")
                return None
                
            # Log detailed video information
            logger.info("Video Details:")
            logger.info(f"- Title: {info.get('title')}")
            logger.info(f"- Duration: {info.get('duration')} seconds")
            logger.info(f"- Selected Format: {format_string}")
            
            # Perform the download
            ydl.download([url])
            
            # Get the output filename
            if format == 'mp3':
                filename = f"{info.get('title')}.mp3"
            else:
                filename = f"{info.get('title')}.mp4"
            
            output_path = os.path.join(output_dir, filename)
            
            # Check if file exists
            if os.path.exists(output_path):
                logger.info(f"Download completed: {output_path}")
                return output_path
            else:
                # Try to find the downloaded file by listing directory contents
                files = os.listdir(output_dir)
                if files:
                    # Return the most recently created file
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
                    latest_file = os.path.join(output_dir, files[0])
                    logger.info(f"Found downloaded file: {latest_file}")
                    return latest_file
                    
                logger.error("Download completed but file not found")
                return None
            
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
    parser.add_argument('--list-formats', action='store_true', help='List available formats without downloading')
    parser.add_argument('--format-id', help='Specific format ID to download (from --list-formats)')
    
    args = parser.parse_args()
    
    output_path = download_video(args.url, args.format, args.quality, args.output, args.list_formats, args.format_id)
    if output_path and not args.list_formats:
        print(f"Successfully downloaded to: {output_path}") 