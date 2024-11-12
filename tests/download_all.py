import os
from google.cloud import storage
import requests
from tqdm import tqdm
import json
from google.oauth2 import service_account

# Load credentials from service account file
credentials = service_account.Credentials.from_service_account_file(
    'nd-pi-ec02a-firebase-adminsdk-8a7lb-dc8e6032fb.json'
)

# Initialize storage client
storage_client = storage.Client(credentials=credentials)
BUCKET_NAME = "nd-pi-ec02a.appspot.com"

def download_file(url, local_path):
    """Download a file from URL with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(local_path, 'wb') as file, tqdm(
        desc=os.path.basename(local_path),
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)

def download_all_videos():
    """Download all videos from the youtube_videos directory"""
    # Create downloads directory if it doesn't exist
    download_dir = "downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Get bucket
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # List all blobs in youtube_videos directory
    blobs = bucket.list_blobs(prefix='youtube_videos/')
    
    print("\nFetching video list...")
    videos = list(blobs)
    
    if not videos:
        print("No videos found in storage.")
        return
    
    print(f"\nFound {len(videos)} videos.")
    print("\nStarting downloads...")
    
    for blob in videos:
        if blob.name == 'youtube_videos/':  # Skip directory itself
            continue
            
        filename = os.path.basename(blob.name)
        local_path = os.path.join(download_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(local_path):
            print(f"\nSkipping {filename} (already exists)")
            continue
            
        print(f"\nDownloading {filename}")
        blob.make_public()
        download_file(blob.public_url, local_path)
        
        # Print file size
        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        print(f"Downloaded: {filename} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    download_all_videos() 