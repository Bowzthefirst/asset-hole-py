import requests
import json
from datetime import datetime
import time

def test_cloud_function():
    url = "https://us-central1-nd-pi-428502.cloudfunctions.net/youtube-download"
    data = {
        "url": "https://www.youtube.com/watch?v=0DNJH-8UluI"
    }
    
    print(f"\n=== Testing Cloud Function at {datetime.now()} ===")
    print(f"Sending request to: {url}")
    print(f"With data: {json.dumps(data, indent=2)}")
    
    try:
        # Make request with debug info and increased timeout
        print("\nMaking request...")
        response = requests.post(
            url, 
            json=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout=600  # 10 minute timeout
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        
        try:
            print(f"Response Content: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response Content: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\nRequest timed out. The function might still be processing.")
        print("Check the Cloud Functions logs for more details.")
    except requests.exceptions.ConnectionError as e:
        print("\nConnection error occurred. The function might have timed out.")
        print(f"Error details: {str(e)}")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")

if __name__ == "__main__":
    test_cloud_function() 