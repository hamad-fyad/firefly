import os
from dotenv import load_dotenv
import requests

load_dotenv()
def get_firefly_url():
    remote = "http://52.212.42.101:8080"
    local = "http://localhost:8080"
    try:
        r = requests.get(remote, timeout=2)
        if r.status_code < 500:
            return remote
    except Exception:
        pass
    return local

BASE_URL = get_firefly_url() + "/api/v1"
print(f"Using BASE_URL: {BASE_URL}")
if "local" in BASE_URL:
    API_TOKEN = os.getenv("API_TESTING_TOKEN2") 
else:
    API_TOKEN = os.getenv("API_TESTING_TOKEN")
    
STATIC_CRON_TOKEN = os.getenv("STATIC_CRON_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"  
}
