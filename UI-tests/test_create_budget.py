import datetime
import time
import unittest
from selenium import webdriver
from Helper_Class import LoginPage, registerPage,new_user, DashboardPage
import os 

firefly = os.environ.get("FIREFLY_URL", "http://localhost:8080")
class FireflyBudgetTest(unittest.TestCase):

    def setUp(self):

        self.name = "test_name_" + str(datetime.datetime.now())
        self.driver = webdriver.Chrome()
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
