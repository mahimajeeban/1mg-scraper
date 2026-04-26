import os
import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_driver():
    options = Options()
    is_headless = os.environ.get("HEADLESS", "False").lower() == "true"
    if is_headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = 'eager' # Don't wait for full resource loading
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30) # Prevent freezing
    return driver

def setup_session():
    session = requests.Session()
    # Adding robust headers to mimic a browser
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    })
    
    # Retry strategy for network failures or server errors
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

def fetch_product_links(driver, base_url, max_products):
    """Fetches up to `max_products` product URLs from the search pages by scrolling."""
    links = []
    print(f"Loading search page: {base_url}")
    
    try:
        driver.get(base_url)
    except TimeoutException:
        print(f"Page load timed out, attempting to proceed...")
        
    # Initial wait to let page load completely
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/otc/'], a[href*='/drugs/']"))
        )
    except TimeoutException:
        print("Timeout waiting for initial product links to load.")
        
    time.sleep(3) # Additional wait for JS execution
    
    if "Just a moment..." in driver.page_source or "Cloudflare" in driver.page_source:
        print("Cloudflare bot protection triggered.")
        return links
        
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scroll_attempts = 50 # Prevent infinite looping
    
    while len(links) < max_products and scroll_attempts < max_scroll_attempts:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find all potential product links
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
                        
        print(f"Collected {len(links)} links so far...")
        
        if len(links) >= max_products:
            break
            
        # Detect the last loaded product element and scroll just until it is visible
        product_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/otc/'], a[href*='/drugs/']")
        if product_elements:
            last_product = product_elements[-1]
            # Scroll to the last product so it's centered in the viewport
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", last_product)
        else:
            # Fallback small scroll
            driver.execute_script("window.scrollBy(0, 500);")
            
        time.sleep(3) # Wait briefly for new products to load
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # If height hasn't changed and no new links were found, we might be at the end
        if new_height == last_height and not new_links_found:
            # Try a small scroll to trigger just in case
            driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Reached end of page or no more products loading.")
                break
                
        last_height = new_height
        scroll_attempts += 1
            
    return links[:max_products]

def parse_product_page(driver, url):
    """Extracts product details from the product page."""
    try:
        try:
            driver.get(url)
            # Explicitly wait for product title to appear
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except TimeoutException:
            print(f"Page load timed out for {url}, attempting to proceed...")
            
        time.sleep(1) # Small fallback wait for DOM complete update
        
        if "Just a moment..." in driver.page_source or "Cloudflare" in driver.page_source:
            print("Cloudflare bot protection triggered on product page.")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        company_name = "N/A"
        medicine_name = "N/A"
        composition = "N/A"
        price = "N/A"
        description_text = "N/A"
        image_urls = set()
        
        # 1. Title (Medicine Name)
        h1 = soup.find("h1")
        if h1:
            medicine_name = h1.get_text(strip=True)
            
        # 2. Company Name
        brand_div = soup.find("a", href=lambda h: h and "/manufacturer/" in h)
        if not brand_div:
            brand_div = soup.find(lambda tag: tag.name == "div" and tag.get("class") and any("brand" in c.lower() or "manufacturer" in c.lower() for c in tag.get("class", [])))
        if brand_div:
            company_name = brand_div.get_text(strip=True)
            
        # 3. Composition / Salt
        salt_div = soup.find("a", href=lambda h: h and "/generics/" in h)
        if not salt_div:
            salt_div = soup.find(lambda tag: tag.name == "div" and tag.get("class") and any("salt" in c.lower() for c in tag.get("class", [])))
        if salt_div:
            composition = salt_div.get_text(strip=True)
            
        # 4. Price
        # Look for a span containing price
        price_wrapper = soup.find("span", text=re.compile(r'MRP|₹'))
        if price_wrapper:
            price_text = price_wrapper.find_parent().get_text(separator=' ', strip=True) if price_wrapper.find_parent() else price_wrapper.get_text(strip=True)
            match = re.search(r'₹\s?[0-9,.]+', price_text)
            if match:
                price = match.group(0).replace('₹', '').replace(',', '').strip()
        
        if price == "N/A":
             # fallback finding element by class containing price
             price_div = soup.find(lambda tag: tag.name == "span" and tag.get("class") and any("price" in c.lower() or "mrp" in c.lower() for c in tag.get("class", [])))
             if price_div:
                 price_text = price_div.get_text(strip=True)
                 match = re.search(r'₹[0-9,.]+', price_text)
                 if match:
                     price = match.group(0).replace('₹', '').replace(',', '').strip()
                     
        # 5. Description
        desc_div = soup.find("div", {"id": "aboutexpand"})
        if not desc_div:
            desc_div = soup.find("div", {"class": re.compile(r"ProductDescription|product-description", re.I)})
        if not desc_div:
            desc_div = soup.find(lambda tag: tag.name == "div" and tag.get("class") and any("description" in c.lower() for c in tag.get("class", [])))
            
        if desc_div:
             texts = desc_div.stripped_strings
             description_text = "\n".join(texts)
             if not description_text:
                 description_text = "N/A"
             
        # 6. Images
        img_tags = soup.find_all("img")
        for img in img_tags:
            src = img.get("src")
            if src and "http" in src and ("/image/upload/" in src):
                image_urls.add(src)
                
        # Ensure we don't have empty critical fields
        if not medicine_name or medicine_name == "N/A":
            # If no h1 found, grab from title tag
            if soup.title:
                medicine_name = soup.title.get_text(strip=True).split('|')[0].strip()
            
        return {
            "companyName": company_name,
            "medicineName": medicine_name,
            "composition": composition,
            "price": price,
            "description": description_text,
            "image_urls": list(image_urls)
        }
        
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return None

def clean_filename(name):
    # Remove spaces and special characters for a clean filename
    return re.sub(r'[^a-zA-Z0-9]+', '', name)

def download_images(session, image_urls, product_name, save_dir):
    """Downloads images for a product and returns comma-separated filenames."""
    if not image_urls:
        return ""
        
    cleaned_name = clean_filename(product_name)
    if not cleaned_name:
        cleaned_name = "product"
        
    os.makedirs(save_dir, exist_ok=True)
    
    saved_filenames = []
    
    # Optional logic: just limit to say max 5 images if there are too many thumbnails
    image_urls = list(image_urls)[:10]
    
    for i, url in enumerate(image_urls, start=1):
        filename_base = cleaned_name if len(image_urls) == 1 else f"{cleaned_name}{i}"
        filename = f"{filename_base}.png"
        filepath = os.path.join(save_dir, filename)
        
        # Avoid duplicate downloads across different products referring same image
        if filename in saved_filenames:
             continue
             
        # Optional: check if file already exists locally
        if os.path.exists(filepath):
             saved_filenames.append(filename)
             continue
            
        try:
            r = session.get(url, stream=True, timeout=10)
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            saved_filenames.append(filename)
            time.sleep(0.2)
        except Exception as e:
            print(f"Failed to download image {url}: {e}")
            
    return ",".join(saved_filenames)

def save_data(data, output_file):
    """Saves data to an Excel file with text-wrapping enabled."""
    df = pd.DataFrame(data)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Using openpyxl to format the cells neatly
    try:
        import openpyxl
    except ImportError:
        print("Please install openpyxl to save as Excel.")
        return
        
    writer = pd.ExcelWriter(output_file, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Products')
    
    workbook = writer.book
    worksheet = writer.sheets['Products']
    
    # Apply text wrapping and appropriate column widths
    for i, col_name in enumerate(df.columns, start=1):
        column_letter = openpyxl.utils.get_column_letter(i)
        # Set max width to 50 for readability
        worksheet.column_dimensions[column_letter].width = min(
            max(df[col_name].astype(str).map(len).max(), len(col_name)) + 2, 
            60
        )
        
    # Wrap text for all cells
    for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
        for cell in row:
            cell.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
            
    writer.close()
    print(f"Data saved successfully to {output_file}")


def main():
    base_url = os.environ.get("BASE_URL", "https://www.1mg.com/search/all?name=mankind")
    max_products = int(os.environ.get("MAX_PRODUCTS", "100"))
    output_dir = os.environ.get("OUTPUT_FOLDER", "mankind")
    images_dir = os.path.join(output_dir, "images")
    output_excel = os.path.join(output_dir, "data.xlsx")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # Session for downloading images efficiently
    session = setup_session()
    # Driver for navigating dynamic HTML pages
    print("Initializing browser driver...")
    driver = setup_driver()
    
    try:
        print(f"Fetching up to {max_products} product links...")
        product_links = fetch_product_links(driver, base_url, max_products)
        print(f"Gathered {len(product_links)} product links.")
        
        if not product_links:
            print("No products to process. This usually indicates layout change or bot blocking.")
            return
            
        all_products_data = []
        
        for i, link in enumerate(product_links, 1):
            print(f"[{i}/{len(product_links)}] Scraping: {link}")
            product_info = parse_product_page(driver, link)
            
            if not product_info:
                print("Failed to extract data, skipping.")
                continue
                
            img_urls = product_info.pop("image_urls", [])
            # still use requests session for fast image downloading
            image_names = download_images(session, img_urls, product_info['medicineName'], images_dir)
            product_info['imageName'] = image_names
            
            all_products_data.append(product_info)
            
        if all_products_data:
            save_data(all_products_data, output_excel)
        else:
            print("No product data collected.")
            
    finally:
        is_headless = os.environ.get("HEADLESS", "False").lower() == "true"
        if not is_headless:
            print("Browser is still open for you to inspect. Press Enter in this terminal to close the browser.")
            input("Press Enter to close browser...")
        print("Closing browser driver.")
        driver.quit()

if __name__ == "__main__":
    main()
