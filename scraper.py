import os
import shutil
from dotenv import load_dotenv

from utils import setup_logger
from driver_manager import DriverManager
from session_manager import SessionManager
from link_fetcher import ProductLinkFetcher
from parser import ProductParser
from downloader import ImageDownloader
from excel_manager import ExcelManager

logger = setup_logger(__name__)

class MainScraper:
    """Controller class orchestrating the entire scraping process."""
    
    def __init__(self):
        load_dotenv()
        # Support comma-separated list of companies
        company_names_str = os.environ.get("COMPANY_NAME", "mankind")
        self.company_names = [name.strip() for name in company_names_str.split(",")]
        
        self.base_url_template = os.environ.get("BASE_URL", "https://www.1mg.com/search/all?name=")
        self.max_products = int(os.environ.get("MAX_PRODUCTS", "100"))
        self.batch_size = 100  # Products per batch folder
        self.is_headless = os.environ.get("HEADLESS", "False").lower() == "true"
        self.use_proxy_bypass = os.environ.get("USE_PROXY_BYPASS", "False").lower() == "true"
        
        # Base products directory
        self.products_base_dir = "products"
        os.makedirs(self.products_base_dir, exist_ok=True)
        
        self.driver_manager = DriverManager(
            headless=self.is_headless,
            use_proxy_bypass=self.use_proxy_bypass
        )
        self.session_manager = SessionManager()
        
        self.link_fetcher = ProductLinkFetcher(self.driver_manager)
        self.downloader = ImageDownloader(self.session_manager)
        self.excel_manager = ExcelManager()
    
    def _cleanup_old_folders(self, company_name):
        """Remove all existing batch folders for this company."""
        pattern = f"{company_name}_"
        for item in os.listdir(self.products_base_dir):
            if item.startswith(pattern) or item == company_name:
                folder_path = os.path.join(self.products_base_dir, item)
                if os.path.isdir(folder_path):
                    logger.info(f"Removing old folder: {folder_path}")
                    shutil.rmtree(folder_path)
    
    def _get_batch_folder(self, company_name, batch_num):
        """Get the folder path for a specific batch number."""
        if batch_num == 1:
            folder_name = f"{company_name}_1"
        else:
            folder_name = f"{company_name}_{batch_num}"
        
        batch_dir = os.path.join(self.products_base_dir, folder_name)
        images_dir = os.path.join(batch_dir, "images")
        
        os.makedirs(batch_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        
        return batch_dir, images_dir

    def run_for_company(self, company_name):
        """Run scraping process for a single company."""
        logger.info(f"\n{'#'*70}")
        logger.info(f"# Starting scraping for company: {company_name.upper()}")
        logger.info(f"{'#'*70}\n")
        
        # Clean up old folders for this company
        self._cleanup_old_folders(company_name)
        
        # Build URL for this company
        base_url = self.base_url_template + company_name
        
        # Create parser for this company
        parser = ProductParser(self.driver_manager, default_company=company_name.capitalize())
        
        logger.info(f"Fetching up to {self.max_products} product links from {base_url}...")
        product_links = self.link_fetcher.fetch(base_url, self.max_products)
        logger.info(f"Gathered {len(product_links)} product links for {company_name}.")
        
        if not product_links:
            logger.warning(f"No products found for {company_name}. Skipping.")
            return {
                'company': company_name,
                'total_success': 0,
                'total_failed': 0,
                'total_products': 0,
                'batch_summaries': []
            }
        
        # Calculate number of batches needed
        total_batches = (len(product_links) + self.batch_size - 1) // self.batch_size
        logger.info(f"Will create {total_batches} batch folder(s) with max {self.batch_size} products each")
        
        all_failed_products = []
        batch_summaries = []
        
        # Process products in batches
        for batch_num in range(1, total_batches + 1):
            start_idx = (batch_num - 1) * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(product_links))
            batch_links = product_links[start_idx:end_idx]
            
            logger.info(f"\n{'='*70}")
            logger.info(f"Processing Batch {batch_num}/{total_batches} ({len(batch_links)} products)")
            logger.info(f"{'='*70}\n")
            
            # Get batch folder paths
            batch_dir, images_dir = self._get_batch_folder(company_name, batch_num)
            
            batch_products_data = []
            batch_failed = []
            
            for i, link in enumerate(batch_links, 1):
                global_idx = start_idx + i
                logger.info(f"[{global_idx}/{len(product_links)}] Scraping: {link}")
                product_info = parser.parse(link)
                
                if not product_info:
                    logger.warning(f"Failed to extract data for {link}, skipping.")
                    batch_failed.append(link)
                    continue
                
                # Handle Image Downloading
                img_urls = product_info.pop("image_urls", [])
                saved_filenames_str = self.downloader.download(img_urls, product_info['medicineName'], images_dir)
                
                if saved_filenames_str:
                    formatted_paths = [f"./images/{fname}" for fname in saved_filenames_str.split(',')]
                    product_info['imageLink'] = ",\n".join(formatted_paths)
                else:
                    product_info['imageLink'] = ""
                
                batch_products_data.append(product_info)
            
            # Save batch Excel file
            if batch_products_data:
                excel_path = os.path.join(batch_dir, "data.xlsx")
                self.excel_manager.save(batch_products_data, excel_path)
                logger.info(f"Batch {batch_num}: Saved {len(batch_products_data)} products to {excel_path}")
            
            # Track batch summary
            batch_summaries.append({
                'batch_num': batch_num,
                'folder': batch_dir,
                'success': len(batch_products_data),
                'failed': len(batch_failed),
                'total': len(batch_links)
            })
            all_failed_products.extend(batch_failed)
        
        # Return company summary
        return {
            'company': company_name,
            'total_success': sum(b['success'] for b in batch_summaries),
            'total_failed': len(all_failed_products),
            'total_products': len(product_links),
            'batch_summaries': batch_summaries
        }
    
    def run(self):
        """Main entry point: runs scraping for all configured companies."""
        try:
            logger.info(f"Starting scraping for {len(self.company_names)} company(ies): {', '.join(self.company_names)}")
            
            company_summaries = []
            
            # Process each company
            for company_name in self.company_names:
                summary = self.run_for_company(company_name)
                company_summaries.append(summary)
            
            # Print combined summary across all companies
            print("\n" + "="*70)
            print("OVERALL SCRAPING SUMMARY - ALL COMPANIES")
            print("="*70)
            
            for summary in company_summaries:
                company = summary['company']
                total_success = summary['total_success']
                total_failed = summary['total_failed']
                total_products = summary['total_products']
                
                print(f"\n📦 Company: {company.upper()}")
                print(f"   ✅ Successfully scraped: {total_success}/{total_products} products")
                print(f"   ❌ Failed: {total_failed}/{total_products} products")
                
                if summary['batch_summaries']:
                    print(f"   Batch Breakdown:")
                    for batch in summary['batch_summaries']:
                        print(f"      Batch {batch['batch_num']}: {batch['success']}/{batch['total']} products → {batch['folder']}")
            
            # Grand totals
            grand_total_success = sum(s['total_success'] for s in company_summaries)
            grand_total_failed = sum(s['total_failed'] for s in company_summaries)
            grand_total_products = sum(s['total_products'] for s in company_summaries)
            
            print(f"\n{'='*70}")
            print(f"GRAND TOTAL:")
            print(f"✅ Total Success: {grand_total_success}/{grand_total_products} products")
            print(f"❌ Total Failed: {grand_total_failed}/{grand_total_products} products")
            print("="*70 + "\n")
                
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
