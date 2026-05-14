from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from utils import setup_logger

logger = setup_logger(__name__)

class DriverManager:
    """Manages Selenium WebDriver setup and teardown."""
    
    def __init__(self, headless=False, timeout=30):
        self.headless = headless
        self.timeout = timeout
        self.driver = None

    def get_driver(self):
        if self.driver is None:
            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.page_load_strategy = 'eager'
            
            try:
                self.driver = webdriver.Chrome(options=options)
                self.driver.set_page_load_timeout(self.timeout)
                logger.info("WebDriver initialized successfully.")
            except WebDriverException as e:
                logger.error(f"Failed to initialize WebDriver: {e}")
                raise
        return self.driver

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver closed.")
