import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import setup_logger

logger = setup_logger(__name__)

class ProductParser:
    """Extracts detailed information from a single product page."""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager

    def parse(self, url):
        driver = self.driver_manager.get_driver()
        
        # Add retry loop for page load to handle occasional failures gracefully
        max_retries = 2
        for attempt in range(max_retries):
            try:
                driver.get(url)
                # Wait explicitly for either h1 or description to ensure main content has loaded
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
                break
            except TimeoutException:
                logger.warning(f"Timeout on {url} (Attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.warning(f"Proceeding anyway for {url}")
            except Exception as e:
                logger.error(f"Error loading {url}: {e}")
                return None
                
        # Additional explicit wait for description area which might take longer
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#aboutexpand, div.ProductDescription, div[class*='description']"))
            )
        except TimeoutException:
            # If description doesn't appear, we still proceed to parse whatever is there
            pass

        time.sleep(1)
        
        if "Just a moment..." in driver.page_source or "Cloudflare" in driver.page_source:
            logger.error("Cloudflare bot protection triggered on product page.")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        company_name = "Mankind"
        medicine_name = "N/A"
        composition = ""
        price = "N/A"
        description_text = "N/A"
        image_urls = set()
        
        # 1. Medicine Name
        h1 = soup.find("h1")
        if h1:
            medicine_name = h1.get_text(strip=True)
        elif soup.title:
            medicine_name = soup.title.get_text(strip=True).split('|')[0].strip()
            
        # 2. Composition
        salt_tags = soup.find_all("a", href=lambda h: h and "/generics/" in h)
        if salt_tags:
            salts = []
            for tag in salt_tags:
                txt = tag.get_text(strip=True)
                if txt and txt not in salts:
                    salts.append(txt)
            composition = " + ".join(salts)
        else:
            salt_div = soup.find(lambda tag: tag.name == "div" and tag.get("class") and any("salt" in c.lower() for c in tag.get("class", [])))
            if salt_div:
                composition = salt_div.get_text(strip=True)
            
        # 3. Price
        price_text_found = ""
        price_divs = soup.find_all(lambda tag: tag.name in ["span", "div"] and tag.get("class") and any("price" in c.lower() or "mrp" in c.lower() for c in tag.get("class", [])))
        for div in price_divs:
            t = div.get_text(separator=' ', strip=True)
            if '₹' in t:
                price_text_found = t
                break
                
        if not price_text_found:
            for tag in soup.find_all(["span", "div"]):
                t = tag.get_text(separator=' ', strip=True)
                if '₹' in t and len(t) < 40 and ('mrp' in t.lower() or 'price' in t.lower()):
                    price_text_found = t
                    break
                    
        if price_text_found:
            match = re.search(r'₹\s?([0-9,.]+)', price_text_found)
            if match:
                price_str = match.group(1).replace(',', '').strip()
                try: 
                    price = float(price_str)
                except ValueError: 
                    price = price_str
                     
        # 4. Description
        desc_div = soup.find("div", {"id": "aboutexpand"})
        if not desc_div:
            desc_div = soup.find("div", {"class": re.compile(r"ProductDescription|product-description", re.I)})
        if not desc_div:
            desc_div = soup.find(lambda tag: tag.name == "div" and tag.get("class") and any("description" in c.lower() for c in tag.get("class", [])))
            
        if desc_div:
             raw_text = " ".join(desc_div.stripped_strings)
             clean_text = re.sub(r'\s+', ' ', raw_text).strip()
             if clean_text:
                 description_text = f"{medicine_name}\n{clean_text}"
             
        # 5. Images
        img_tags = soup.find_all("img")
        for img in img_tags:
            src = img.get("src")
            if not src or "http" not in src:
                continue
            
            classes = img.get("class", [])
            is_product_img = any("picture-image" in c.lower() or "thumbnail" in c.lower() for c in classes)
            
            if ("/image/upload/" in src) or is_product_img or ("w_380" in src) or ("w_700" in src):
                if not any(icon in src.lower() for icon in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']):
                    image_urls.add(src)
            
        return {
            "companyName": company_name,
            "medicineName": medicine_name,
            "composition": composition,
            "price": price,
            "description": description_text,
            "image_urls": list(image_urls)
        }
