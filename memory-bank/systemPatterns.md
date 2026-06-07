# System Patterns: Architecture & Design Decisions

## System Architecture

### High-Level Flow
```
scraper.py (Orchestrator)
    ↓
    ├─→ DriverManager (browser setup)
    ├─→ SessionManager (HTTP session for images)
    ├─→ ProductLinkFetcher (collect URLs from search)
    ├─→ ProductParser (extract data from each product page)
    │       ↓
    │       ├─→ Gemini LLM (intelligent extraction)
    │       └─→ CSS Selectors (fallback)
    ├─→ ImageDownloader (save images locally)
    └─→ ExcelManager (format and save Excel)
```

### Module Relationships

#### 1. `scraper.py` - Main Orchestrator
**Responsibility**: Coordinate the entire scraping pipeline
**Dependencies**: All other modules
**Key Logic**:
- Reads `.env` configuration
- Creates output directories
- Orchestrates: fetch links → parse products → download images → save Excel
- Handles final summary printing
- Keeps browser open in headed mode for inspection

**CRITICAL DESIGN DECISION**:
```python
# Default company name is derived from OUTPUT_FOLDER
company_name = self.output_dir.capitalize()
self.parser = ProductParser(self.driver_manager, default_company=company_name)
```
**Why**: If LLM can't find company name, use folder name (e.g., "mankind" → "Mankind")

#### 2. `driver_manager.py` - WebDriver Lifecycle
**Responsibility**: Selenium WebDriver setup, health checks, teardown
**Key Patterns**:
- **Singleton pattern**: Reuses same driver instance across all requests
- **Lazy initialization**: Driver created on first `get_driver()` call
- **Health check**: `_is_driver_alive()` tests connection before reuse
- **Retry logic**: 3 attempts with exponential backoff (3s, 6s, 9s)

**CRITICAL CONSTRAINT - Proxy Bypass**:
```python
if self.use_proxy_bypass:
    options.add_argument("--proxy-bypass-list=localhost,127.0.0.1,::1,<local>")
```
**Why**: Corporate proxies block Selenium→ChromeDriver communication on localhost
**Do NOT remove**: Essential for enterprise environments

**Anti-Detection**:
- `--disable-blink-features=AutomationControlled` - Hides Selenium detection
- Real user agent string
- `page_load_strategy = 'eager'` - Don't wait for all resources

#### 3. `link_fetcher.py` - Pagination Handler
**Responsibility**: Collect all product URLs from infinite scroll search page
**Key Algorithm**:
```
1. Load search page
2. While (links < max_products AND scroll_attempts < 50):
   a. Parse HTML for product links (/otc/ or /drugs/)
   b. Scroll to last product element (smooth scroll)
   c. Wait 3 seconds for new content to load
   d. If no new links AND no height change → nudge scroll and recheck
   e. If still no change → end of page, break
3. Return first max_products links
```

**CRITICAL TIMING**:
- 3-second delays between scrolls are **non-negotiable**
- Mimics human reading time
- Reduces Cloudflare suspicion
- Allows network requests to complete

**Cloudflare Detection**:
```python
if "Just a moment..." in driver.page_source or "Cloudflare" in driver.page_source:
    logger.error("Cloudflare bot protection triggered...")
    return links  # Empty or partial results
```

#### 4. `parser.py` - Data Extraction Engine
**Responsibility**: Extract structured data from individual product pages
**Two-Strategy Pattern**:

**Strategy 1: LLM Extraction (Primary)**
- Uses Gemini 1.5 Flash
- Sends page text (trimmed to 6000 chars)
- Prompt requests JSON with: `medicineName, companyName, price, composition, summary, description`
- Parses JSON (strips markdown code blocks)
- **Formats description**: `"{medicineName}\n\n{summary}\n\nRead More...\n\n{description}"`
- Retry logic: 3 attempts with exponential backoff (5s, 10s, 20s)

**Strategy 2: CSS Selectors (Fallback)**
- Finds elements by class patterns (e.g., `DrugPriceBox__slashed-price`)
- Extracts text and cleans formatting
- Description format: `"{medicineName}\n{cleanText}"`

**CRITICAL CONSTRAINT - Description Format**:
```python
# LLM path:
formatted_desc = f"{data['medicineName']}\n\n{data['summary']}\n\nRead More...\n\n{data['description']}"

# CSS path:
description_text = f"{medicine_name}\n{clean_text}"
```
**Do NOT change**: Excel formatting and business logic depend on this structure

**"Read More" Button Handling**:
```javascript
// Clicks all "read more" buttons via JavaScript injection
var elements = document.querySelectorAll("span, div, a, button, label");
for (var i = 0; i < elements.length; i++) {
    var text = elements[i].innerText ? elements[i].innerText.toLowerCase().trim() : "";
    if (text === "read more" || text === "show more" || text === "view more") {
        elements[i].click();
    }
}
```

**Image Extraction**:
- Always uses HTML parsing (reliable, no LLM needed)
- Filters for product images: `/image/upload/` or `w_380` or `w_700` or `picture-image` class
- Excludes social media icons

#### 5. `downloader.py` - Image Management
**Responsibility**: Download and deduplicate product images
**Key Logic**:
- Cleans filename: removes non-alphanumeric characters
- Limit: First 10 images per product
- Naming: `{productName}.png`, `{productName}1.png`, `{productName}2.png`, ...
- **Deduplication**: Checks `os.path.exists(filepath)` before downloading
- Retry: 3 attempts with exponential backoff (1s, 2s, 4s)
- Rate limiting: 1-second delay between downloads

**CRITICAL PATTERN - Filename Return**:
```python
saved_filenames = []  # ["ProductA.png", "ProductA1.png"]
return ",".join(saved_filenames)  # "ProductA.png,ProductA1.png"
```

**Used by scraper.py**:
```python
formatted_paths = [f"./images/{fname}" for fname in saved_filenames_str.split(',')]
product_info['imageLink'] = ",\n".join(formatted_paths)
# Result: "./images/ProductA.png,\n./images/ProductA1.png"
```

#### 6. `excel_manager.py` - Output Formatter
**Responsibility**: Create professionally formatted Excel file
**Fixed Schema**:
```python
columns_order = ["companyName", "medicineName", "composition", "price", "description", "imageLink"]
```
**Do NOT modify**: Business reports depend on this exact order

**Formatting Rules**:
- Headers: Bold, 12pt, centered, bordered
- Description column: 80 chars wide (for long summaries)
- ImageLink column: 30 chars wide (multiple paths)
- Other columns: Auto-width (max 50 chars)
- All cells: Wrap text, top-aligned, bordered
- CSV fallback if openpyxl not installed

#### 7. `session_manager.py` - HTTP Client
**Responsibility**: Configured requests.Session for image downloads
**Retry Strategy**:
- Total retries: 5
- Backoff: 2, 4, 8, 16, 32 seconds
- Retry on: 429, 500, 502, 503, 504 status codes
- Only for: HEAD, GET, OPTIONS methods

**Headers**: Real browser headers to avoid blocking

#### 8. `summarizer.py` - LEGACY MODULE
**Status**: **NO LONGER USED IN PRODUCTION**
**History**: Previously called to generate summaries separately
**Current State**: `scraper.py` does NOT import or use this module
**Why Keep**: May be useful for future enhancements or standalone summarization
**Migration**: LLM in `parser.py` now handles summary inline

#### 9. `utils.py` - Logging Setup
**Responsibility**: Configure logging and suppress noisy libraries
**Pattern**: Shared logger factory function
**Suppressions**:
- TensorFlow warnings
- Selenium debug logs
- urllib3 connection logs
- Google API internal logs

## Key Design Decisions

### 1. Why Single Driver Instance?
**Decision**: Reuse same WebDriver across all page visits
**Reasoning**:
- Faster: No startup overhead per product
- Maintains session/cookies (reduces bot detection)
- Lower memory footprint
**Trade-off**: If driver crashes, entire scrape fails (acceptable for batch jobs)

### 2. Why Separate SessionManager from DriverManager?
**Decision**: Selenium for HTML, Requests for images
**Reasoning**:
- Images don't need JavaScript
- Requests is faster and more efficient for binary downloads
- Separation of concerns
- Parallel capabilities (could download images async in future)

### 3. Why Trim Page Text to 6000 Chars?
**Decision**: Send only first 6000 characters to Gemini
**Reasoning**:
- ~1500 tokens (within context limits)
- Product info is usually in first half of page
- Reduces API costs
- Faster responses

### 4. Why Exponential Backoff Everywhere?
**Decision**: All retry logic uses exponential delays
**Reasoning**:
- Respects rate limits (don't hammer failing endpoints)
- Gives transient issues time to resolve
- Industry best practice

### 5. Why Cloudflare Checks in Multiple Places?
**Decision**: Check in both `link_fetcher` and `parser`
**Reasoning**:
- Search page may have different protections than product pages
- Early detection prevents wasting time
- Clear error messages help user troubleshoot

## Critical Implementation Paths

### Path 1: Successful Product Extraction
```
scraper.run()
  → link_fetcher.fetch() returns 100 URLs
  → for each URL:
      → parser.parse(url)
          → driver.get(url)
          → parser._extract_with_llm() succeeds
          → returns {companyName, medicineName, composition, price, description, image_urls}
      → downloader.download() saves images, returns "img1.png,img2.png"
      → scraper formats imageLink as "./images/img1.png,\n./images/img2.png"
      → product_info added to all_products_data[]
  → excel_manager.save() writes Excel
  → Success summary printed
```

### Path 2: LLM Quota Exceeded
```
parser._extract_with_llm()
  → Gemini API raises ResourceExhausted
  → Retry 3 times with backoff
  → All retries fail
  → Returns None
parser.parse() sees None
  → logs "LLM extraction failed, falling back..."
  → parser._extract_with_css() executes
  → Returns data (CSS-extracted)
→ Scraper continues normally
```

### Path 3: Individual Product Failure
```
scraper.run()
  → parser.parse(url) returns None (timeout/Cloudflare/parsing error)
  → scraper logs warning
  → Adds URL to failed_products[]
  → Continues with next product
  → Final summary shows X/100 success, Y/100 failed
```

## Anti-Patterns to Avoid

❌ **Don't remove retry logic** - Network failures are common
❌ **Don't change column order** - Business reports hardcoded
❌ **Don't make LLM mandatory** - Must work without API key
❌ **Don't remove proxy bypass** - Breaks corporate deployments
❌ **Don't reduce delays** - Increases Cloudflare detection risk
❌ **Don't add new columns without documenting** - Excel schema is contract
❌ **Don't remove Cloudflare checks** - Silent failures are worse than loud errors
