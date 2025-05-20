import yt_dlp
import logging
import os
import tempfile
from datetime import datetime
import http.client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
requests_log = logging.getLogger("urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# Enable HTTP connection debugging
http.client.HTTPConnection.debuglevel = 1

def get_proxy_url():
    """Construct proxy URL from environment variables"""
    host = os.getenv('IPROYAL_PROXY_HOST')
    port = os.getenv('IPROYAL_PROXY_PORT')
    username = os.getenv('IPROYAL_PROXY_USERNAME')
    password = os.getenv('IPROYAL_PROXY_PASSWORD')
    
    if not all([host, port, username, password]):
        raise ValueError("Missing proxy configuration in environment variables")
    
    return f'http://{username}:{password}@{host}:{port}'

def download_video(url, format='mp4', quality='normal', output_dir='downloads'):
    """
    Download a video from YouTube using IPRoyal proxy with detailed request logging
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get proxy URL
    proxy_url = get_proxy_url()
    logger.info(f"Using proxy: {proxy_url.replace(os.getenv('IPROYAL_PROXY_PASSWORD'), '****')}")
    
    # Enhanced browser-like headers and options
    common_opts = {
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'verbose': True,
        'debug_printtraffic': True,
        'proxy': proxy_url,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        },
        'socket_timeout': 30,
        'retries': 3,
        # Add cookies support
        'cookiesfrombrowser': ('chrome',),
        # Add more options to bypass restrictions
        'extractor_retries': 3,
        'fragment_retries': 3,
        'skip_download': False,
        'force_generic_extractor': False,
        'sleep_interval': 1,  # Add delay between requests
        'max_sleep_interval': 5,
        'sleep_interval_requests': 1,
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Log the full options being used (hiding proxy password)
            safe_opts = dict(ydl_opts)
            if 'proxy' in safe_opts:
                safe_opts['proxy'] = safe_opts['proxy'].replace(
                    os.getenv('IPROYAL_PROXY_PASSWORD'), '****')
            logger.debug(f"YouTube-DL Options: {safe_opts}")
            
            # Get video info first
            logger.info("Extracting video information through proxy...")
            info = ydl.extract_info(url, download=False)
            
            # Log detailed video information
            logger.info("Video Details:")
            logger.info(f"- Title: {info.get('title')}")
            logger.info(f"- Duration: {info.get('duration')} seconds")
            logger.info(f"- View Count: {info.get('view_count')}")
            logger.info(f"- Available Formats: {len(info.get('formats', []))}")
            logger.info(f"- Selected Format: {format_string}")
            
            # Perform the download
            logger.info("Starting download through proxy...")
            ydl.download([url])
            
            # Get the output filename
            if format == 'mp3':
                filename = f"{info.get('title')}.mp3"
            else:
                filename = f"{info.get('title')}.mp4"
            
            output_path = os.path.join(output_dir, filename)
            logger.info(f"Download completed: {output_path}")
            return output_path
            
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download YouTube videos through IPRoyal proxy')
    parser.add_argument('url', help='YouTube URL')
    parser.add_argument('--format', choices=['mp4', 'mp3'], default='mp4', help='Output format (mp4 or mp3)')
    parser.add_argument('--quality', choices=['normal', 'medium', 'high'], default='normal', help='Video quality')
    parser.add_argument('--output', default='downloads', help='Output directory')
    
    args = parser.parse_args()
    
    output_path = download_video(args.url, args.format, args.quality, args.output)
    if output_path:
        print(f"Successfully downloaded to: {output_path}") 