import os
import re
import time
from utils import setup_logger

logger = setup_logger(__name__)

class ImageDownloader:
    """Downloads images for products to the local filesystem."""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager

    def clean_filename(self, name):
        return re.sub(r'[^a-zA-Z0-9]+', '', name)

    def download(self, image_urls, product_name, save_dir):
        if not image_urls:
            return ""
            
        cleaned_name = self.clean_filename(product_name)
        if not cleaned_name:
            cleaned_name = "product"
            
        os.makedirs(save_dir, exist_ok=True)
        saved_filenames = []
        image_urls = list(image_urls)[:10]
        session = self.session_manager.get_session()
        
        for i, url in enumerate(image_urls):
            filename = f"{cleaned_name}.png" if i == 0 else f"{cleaned_name}{i}.png"
            filepath = os.path.join(save_dir, filename)
            
            if filename in saved_filenames or os.path.exists(filepath):
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
                logger.error(f"Failed to download image {url}: {e}")
                
        return ",".join(saved_filenames)
