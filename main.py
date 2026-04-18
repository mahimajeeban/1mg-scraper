import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from storage import Storage
from downloader import Downloader
import os

class ProductScraper:
    def __init__(self, base_url, max_pages=None, scratch_dir='.'):
        self.base_url = base_url
        self.max_pages = max_pages
        self.domain = 'https://www.1mg.com'
        
        # Keep outputs inside project
        csv_path = os.path.join(scratch_dir, 'data.csv')
        excel_path = os.path.join(scratch_dir, 'data.xlsx')
        images_dir = os.path.join(scratch_dir, 'images')
        
        self.storage = Storage(csv_filepath=csv_path, excel_filepath=excel_path)
        self.downloader = Downloader(base_dir=images_dir)
        
        print("Initializing Headless Browser...")
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--log-level=3')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
        self.driver = webdriver.Chrome(options=options)

    def close(self):
        print("Closing browser and exporting Excel sheet...")
        self.driver.quit()
        self.storage.export_to_excel()

    def run(self):
        page = 1
        product_urls = set()
        
        print(f"\n====== Phase 1: Category Scraping ======")
        while True:
            if self.max_pages and page > self.max_pages:
                break
                
            page_url = f"{self.base_url}?page={page}" if page > 1 else self.base_url
            print(f"Fetching Listing Page {page}: {page_url}")
            
            self.driver.get(page_url)
            time.sleep(3)  # Allow JS and Vue hydration to process
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            links = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if href and ('/otc/' in href or '/drugs/' in href):
                    links.append(href)
                    
            links = list(set(links)) # Unique on page
            
            if not links:
                print("No product links found on page (may be bot-blocked or end of catalog). Breaking loop.")
                break
                
            new_links = 0
            for link in links:
                full_url = urljoin(self.domain, link)
                if full_url not in product_urls:
                    product_urls.add(full_url)
                    new_links += 1
            
            if new_links == 0:
                print("No new unique products found on page. Breaking loop.")
                break
                
            page += 1

        print(f"\nPhase 1 Complete. Total products found: {len(product_urls)}")
        print(f"\n====== Phase 2: Details Scraping ======")
        
        for idx, p_url in enumerate(list(product_urls)):
            print(f"Scraping Product [{idx+1}/{len(product_urls)}]: {p_url}")
            self._scrape_product_details(p_url)

    def _scrape_product_details(self, url, retries=3):
        for attempt in range(retries):
            try:
                self.driver.get(url)
                time.sleep(2.5) # Wait for elements
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Name
                name = 'N/A'
                h1 = soup.find('h1')
                if h1:
                    name = h1.get_text(strip=True)
                
                # Price
                price = 'N/A'
                price_elems = soup.find_all(string=lambda t: t and '₹' in t)
                if price_elems:
                    price = price_elems[0].strip()
                    
                # Description
                description = 'N/A'
                desc_divs = soup.find_all('div')
                for div in desc_divs:
                    div_id = div.get('id', '')
                    if div_id and ('description' in div_id.lower() or 'information' in div_id.lower()):
                        description = div.get_text(separator=' ', strip=True)
                        break
                
                if description == 'N/A':
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        description = meta_desc.get('content', 'N/A')

                # Filter lengthy descriptions to prevent sheet breakage
                if len(description) > 5000:
                    description = description[:5000] + '... [Truncated]'

                # Image Extractor
                images = []
                for img in soup.find_all('img'):
                    src = img.get('src')
                    if src and src.startswith('http') and ('gumlet' in src or 'product' in src):
                        if '1X1' not in src.upper() and 'sso.png' not in src:
                            images.append(src)
                
                images = list(dict.fromkeys(images)) # filter dupes
                
                # Media Download
                folder_path = 'N/A'
                if images and name != 'N/A':
                    folder_path = self.downloader.download_product_images(name, images)
                
                product_data = {
                    'Name': name,
                    'Price': price,
                    'Description': description,
                    'Product_URL': url,
                    'Image_Folder': folder_path,
                    'Image_URLs': ', '.join(images) # Join correctly for a single string cell
                }
                
                self.storage.append_product(product_data)
                break
                
            except Exception as e:
                print(f"Attempt {attempt+1}/{retries} failed for {url}: {e}")
                time.sleep(2)

if __name__ == "__main__":
    import os
    BASE_URL = 'https://www.1mg.com/categories/vitamins-nutrition/vitamin-d-121'
    # Use max_pages=1 for demonstration/testing
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scraper = ProductScraper(BASE_URL, max_pages=1, scratch_dir=current_dir)
    
    try:
        scraper.run()
    finally:
        scraper.close()
        print("Script execution completed.")
