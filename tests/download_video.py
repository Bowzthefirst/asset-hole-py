import requests
import json
from datetime import datetime
import sys

def download_video(video_url):
    """Download a single YouTube video using the cloud function"""
    
    # Cloud function URL
    api_url = "https://us-central1-nd-pi-428502.cloudfunctions.net/youtube-download"
    
    # Prepare request data
    data = {"url": video_url}
    
    print(f"\n=== Starting Download at {datetime.now()} ===")
    print(f"Video URL: {video_url}")
    
    try:
        # Make request
        print("\nSending request to cloud function...")
        response = requests.post(
            api_url,
            json=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout=600  # 10 minute timeout
        )
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Download Successful!")
            print(f"Title: {result['title']}")
            print(f"File Size: {result['file_size_mb']:.2f} MB")
            print(f"\nDownload URL: {result['download_url']}")
            return True
            
        else:
            print("\n❌ Download Failed")
            print(f"Status Code: {response.status_code}")
            try:
                error = response.json().get('error', 'Unknown error')
                print(f"Error: {error}")
            except:
                print(f"Raw Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\nUsage: python download_video.py <youtube_url>")
        print("Example: python download_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)
        
    video_url = sys.argv[1]
    download_video(video_url) 