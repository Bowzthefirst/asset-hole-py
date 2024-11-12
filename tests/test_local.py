from flask import Flask, Request, jsonify
import json
from werkzeug.test import EnvironBuilder
import yt_dlp
import logging
import os
import tempfile
import re
from datetime import datetime
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add these constants
BUCKET_NAME = "nd-pi-ec02a.appspot.com"
storage_client = storage.Client()

def is_valid_youtube_url(url: str) -> bool:
    """Validate YouTube URL format"""
    youtube_regex = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
    return bool(re.match(youtube_regex, url))

def get_video_info(url: str) -> dict:
    """Get video info without downloading"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'nocheckcertificate': True,
            'geo_bypass': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'video'),
                'duration': info.get('duration', 0),
                'formats': info.get('formats', [])
            }
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
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
            'merge_output_format': 'mp4'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Verify file exists and has size
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return False

def test_download_function():
    """Test the download functionality locally"""
    app = Flask(__name__)
    
    # Test cases
    test_cases = [
        {
            "name": "Valid YouTube URL",
            "data": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            "expected_status": 200
        },
        {
            "name": "Invalid URL",
            "data": {"url": "https://invalid-url.com"},
            "expected_status": 400
        },
        {
            "name": "Missing URL",
            "data": {},
            "expected_status": 400
        }
    ]

    with app.test_request_context():
        for test in test_cases:
            print(f"\n=== Testing: {test['name']} ===")
            
            builder = EnvironBuilder(
                method='POST',
                data=json.dumps(test['data']),
                content_type='application/json'
            )
            request = Request(builder.get_environ())

            try:
                request_json = json.loads(request.data.decode('utf-8')) if request.data else {}
                
                if not request_json or 'url' not in request_json:
                    print("Result: No URL provided")
                    continue

                video_url = request_json['url']
                
                if not is_valid_youtube_url(video_url):
                    print("Result: Invalid YouTube URL")
                    continue

                info = get_video_info(video_url)
                if not info:
                    print("Result: Could not get video info")
                    continue

                # Generate safe filename
                safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                blob_name = f"youtube_videos/{filename}"

                # Create a temporary directory instead of just a file
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_file_path = os.path.join(temp_dir, filename)
                    
                    try:
                        print("\nDownloading video...")
                        success = download_video(video_url, temp_file_path)
                        
                        if not success:
                            print("Result: Could not download video")
                            continue
                        
                        # Verify file size
                        file_size = os.path.getsize(temp_file_path)
                        print(f"Downloaded file size: {file_size / (1024*1024):.2f} MB")
                        
                        if file_size == 0:
                            print("Error: Downloaded file is empty")
                            continue
                        
                        print(f"Success! Video info retrieved:")
                        print(f"Title: {info['title']}")
                        print(f"Duration: {info['duration']} seconds")
                        print(f"File path: {temp_file_path}")
                        
                        # Upload to Google Cloud Storage
                        print("\nAttempting to upload to Google Cloud Storage...")
                        try:
                            bucket = storage_client.bucket(BUCKET_NAME)
                            blob = bucket.blob(blob_name)
                            
                            # Upload with explicit content type and check if file exists
                            blob.upload_from_filename(temp_file_path, content_type='video/mp4')
                            blob.make_public()
                            
                            print(f"Upload successful!")
                            print(f"Public URL: {blob.public_url}")
                            
                            # Verify upload
                            uploaded_blob = bucket.get_blob(blob_name)
                            if uploaded_blob:
                                print(f"Verified upload size: {uploaded_blob.size / (1024*1024):.2f} MB")
                            else:
                                print("Warning: Could not verify upload")
                                
                        except Exception as e:
                            print(f"Upload failed: {str(e)}")

                    except Exception as e:
                        print(f"Processing failed: {str(e)}")
                        
                    print("Temporary files cleaned up")

            except Exception as e:
                print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_download_function() 