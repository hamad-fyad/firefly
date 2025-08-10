import datetime
import time
import unittest
from selenium import webdriver
from Helper_Class import LoginPage, registerPage,new_user, DashboardPage
import os 
import tempfile
firefly = os.environ.get("FIREFLY_URL", "http://52.212.42.101:8080")

class Fireflylogout(unittest.TestCase):
    def setUp(self):
        headless = str(os.environ.get("HEADLESS", "false")).lower() in ("true", "1")
        options = webdriver.ChromeOptions()

        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

        # ✅ Unique Chrome user profile
        user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={user_data_dir}")

        self.driver = webdriver.Chrome(options=options)
        self.driver.get(firefly + "/login")
        self.driver.maximize_window()

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

