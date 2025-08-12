
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class registerPage:
    def __init__(self, driver):
        self.driver = driver
        WebDriverWait(driver, 10).until(EC.url_contains("register"))
        self.email_field = (By.XPATH, "//input[@placeholder='Email address']")
        self.password_field = (By.XPATH, "//input[@placeholder='Password']")
        self.confirm_password_field = (By.XPATH, "//input[@placeholder='Password (again)']")
        self.checkbox = (By.XPATH, "//input[@type='checkbox']")
        self.register_button = (By.XPATH, "//button[normalize-space()='Register']")


    def register_new_user(self, email, password):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.email_field)).send_keys(email)
        self.driver.find_element(*self.password_field).send_keys(password)

        self.driver.find_element(*self.confirm_password_field).send_keys(password)
        self.driver.find_element(*self.checkbox).click()
        self.driver.find_element(*self.register_button).click()
        return new_user(self.driver)
    
class new_user:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
          # Wait for elements to load
        self.bank_name = (By.ID, "ffInput_bank_name")
        self.bank_balance = (By.ID, "bank_balance")
        self.submit = (By.XPATH, "//input[@name='submit']")
        self.skip_button = (By.CSS_SELECTOR, ".introjs-button.introjs-skipbutton")

    def enter_as_new_user(self, bankname, bank_balance):
          # Wait for elements to load
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.bank_name)).send_keys(bankname)
        self.driver.find_element(*self.bank_balance).send_keys(bank_balance)
        self.driver.find_element(*self.submit).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.skip_button)).click()
        return DashboardPage(self.driver)
    
class LoginPage:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        WebDriverWait(driver, 10).until(EC.title_contains("Login"))
        self.email_field = (By.XPATH, "//input[@placeholder='Email address']")
        self.password_field = (By.XPATH, "//input[@placeholder='Password']")
        self.login_button = (By.XPATH, "//button[normalize-space()='Sign in']")
        # self.skip_button = (By.XPATH, "//a[normalize-space()='Skip']")

    def login_as_valid_user(self, username, password):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.email_field)).send_keys(username)
        self.driver.find_element(*self.password_field).send_keys(password)
        self.driver.find_element(*self.login_button).click()
        # self.driver.find_element(*self.skip_button).click()
        return DashboardPage(self.driver)


class DashboardPage:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        WebDriverWait(driver, 10).until(EC.title_contains("Home » Firefly III"))
        self.budgets_link = (By.XPATH, "//li[@id='budget-menu']//a")
        self.dashboard_link = (By.XPATH, "//a[.//span[text()='Dashboard']]")
        self.options = (By.XPATH, "//li[@id='option-menu']//a[@href='#']")
        self.profile_link = (By.XPATH, "//span[normalize-space()='Profile']")
        self.delete_account_link = (By.XPATH, "//a[normalize-space()='Delete account']")
        self.password = (By.ID, "password")
        self.delete_button = (By.XPATH, "//button[normalize-space()='DELETE your account']")
        self.skip_button = (By.CSS_SELECTOR, ".introjs-button.introjs-skipbutton")


    def go_to_budgets(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.skip_button)
            ).click()
        except:
            print("No intro skip button visible at first.")

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(self.budgets_link)
        ).click()

        return BudgetPage(self.driver)


    # def go_to_dashboard(self):
    #     self.driver.implicitly_wait(10) 
    #     WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.dashboard_link)).click()
    #     WebDriverWait(self.driver, 10).until(
    #         lambda d: d.find_elements(By.XPATH, "//h2[contains(text(), 'Dashboard')]")
    #     )
    #     return DashboardPage(self.driver)
    def delete_account(self, password):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.options)).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.profile_link)).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.delete_account_link)).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.password)).send_keys(password)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.delete_button)).click()
        print("Account deleted successfully")
        return LoginPage(self.driver)



        



    def logout(self):
        # Find and click the logout button (update selector as needed)
        logout_button = (By.XPATH, "//a[@class='logout-link']")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(logout_button)).click()
        # Wait for login page to appear
        WebDriverWait(self.driver, 10).until(EC.title_contains("Login"))
        return LoginPage(self.driver) 


class BudgetPage:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        WebDriverWait(driver, 10).until(EC.title_contains("Budgets"))

        # Try to detect the available "create" button
        try:
            create_btn = driver.find_element(By.XPATH, "//a[normalize-space()='Create a budget']")
            if "Create a budget" in create_btn.text:
                self.create_budget = (By.XPATH, "//a[normalize-space()='Create a budget']")
        except Exception:
            # Fallback to the alternative button
            self.create_budget = (
                By.XPATH,
                "//div[@class='box-body no-padding']//div//a[@class='btn btn-success'][normalize-space()='New budget']"
            )

        self.input_name = (By.ID, "ffInput_name")
        self.auto_budget_dropdown = (By.ID, "ffInput_auto_budget_type")
        self.select_budget_option = (
            By.XPATH, "//option[normalize-space()='Set a fixed amount every period']"
        )
        self.amount_input = (By.ID, "ffInput_auto_budget_amount")
        self.save_button = (By.XPATH, "//button[normalize-space()='Store new budget']")
        self.dashboard_link = (By.XPATH, "//a[.//span[text()='Dashboard']]")
        self.skip_button = (By.CSS_SELECTOR, ".introjs-button.introjs-skipbutton")

    def create_new_budget(self, name: str, amount: str):
        # Click on "Create a budget"
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.create_budget)).click()
        # Fill in the budget name
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.input_name)
        ).send_keys(name)

        # Open budget type dropdown and select the option
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.auto_budget_dropdown)).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.select_budget_option)).click()

        # Fill in the amount
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.amount_input)
        ).send_keys(amount)
          # Wait for elements to load
        # Submit the form
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.save_button)).click()
          # Wait for elements to load
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.skip_button)).click()
        # Wait for the page to refresh or redirect
        WebDriverWait(self.driver, 10).until(
            lambda d:
            #d.find_elements(By.XPATH, "//body/div[@id='app']/aside[@class='main-sidebar']/section[@class='sidebar']/ul[@class='sidebar-menu tree']/li[1]/a[1]")#TODO need to change this to a more reliable check
            d.find_elements(By.XPATH, "//span[normalize-space()='Dashboard']")
        )
          # Wait for elements to load

        # Click on Dashboard in sidebar
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(self.dashboard_link)
        ).click()

        return DashboardPage(self.driver)
