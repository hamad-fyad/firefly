import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("FIREFLY_BASE_URL", "http://localhost:8080/api/v1")
API_TOKEN = os.getenv("API_TESTING_TOKEN") 
STATIC_CRON_TOKEN = os.getenv("STATIC_CRON_TOKEN")
print(f"Using BASE_URL: {BASE_URL}, API_TOKEN: {API_TOKEN}")
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"  
}
