import requests
import json
from datetime import datetime
import time

def test_scenario(url, description):
    """Run a single test scenario"""
    api_url = "https://us-central1-nd-pi-428502.cloudfunctions.net/youtube-download"
    data = {"url": url}
    
    print(f"\n=== Testing Scenario: {description} at {datetime.now()} ===")
    print(f"Testing URL: {url}")
    
    try:
        print("\nMaking request...")
        response = requests.post(
            api_url,
            json=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout=600
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        
        try:
            print(f"Response Content: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response Content: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print("\nRequest timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        return False

def run_tests():
    scenarios = [
        {
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # First YouTube video ever
            "description": "Very short video (18 seconds)"
        },
        {
            "url": "https://www.youtube.com/watch?v=0DNJH-8UluI",  # Your test video
            "description": "Previous test video"
        },
        {
            "url": "https://youtu.be/dQw4w9WgXcQ",  # Short form URL
            "description": "Short URL format"
        },
        {
            "url": "https://www.youtube.com/watch?v=invalid",
            "description": "Invalid video ID"
        }
    ]
    
    results = []
    for scenario in scenarios:
        success = test_scenario(scenario["url"], scenario["description"])
        results.append({
            "description": scenario["description"],
            "url": scenario["url"],
            "success": success
        })
        time.sleep(5)  # Wait between tests
        
    print("\n=== Test Summary ===")
    for result in results:
        status = "✅ Passed" if result["success"] else "❌ Failed"
        print(f"{status} - {result['description']}")

if __name__ == "__main__":
    run_tests() 