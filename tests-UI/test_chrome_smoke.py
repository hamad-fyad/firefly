"""
Chrome WebDriver Smoke Test - Verify Selenium Setup

This test validates that Chrome and ChromeDriver are properly configured
for CI/headless environments. It performs basic browser operations to
ensure the WebDriver stack is functional.
"""
import os
import tempfile
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests


def get_firefly_url():
    """Get Firefly III URL - prefer remote, fallback to local."""
    remote = "http://52.212.42.101:8080"
    local = "http://localhost:8080"
    try:
        r = requests.get(remote, timeout=2)
        if r.status_code < 500:
            return remote
    except Exception:
        pass
    return local


class ChromeSmokeTest(unittest.TestCase):
    """Smoke test for Chrome WebDriver functionality."""

    def setUp(self):
        """Set up Chrome WebDriver with CI-optimized configuration."""
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
            
            # Only maximize in GUI mode and with error handling
            if not headless:
                try:
                    self.driver.maximize_window()
                except Exception as e:
                    print(f"Warning: Could not maximize window: {e}")
                    
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            raise

    def test_chrome_basic_functionality(self):
        """Test basic Chrome WebDriver operations."""
        
        # Test 1: Navigate to a simple page
        self.driver.get("https://httpbin.org/html")
        
        # Test 2: Verify page loads
        self.assertIn("Herman Melville", self.driver.page_source)
        
        # Test 3: Get page title
        title = self.driver.title
        self.assertIsNotNone(title)
        
        # Test 4: Find an element
        h1_element = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertIsNotNone(h1_element)
        
        # Test 5: Get window size
        size = self.driver.get_window_size()
        self.assertGreater(size['width'], 0)
        self.assertGreater(size['height'], 0)
        
        print(f"✅ Chrome smoke test passed")
        print(f"   Title: {title}")
        print(f"   Window: {size['width']}x{size['height']}")

    def test_firefly_connectivity(self):
        """Test connectivity to Firefly III instance."""
        
        firefly_url = get_firefly_url()
        
        try:
            # Test basic page load
            self.driver.get(firefly_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Check if we get a reasonable response
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            # Basic validation
            self.assertTrue(len(page_source) > 100, "Page content too short")
            self.assertTrue(current_url.startswith("http"), "Invalid URL redirect")
            
            print(f"✅ Firefly connectivity test passed")
            print(f"   URL: {current_url}")
            print(f"   Page size: {len(page_source)} chars")
            
        except Exception as e:
            print(f"⚠️ Firefly connectivity failed: {e}")
            # Don't fail the test if Firefly is unavailable
            self.skipTest(f"Firefly III unavailable at {firefly_url}: {e}")

    def tearDown(self):
        """Clean up WebDriver and temporary files."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Warning: Error quitting driver: {e}")
                
        # Clean up temporary Chrome profile
        if hasattr(self, "user_data_dir"):
            try:
                import shutil
                shutil.rmtree(self.user_data_dir, ignore_errors=True)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main(verbosity=2)