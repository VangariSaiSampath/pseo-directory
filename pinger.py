import requests
import time

def ping_site():
    url = "https://integration-directory.com/"
    try:
        response = requests.get(url)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Pinged site. Status: {response.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Failed to ping: {e}")

if __name__ == "__main__":
    ping_site()