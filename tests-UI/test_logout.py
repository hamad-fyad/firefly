
import datetime
import time
import unittest
from selenium import webdriver
from Helper_Class import LoginPage, registerPage, new_user, DashboardPage
import os
import tempfile
import requests

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

firefly = get_firefly_url()

class Fireflylogout(unittest.TestCase):
    def setUp(self):
        headless = str(os.environ.get("HEADLESS", "false")).lower() in ("true", "1")
        options = webdriver.ChromeOptions()

        # Essential Chrome arguments for CI/headless environments
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript-harmony-shipping')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--window-size=1920,1080')
        
        if headless:
            options.add_argument('--headless=new')
        else:
            options.add_argument("--start-maximized")

        # Create unique Chrome user profile to avoid conflicts
        self.user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={self.user_data_dir}")

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(firefly + "/login")
            
            # Only maximize in GUI mode and if not already maximized
            if not headless:
                try:
                    self.driver.maximize_window()
                except Exception as e:
                    print(f"Warning: Could not maximize window: {e}")
                    
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            raise


    def test_logout(self):
        # Login as a valid user
        login_page = LoginPage(self.driver)
        self.driver.implicitly_wait(5) # Wait for logout to complete

        dashboard = login_page.login_as_valid_user("hamad.fyad@gmail.com", "Hamadf@0528259919")
        self.assertIn("Home", self.driver.title)
        # Perform logout
        dashboard.logout()
        self.driver.implicitly_wait(5) # Wait for logout to complete
        self.assertIn("Login", self.driver.title) 

    def tearDown(self):
        self.driver.quit()
        if hasattr(self, "user_data_dir"):
            try:
                import shutil
                shutil.rmtree(self.user_data_dir, ignore_errors=True)
            except Exception:
                pass

