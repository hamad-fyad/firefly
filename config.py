import os
from dotenv import load_dotenv
import requests

load_dotenv()

def get_firefly_url(): # here i check if the ec2 instance is up
    # Check for GitHub Actions environment
    if os.getenv('GITHUB_ACTIONS'):
        firefly_base_url = os.getenv('FIREFLY_BASE_URL', 'http://52.212.42.101:8080/api/v1')
        return firefly_base_url.replace('/api/v1', '')
    
    # Local development fallback
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

# API Token selection based on environment
if os.getenv('GITHUB_ACTIONS'):
    # GitHub Actions environment
    API_TOKEN = os.getenv("API_TESTING_TOKEN")
elif "local" in BASE_URL: # if running locally, use the local API token
    API_TOKEN = os.getenv("API_TESTING_TOKEN2") 
else:
    API_TOKEN = os.getenv("FIREFLY_TOKEN2")
    
STATIC_CRON_TOKEN = os.getenv("STATIC_CRON_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"  
}
