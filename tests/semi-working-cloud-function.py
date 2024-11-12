import os
import yt_dlp
import functions_framework
from flask import jsonify, Request
import logging
from google.cloud import storage
from datetime import datetime
import tempfile
import re
import json
from google.oauth2 import service_account
import traceback
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials from environment variable
credentials_json = os.environ.get('YOUTUBE_DOWNLOADER_SA_KEY')
if credentials_json:
    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    storage_client = storage.Client(credentials=credentials)
else:
    # Fallback to default credentials (when running locally)
    storage_client = storage.Client()

BUCKET_NAME = "nd-pi-ec02a.appspot.com"

def is_valid_youtube_url(url: str) -> bool:
    """Validate YouTube URL format"""
    youtube_regex = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
    return bool(re.match(youtube_regex, url))

def get_video_info(url: str) -> dict:
    """Get video info without downloading"""
    try:
        # Ensure URL is properly decoded if it's bytes
        if isinstance(url, bytes):
            url = url.decode('utf-8')
        
        logger.info(f"Getting info for URL: {url}")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'socket_timeout': 30,
            'retries': 3
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    logger.error("No info returned from yt-dlp")
                    return None
                
                logger.info(f"Successfully retrieved info for video: {info.get('title', 'unknown')}")
                return {
                    'title': info.get('title', 'video'),
                    'duration': info.get('duration', 0),
                    'formats': info.get('formats', [])
                }
            except Exception as e:
                logger.error(f"yt-dlp extraction error: {str(e)}")
                return None
                
    except Exception as e:
        logger.error(f"Error in get_video_info: {str(e)}")
        return None

def download_video(url: str, output_path: str) -> bool:
    """Download the video to the specified output path"""
    try:
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'merge_output_format': 'mp4',  # Ensure output is MP4
            'cachedir': '/tmp',  # Use /tmp for cache in cloud function
            'no_cache': True,    # Disable cache
            'noprogress': True,  # Disable progress to avoid console spam
            'max_filesize': 2000000000  # Limit to ~2GB for cloud function
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Starting download to: {output_path}")
            ydl.download([url])
            
            # Verify file exists and has size
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                logger.info(f"Download complete. File size: {size / (1024*1024):.2f} MB")
                return size > 0
            
            logger.error("File does not exist after download")
            return False
            
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return False

@functions_framework.http
def download_youtube(request: Request):
    """HTTP Cloud Function that downloads a YouTube video and uploads it to storage"""
    headers = {'Access-Control-Allow-Origin': '*'}

    if request.method == 'OPTIONS':
        headers.update({
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        })
        return ('', 204, headers)

    try:
        # Get JSON data and ensure proper encoding
        try:
            if request.is_json:
                request_json = request.get_json()
            else:
                request_json = json.loads(request.data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error parsing request data: {str(e)}")
            return (jsonify({'error': 'Invalid request data'}), 400, headers)

        if not request_json or 'url' not in request_json:
            return (jsonify({'error': 'No URL provided'}), 400, headers)

        # Ensure URL is properly encoded string
        video_url = request_json['url']
        if isinstance(video_url, bytes):
            video_url = video_url.decode('utf-8')
        video_url = str(video_url).strip()

        # Validate URL
        if not is_valid_youtube_url(video_url):
            return (jsonify({'error': 'Invalid YouTube URL'}), 400, headers)

        logger.info(f"Processing request for URL: {video_url}")

        # Get video info
        info = get_video_info(video_url)
        if not info:
            return (jsonify({'error': 'Could not get video info'}), 500, headers)

        # Generate safe filename
        safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        blob_name = f"youtube_videos/{filename}"

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(dir='/tmp')
        temp_file_path = os.path.join(temp_dir, filename)
        
        try:
            logger.info("Downloading video...")
            success = download_video(video_url, temp_file_path)
            
            if not success:
                return (jsonify({'error': 'Could not download video'}), 500, headers)

            # Verify file size
            file_size = os.path.getsize(temp_file_path)
            logger.info(f"Downloaded file size: {file_size / (1024*1024):.2f} MB")
            
            if file_size == 0:
                return (jsonify({'error': 'Downloaded file is empty'}), 500, headers)

            # Upload to Google Cloud Storage
            logger.info("Uploading to Google Cloud Storage...")
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(temp_file_path, content_type='video/mp4')
            blob.make_public()

            # Verify upload
            uploaded_blob = bucket.get_blob(blob_name)
            if not uploaded_blob:
                return (jsonify({'error': 'Upload verification failed'}), 500, headers)

            logger.info(f"Upload successful. Size: {uploaded_blob.size / (1024*1024):.2f} MB")

            return (jsonify({
                'title': info['title'],
                'filename': filename,
                'download_url': blob.public_url,
                'video_info': info,
                'file_size_mb': file_size / (1024*1024)
            }), 200, headers)

        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return (jsonify({'error': str(e)}), 500, headers)
        finally:
            # Cleanup temp directory
            try:
                if os.path.exists(temp_dir):
                    os.remove(temp_file_path)
                    os.rmdir(temp_dir)
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")

    except Exception as e:
        logger.error(f"Function error: {str(e)}")
        return (jsonify({'error': str(e)}), 500, headers)

@functions_framework.http
def youtube_download(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        request_json = request.get_json()
        url = str(request_json.get('url', '')).strip()
        
        print(f"Python version: {sys.version}")
        print(f"yt-dlp version: {yt_dlp.version.__version__}")
        print(f"Processing URL: {url}")

        # Basic options for testing
        ydl_opts = {
            'quiet': False,  # Enable output for debugging
            'no_warnings': False,  # Show warnings
            'extract_flat': True,  # Only extract metadata
            'format': 'best',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First just try to validate the URL
                if not yt_dlp.utils.is_url(url):
                    return jsonify({'error': 'Invalid URL format'}), 400, headers

                # Try to extract basic info
                print("Attempting to extract info...")
                basic_info = ydl.extract_info(url, download=False, process=False)
                
                if not basic_info:
                    return jsonify({'error': 'No video information found'}), 404, headers

                return jsonify({
                    'success': True,
                    'video_id': basic_info.get('id', ''),
                    'title': basic_info.get('title', ''),
                    'extractor': basic_info.get('extractor', '')
                }), 200, headers

        except yt_dlp.utils.DownloadError as e:
            print(f"yt-dlp download error: {str(e)}")
            return jsonify({'error': f'Download error: {str(e)}'}), 500, headers
        except Exception as e:
            print(f"yt-dlp extraction error: {str(e)}")
            return jsonify({'error': f'Extraction error: {str(e)}'}), 500, headers

    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500, headers
        # hello
        