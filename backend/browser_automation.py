from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

class BrowserAutomation:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver with webdriver-manager"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def close_driver(self):
        if self.driver:
            self.driver.quit()

# Test function
if __name__ == "__main__":
    automation = BrowserAutomation()
    automation.setup_driver()
    automation.driver.get("https://www.google.com")
    time.sleep(3)
    automation.close_driver()
    print("Browser automation test successful!")
