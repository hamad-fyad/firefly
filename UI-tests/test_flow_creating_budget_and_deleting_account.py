import datetime
import time
import unittest
from selenium import webdriver
from Helper_Class import LoginPage, registerPage,new_user, DashboardPage
import os 
import tempfile
firefly = os.environ.get("FIREFLY_URL", "http://52.212.42.101:8080")
class FireflyBudgetTest(unittest.TestCase):



    def setUp(self):
        self.name = "test_name_" + str(datetime.datetime.now())
        
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
        self.driver.get(firefly + "/register")
        self.driver.maximize_window()


    def test_create_budget(self):
    
        # Try to register a new user
        register_page = registerPage(self.driver)
        new_user_obj = register_page.register_new_user("hamad.fyad.05@gmail.com", "Hamadf@0528259919")
        self.driver.implicitly_wait(5) 
        dashboard = new_user_obj.enter_as_new_user("test_bank", "1000000")
        budget_page = dashboard.go_to_budgets()
        dashboard1 = budget_page.create_new_budget(self.name, "1000")

        self.assertIn("Home", self.driver.title)
        dashboard1.delete_account("Hamadf@0528259919")
        self.assertIn("Login", self.driver.title)


    def tearDown(self):
        self.driver.quit()
