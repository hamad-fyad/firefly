import datetime
import unittest
from selenium import webdriver
from Helper_Class import LoginPage


class FireflyBudgetTest(unittest.TestCase):
    def setUp(self):
        self.name = "test_name_" + str(datetime.datetime.now())
        self.driver = webdriver.Chrome()
        self.driver.get("http://localhost:8080/login")
        self.driver.maximize_window()

    def test_logout(self):
        login_page = LoginPage(self.driver)
        dashboard = login_page.login_as_valid_user("hamad.fyad.05@gmail.com", "Hamadf@0528259919")
        # Perform logout
        dashboard.logout()
        # Assert redirected to login page
        self.assertIn("Login", self.driver.title)

    def tearDown(self):
        self.driver.quit()
