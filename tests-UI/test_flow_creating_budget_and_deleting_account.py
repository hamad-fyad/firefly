import datetime
import time
import unittest
from selenium import webdriver
from Helper_Class import LoginPage, registerPage, new_user, DashboardPage
import os
import tempfile
from dotenv import load_dotenv
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

headless = str(os.environ.get("HEADLESS", "false")).lower() in ("true", "1")
if headless == "false":
    load_dotenv()
firefly = get_firefly_url()

class FireflyBudgetTest(unittest.TestCase):



    def setUp(self):
        
        self.name = "test_name_" + str(datetime.datetime.now())
        
        headless = str(os.environ.get("HEADLESS", "false")).lower() in ("true", "1")
        options = webdriver.ChromeOptions()

        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox') # This option is used to run Chrome in headless mode without a sandbox, which is useful for CI environments.
            options.add_argument('--disable-dev-shm-usage') # This option makes Chrome store temporary data on disk instead of shared memory, avoiding crashes in low-/dev/shm environments.

        # ✅ Unique Chrome user profile
        user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={user_data_dir}")

        self.driver = webdriver.Chrome(options=options)
       
        self.driver.get(firefly + "/register")
        self.driver.maximize_window()
        self.driver.implicitly_wait(10) 


    def test_create_budget(self):
    
        # Try to register a new user
        register_page = registerPage(self.driver)
        new_user_obj = register_page.register_new_user("hamad.fyad.05@gmail.com", "Hamadf@0528259919")
        
        dashboard = new_user_obj.enter_as_new_user("test_bank", "1000000")
        budget_page = dashboard.go_to_budgets()
        dashboard1 = budget_page.create_new_budget(self.name, "1000")

        self.assertIn("Home", self.driver.title)
        dashboard1.delete_account("Hamadf@0528259919")
        self.assertIn("Login", self.driver.title)


    def tearDown(self):
        self.driver.quit()

        
if __name__ == "__main__":
    unittest.main()
    unittest.main(verbosity=2)
# This code is a test case for creating a budget and deleting an account in the Firefly application using Selenium WebDriver.
# It uses the unittest framework to structure the test case, and it includes setup and teardown methods
# to initialize and clean up the WebDriver instance.        