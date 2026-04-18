import os
import requests
import re
from urllib.parse import urlparse

class Downloader:
    def __init__(self, base_dir='images'):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }

    def _sanitize_folder_name(self, name):
        """Clean name for valid folder creation."""
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        return clean_name[:50].strip() # Limit length to avoid path-too-long errors

    def download_product_images(self, product_name, image_urls):
        """Download a list of images into a product-specific folder."""
        folder_name = self._sanitize_folder_name(product_name)
        if not folder_name:
            folder_name = "unknown_product"
            
        product_dir = os.path.join(self.base_dir, folder_name)
        os.makedirs(product_dir, exist_ok=True)

        downloaded_paths = []
        for i, url in enumerate(image_urls):
            if not url or not url.startswith('http'):
                continue
            
            try:
                # Determine extension
                parsed = urlparse(url)
                ext = os.path.splitext(parsed.path)[1]
                if not ext:
                    ext = '.jpg'

                filename = f"image_{i+1}{ext}"
                filepath = os.path.join(product_dir, filename)
                
                # Fetching image
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    downloaded_paths.append(filepath)
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                
        return product_dir
