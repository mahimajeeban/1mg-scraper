import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from utils import setup_logger

logger = setup_logger(__name__)

class DriverManager:
    """Manages Selenium WebDriver setup and teardown."""
    
    def __init__(self, headless=False, timeout=30, use_proxy_bypass=False):
        self.headless = headless
        self.timeout = timeout
        self.use_proxy_bypass = use_proxy_bypass
        self.driver = None

    def get_driver(self):
        if self.driver is None or not self._is_driver_alive():
            # Close existing dead driver if any
            if self.driver is not None:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            
            # Conditional proxy bypass (enabled via .env USE_PROXY_BYPASS=True)
            if self.use_proxy_bypass:
                logger.info("🔧 Proxy bypass enabled for localhost (corporate proxy mode)")
                # Bypass proxy for localhost ONLY (fixes corporate proxy issues)
                # This prevents Selenium from using corporate proxy to connect to ChromeDriver
                # But still allows Chrome to use proxy for external websites (like 1mg.com)
                options.add_argument("--proxy-bypass-list=localhost,127.0.0.1,::1,<local>")
            else:
                logger.info("🌐 Using default proxy settings (no bypass)")
            
            # Suppress Chrome logs and DevTools messages
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument("--log-level=3")  # Only show fatal errors
            options.add_argument("--silent")
            
            # Chrome options to improve stability and avoid network issues
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-breakpad")
            options.add_argument("--disable-component-extensions-with-background-pages")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
            options.add_argument("--force-color-profile=srgb")
            options.add_argument("--metrics-recording-only")
            options.add_argument("--mute-audio")
            options.page_load_strategy = 'eager'
            
            # User agent to appear more like a real browser
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            
            # Suppress Selenium logs
            service = Service(log_output=os.devnull if os.name != 'nt' else 'NUL')
            
            # Retry logic for WebDriver initialization
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Initializing Chrome WebDriver (attempt {attempt + 1}/{max_retries})...")
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self.driver.set_page_load_timeout(self.timeout)
                    logger.info("✅ WebDriver initialized successfully.")
                    break
                    
                except WebDriverException as e:
                    if attempt < max_retries - 1:
                        wait_time = 3 * (attempt + 1)  # Wait 3s, 6s, 9s
                        logger.warning(f"⚠️ WebDriver initialization failed: {e}")
                        logger.warning(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Failed to initialize WebDriver after {max_retries} attempts.")
                        logger.error("Possible causes:")
                        logger.error("  1. Chrome browser not installed or incompatible version")
                        logger.error("  2. ChromeDriver download blocked by firewall/proxy")
                        logger.error("  3. Network connection issues")
                        logger.error("  4. Antivirus blocking ChromeDriver")
                        logger.error("\nTroubleshooting:")
                        logger.error("  • Ensure Chrome browser is installed")
                        logger.error("  • Check your internet connection")
                        logger.error("  • Try disabling antivirus temporarily")
                        logger.error("  • Check firewall/proxy settings")
                        raise
                        
        return self.driver

    def _is_driver_alive(self):
        """Check if the WebDriver session is still active."""
        if self.driver is None:
            return False
        try:
            # Try to get current URL to test connection
            _ = self.driver.current_url
            return True
        except:
            return False
    
    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            logger.info("WebDriver closed.")
