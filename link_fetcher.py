import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import setup_logger

logger = setup_logger(__name__)

class ProductLinkFetcher:
    """Navigates search pages and fetches product links."""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager

    def fetch(self, base_url, max_products):
        driver = self.driver_manager.get_driver()
        links = []
        logger.info(f"Loading search page: {base_url}")
        
        try:
            driver.get(base_url)
        except TimeoutException:
            logger.warning("Page load timed out, attempting to proceed...")
            
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/otc/'], a[href*='/drugs/']"))
            )
        except TimeoutException:
            logger.warning("Timeout waiting for initial product links to load.")
            
        time.sleep(3)
        
        if "Just a moment..." in driver.page_source or "Cloudflare" in driver.page_source:
            logger.error("Cloudflare bot protection triggered on search page. Please try running headful or later.")
            return links
            
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 50
        
        while len(links) < max_products and scroll_attempts < max_scroll_attempts:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            a_tags = soup.find_all("a", href=True)
            new_links_found = False
            
            for tag in a_tags:
                href = tag['href']
                if "/otc/" in href or "/drugs/" in href:
                    full_url = href if href.startswith("http") else f"https://www.1mg.com{href}"
                    if full_url not in links:
                        links.append(full_url)
                        new_links_found = True
                        if len(links) >= max_products:
                            break
                            
            logger.info(f"Collected {len(links)} links so far...")
            
            if len(links) >= max_products:
                break
                
            product_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/otc/'], a[href*='/drugs/']")
            if product_elements:
                last_product = product_elements[-1]
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", last_product)
            else:
                driver.execute_script("window.scrollBy(0, 500);")
                
            time.sleep(3)  # Small delay to mimic human reading/scrolling and allow network requests
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height and not new_links_found:
                # Nudge the scroll to see if it triggers loading
                driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("Reached end of page or no more products loading.")
                    break
                    
            last_height = new_height
            scroll_attempts += 1
                
        return links[:max_products]
