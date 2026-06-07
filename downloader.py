import os
import re
import time
from requests.exceptions import ConnectionError, Timeout, RequestException
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
                
            # Retry logic for connection errors
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    r = session.get(url, stream=True, timeout=15)
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                    saved_filenames.append(filename)
                    logger.info(f"Successfully downloaded: {filename}")
                    time.sleep(1)  # Increased delay to reduce rate limiting and connection resets
                    break  # Success, exit retry loop
                    
                except (ConnectionError, Timeout) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"Connection error for {url}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed to download image after {max_retries} attempts {url}: {e}")
                        
                except RequestException as e:
                    logger.error(f"HTTP error downloading image {url}: {e}")
                    break  # Don't retry on HTTP errors
                    
                except Exception as e:
                    logger.error(f"Unexpected error downloading image {url}: {e}")
                    break  # Don't retry on unexpected errors
                
        return ",".join(saved_filenames)
