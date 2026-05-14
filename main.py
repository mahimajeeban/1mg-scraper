import os
from dotenv import load_dotenv

from utils import setup_logger
from driver_manager import DriverManager
from session_manager import SessionManager
from link_fetcher import ProductLinkFetcher
from parser import ProductParser
from downloader import ImageDownloader
from summarizer import DescriptionSummarizer
from excel_manager import ExcelManager

logger = setup_logger(__name__)

class MainScraper:
    """Controller class orchestrating the entire scraping process."""
    
    def __init__(self):
        load_dotenv()
        self.base_url = os.environ.get("BASE_URL", "https://www.1mg.com/search/all?name=mankind")
        self.max_products = int(os.environ.get("MAX_PRODUCTS", "100"))
        self.output_dir = os.environ.get("OUTPUT_FOLDER", "mankind")
        self.images_dir = os.path.join(self.output_dir, "images")
        self.output_excel = os.path.join(self.output_dir, "data.xlsx")
        self.is_headless = os.environ.get("HEADLESS", "False").lower() == "true"
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        self.driver_manager = DriverManager(headless=self.is_headless)
        self.session_manager = SessionManager()
        
        self.link_fetcher = ProductLinkFetcher(self.driver_manager)
        self.parser = ProductParser(self.driver_manager)
        self.downloader = ImageDownloader(self.session_manager)
        self.summarizer = DescriptionSummarizer()
        self.excel_manager = ExcelManager()

    def run(self):
        try:
            logger.info(f"Fetching up to {self.max_products} product links from {self.base_url}...")
            product_links = self.link_fetcher.fetch(self.base_url, self.max_products)
            logger.info(f"Gathered {len(product_links)} product links.")
            
            if not product_links:
                logger.warning("No products to process. Exiting.")
                return
                
            all_products_data = []
            
            for i, link in enumerate(product_links, 1):
                logger.info(f"[{i}/{len(product_links)}] Scraping: {link}")
                product_info = self.parser.parse(link)
                
                if not product_info:
                    logger.warning(f"Failed to extract data for {link}, skipping.")
                    continue
                    
                # Handle Image Downloading
                img_urls = product_info.pop("image_urls", [])
                image_names = self.downloader.download(img_urls, product_info['medicineName'], self.images_dir)
                product_info['imageLink'] = image_names if image_names else "N/A"
                
                # Handle LLM Summarization and formatting
                original_desc = product_info['description']
                summary = self.summarizer.summarize(original_desc)
                
                if summary:
                    # Formatting exactly as requested:
                    # Short summary
                    # Read More...
                    # Full original description
                    formatted_desc = f"{summary}\n\nRead More...\n\n{original_desc}"
                    product_info['description'] = formatted_desc
                
                all_products_data.append(product_info)
                
            if all_products_data:
                self.excel_manager.save(all_products_data, self.output_excel)
            else:
                logger.warning("No product data collected.")
                
        except Exception as e:
            logger.error(f"An unexpected error occurred during execution: {e}", exc_info=True)
        finally:
            if not self.is_headless:
                logger.info("Browser is still open for you to inspect.")
                input("Press Enter in this terminal to close browser...")
            self.driver_manager.close_driver()

if __name__ == "__main__":
    scraper = MainScraper()
    scraper.run()
