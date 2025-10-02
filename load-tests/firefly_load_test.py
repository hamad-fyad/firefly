from locust import HttpUser, task, between
import os

class FireflyAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.headers = {
            "Authorization": f"Bearer {os.getenv('API_TESTING_TOKEN', 'dummy_token')}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.api+json"
        }
    
    @task(3)
    def get_about(self):
        with self.client.get("/api/v1/about", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [401, 403]:
                response.success()  # Expected for load testing without real auth
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(2)
    def get_accounts(self):
        with self.client.get("/api/v1/accounts", headers=self.headers, catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def get_transactions(self):
        with self.client.get("/api/v1/transactions", headers=self.headers, catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
