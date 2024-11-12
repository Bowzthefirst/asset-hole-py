import requests
import time
import json
from datetime import datetime

def test_youtube_url(url):
    # Using the correct cloud function URL
    api_url = "https://us-central1-nd-pi-428502.cloudfunctions.net/youtube-download"
    data = {"url": url}
    
    print(f"\n=== Testing Cloud Function at {datetime.now()} ===")
    print(f"Testing URL: {url}")
    print(f"Sending request to: {api_url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        # Add headers to mimic a browser
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/96.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1'
        }
        
        print("\nMaking request...")
        response = requests.post(
            api_url, 
            json=data, 
            headers=headers, 
            timeout=540  # 9 minute timeout
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print("Response Data:")
            print(json.dumps(response_data, indent=2))
            
            if response.status_code == 200:
                print("\nSUCCESS!")
                print(f"Title: {response_data.get('title')}")
                print(f"Storage Path: {response_data.get('storage_path')}")
                print(f"Public URL: {response_data.get('public_url')}")
                print(f"File Size: {response_data.get('file_size_mb', 0):.2f} MB")
            else:
                print("\nERROR!")
                print(f"Error details: {response_data.get('details', response_data.get('error', 'No details provided'))}")
                
        except json.JSONDecodeError:
            print(f"Raw Response Content: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\nRequest timed out after 9 minutes!")
        print("The function might still be processing.")
        print("Check the Cloud Functions logs for more details.")
    except requests.exceptions.RequestException as e:
        print(f"\nRequest Error: {str(e)}")
    except Exception as e:
        print(f"\nGeneral Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Never Gonna Give You Up
    ]
    
    for url in urls:
        test_youtube_url(url)
        time.sleep(3)