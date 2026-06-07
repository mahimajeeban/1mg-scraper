import os
import time
import json
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import setup_logger

logger = setup_logger(__name__)

try:
    import google.genai as genai
    from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded
    GENAI_AVAILABLE = True
except ImportError:
    try:
        # Fallback to old package
        import google.generativeai as genai
        from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded
        GENAI_AVAILABLE = True
    except ImportError:
        GENAI_AVAILABLE = False

class ProductParser:
    """Extracts detailed information from a single product page using Gemini LLM."""
    
    def __init__(self, driver_manager, api_key=None, default_company=None):
        self.driver_manager = driver_manager
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.default_company = default_company or "Unknown"
        self.llm_enabled = False
        
        if self.api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.llm_enabled = True
                logger.info("ProductParser initialized with Gemini LLM extraction.")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini API: {e}. Falling back to CSS selectors.")
        else:
            if not GENAI_AVAILABLE:
                logger.warning("google-generativeai not installed. Using CSS selector fallback.")
            elif not self.api_key:
                logger.warning("GEMINI_API_KEY not found. Using CSS selector fallback.")

    def parse(self, url):
        """Extract product data from URL using LLM or CSS fallback."""
        driver = self.driver_manager.get_driver()
        
        # Load the page with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                driver.get(url)
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
        
        # Wait for description area
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#aboutexpand, div.ProductDescription, div[class*='description']"))
            )
        except TimeoutException:
            pass

        time.sleep(1)
        
        # Try to click "Read More" buttons to expand content
        try:
            driver.execute_script("""
                var elements = document.querySelectorAll("span, div, a, button, label");
                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].innerText ? elements[i].innerText.toLowerCase().trim() : "";
                    if (text === "read more" || text === "show more" || text === "view more") {
                        elements[i].click();
                    }
                }
            """)
            time.sleep(1)
        except Exception:
            pass
            
        # Check for Cloudflare
        if "Just a moment..." in driver.page_source or "Cloudflare" in driver.page_source:
            logger.error("Cloudflare bot protection triggered on product page.")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract images (keep this in HTML parsing - it's reliable)
        image_urls = self._extract_images(soup)
        
        # Try LLM extraction first
        if self.llm_enabled:
            product_data = self._extract_with_llm(driver, url)
            if product_data:
                product_data['image_urls'] = list(image_urls)
                return product_data
            logger.warning(f"LLM extraction failed for {url}, falling back to CSS selectors")
        
        # Fallback to CSS selectors
        return self._extract_with_css(soup, image_urls)

    def _extract_with_llm(self, driver, url):
        """Extract product data using Gemini LLM."""
        try:
            # Get visible text from page
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Trim to reasonable length (12000 chars ~ 3000 tokens)
            # Increased to ensure composition sections are not cut off
            if len(page_text) > 12000:
                page_text = page_text[:12000]
            
            # Construct prompt
            prompt = f"""You are a product data extractor for a medical e-commerce website.
Extract the following fields from the product page text and return ONLY valid JSON (no markdown, no explanations):

{{
  "medicineName": "full product name",
  "companyName": "manufacturer/brand name (default to '{self.default_company}' if unclear)",
  "price": "MRP price as a number (e.g., 99.0) or 'N/A'",
  "composition": "CRITICAL: You MUST find composition/ingredients. Scan the ENTIRE text carefully for ANY of these labels (case-insensitive): 'SALT COMPOSITION', 'Key Ingredients', 'Ingredients', 'Active Ingredients', 'Composition', 'Contains', 'Key Actives', 'Active Substance', 'Formulation'. It will appear as a list of chemical names or ingredient names. Extract all items and join with ' + '. If you truly cannot find it after scanning the entire text, only then use 'N/A'.",
  "summary": "Write EXACTLY 1-2 sentences (max 30 words). Quick overview for customers.",
  "description": "Write EXACTLY 3-4 sentences only (max 60 words total). Cover: what the product is, primary purpose, key benefits, who it's for. Do NOT include composition/ingredients here. Focus ONLY on use and benefits."
}}

CRITICAL RULES:
1. **Composition**: MUST extract if present. Scan entire text. Chemical/ingredient names will appear after one of the labels above.
2. **Description**: STRICT LIMIT - exactly 3-4 sentences, max 60 words. Focus on USE not INGREDIENTS.
3. Composition and description are SEPARATE fields - NEVER mix them.

Return ONLY the JSON object, nothing else.

Page text:
{page_text}"""

            # Call Gemini with retry logic
            max_retries = 3
            base_delay = 5
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    if not response.text:
                        logger.warning("Empty response from Gemini")
                        continue
                    
                    # Parse JSON response
                    response_text = response.text.strip()
                    
                    # Remove markdown code blocks if present
                    if response_text.startswith("```"):
                        response_text = re.sub(r'^```json?\s*', '', response_text)
                        response_text = re.sub(r'\s*```$', '', response_text)
                    
                    data = json.loads(response_text)
                    
                    # Validate required fields
                    required_fields = ["medicineName", "companyName", "price", "composition", "summary", "description"]
                    if all(field in data for field in required_fields):
                        # Convert price to float if possible
                        try:
                            if data['price'] != "N/A":
                                data['price'] = float(str(data['price']).replace(',', '').replace('₹', '').strip())
                        except (ValueError, AttributeError):
                            data['price'] = "N/A"
                        
                        # Format description: ProductName\n\nSummary\n\nRead More...\n\nFull Description
                        formatted_desc = f"{data['medicineName']}\n\n{data['summary']}\n\nRead More...\n\n{data['description']}"
                        
                        return {
                            "companyName": data['companyName'],
                            "medicineName": data['medicineName'],
                            "composition": data['composition'],
                            "price": data['price'],
                            "description": formatted_desc
                        }
                    else:
                        logger.warning(f"Missing fields in LLM response: {data.keys()}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from Gemini response: {e}")
                    logger.debug(f"Response text: {response_text[:200]}")
                    
                except (ResourceExhausted, DeadlineExceeded) as e:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Gemini API rate limit/timeout (Attempt {attempt+1}/{max_retries}). Waiting {delay}s...")
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"LLM extraction error: {e}")
                    break
            
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM extraction: {e}")
            return None

    def _extract_with_css(self, soup, image_urls):
        """Fallback extraction using CSS selectors (original method)."""
        company_name = self.default_company
        medicine_name = "N/A"
        composition = ""
        price = "N/A"
        description_text = "N/A"
        
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
        
        exact_mrp_tag = soup.find(class_=re.compile(r'DrugPriceBox__slashed-price', re.I))
        if exact_mrp_tag:
            price_text_found = exact_mrp_tag.get_text(separator=' ', strip=True)
            
        if not price_text_found:
            exact_price_tag = soup.find(class_=re.compile(r'DrugPriceBox__best-price|DrugPriceBox__price|PriceBoxPlanOption__offer-price', re.I))
            if exact_price_tag:
                price_text_found = exact_price_tag.get_text(separator=' ', strip=True)

        if not price_text_found:
            price_divs = soup.find_all(lambda tag: tag.name in ["span", "div"] and tag.get("class") and any("price" in c.lower() or "mrp" in c.lower() for c in tag.get("class", [])))
            for div in price_divs:
                classes = " ".join(div.get("class", [])).lower()
                if "substitute" in classes:
                    continue
                t = div.get_text(separator=' ', strip=True)
                if '₹' in t:
                    price_text_found = t
                    break
                    
        if not price_text_found:
            for tag in soup.find_all(["span", "div"]):
                classes = " ".join(tag.get("class", [])).lower() if tag.get("class") else ""
                if "substitute" in classes:
                    continue
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
            intro_title = soup.find("h2", string=re.compile(r"Product introduction", re.I))
            if intro_title and intro_title.find_next_sibling("div", class_=re.compile(r"DrugOverview__content", re.I)):
                desc_div = intro_title.find_next_sibling("div")
        if not desc_div:
            desc_div = soup.find(lambda tag: tag.name == "div" and tag.get("class") and any("description" in c.lower() for c in tag.get("class", [])))
            
        if desc_div:
            raw_text = " ".join(desc_div.stripped_strings)
            clean_text = re.sub(r'\s+', ' ', raw_text).strip()
            clean_text = re.sub(r'(?i)\b(read more|show more|view more|show less)\b', '', clean_text).strip()
            
            if clean_text:
                description_text = f"{medicine_name}\n{clean_text}"
             
        return {
            "companyName": company_name,
            "medicineName": medicine_name,
            "composition": composition,
            "price": price,
            "description": description_text,
            "image_urls": list(image_urls)
        }

    def _extract_images(self, soup):
        """Extract product image URLs from HTML."""
        image_urls = set()
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
        
        return image_urls
