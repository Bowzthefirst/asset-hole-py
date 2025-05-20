#!/usr/bin/env python3
import yt_dlp

# URL of the video you want to download (change this to any YouTube URL)
VIDEO_URL = "https://www.youtube.com/watch?v=D4llDi20gM4"

def download_video(url):
    """
    Download a YouTube video using yt-dlp
    
    Args:
        url (str): The YouTube video URL
    """
    # Configure yt-dlp options for more reliable downloads
    ydl_opts = {
        # Use a more flexible format selection to avoid format errors
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        'outtmpl': '%(title)s.%(ext)s',  # Output filename template
        'ignoreerrors': True,  # Skip errors
        'nooverwrites': False,  # Overwrite existing files
        'quiet': False,  # Show download progress
        'no_warnings': False,  # Show warnings
        'nocheckcertificate': True,  # Don't verify SSL certificates
    }
    
    # Print information about the download
    print(f"Downloading video: {url}")
    print("This may take a few moments...")
    
    try:
        # Create a YoutubeDL object with our options
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video information first
            info = ydl.extract_info(url, download=False)
            
            if info:
                print(f"Title: {info.get('title')}")
                print(f"Duration: {info.get('duration')} seconds")
                
                # Download the video
                ydl.download([url])
                print(f"Download complete! Saved as: {info.get('title')}.{info.get('ext', 'mp4')}")
            else:
                print("Failed to get video information")
                
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {e}")
        # Try with a different format if the requested format is not available
        if "Requested format is not available" in str(e):
            print("Trying with a different format...")
            ydl_opts['format'] = 'best'
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    print("Download complete!")
            except Exception as e2:
                print(f"Second attempt failed: {e2}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Just run the download function with the URL defined in the script
    download_video(VIDEO_URL)
