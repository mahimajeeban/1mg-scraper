# 1mg Web Scraper 🔬💊

## Project Overview
This is an intelligent, AI-powered web scraping application that extracts product data and images from 1mg.com. Unlike traditional scrapers that rely on brittle CSS selectors, this scraper uses **Gemini AI (LLM)** to intelligently extract product information, making it robust against layout changes and inconsistent page structures.

## ✨ Key Features

### 🤖 **AI-Powered Extraction** (NEW!)
- Uses **Google Gemini 1.5 Flash** LLM to extract product data from page text
- **Layout-agnostic**: Works regardless of HTML structure changes
- **Single API call** extracts AND summarizes product information
- **Automatic fallback** to CSS selectors if API key not provided
- **Cost-effective**: ~$0.20 per 1000 products

### 📊 **Robust Data Collection**
- **Dynamic scrolling**: Handles infinite scroll pagination automatically
- **Deep extraction**: Visits each product page for comprehensive details
- **Smart retry logic**: Handles API rate limits and page load failures
- **Cloudflare detection**: Warns when bot protection is triggered

### 🖼️ **Image Management**
- Downloads up to 10 images per product
- Smart file naming based on product name
- Skips existing files (resume support)
- Stores relative paths in Excel for easy access

### 📈 **Professional Excel Output**
- Formatted columns with proper widths
- Text wrapping and borders
- Clean, readable structure
- Includes: Company, Name, Composition, Price, Description, Image Paths

### 🔧 **Easy Configuration**
- `.env` file for all settings
- Headless/headful browser modes
- Configurable product limits
- Modular, maintainable codebase

---

## 🏗️ Architecture

### How It Works:

```
1. Selenium opens 1mg search page
        ↓
2. Scrolls to collect all product links
        ↓
3. For each product page:
   - Load page with Selenium
   - Extract visible text
   - Send to Gemini AI
        ↓
4. Gemini returns JSON:
   {name, company, price, composition, summary, description}
        ↓
5. Download images from HTML
        ↓
6. Save to formatted Excel
```

### Why LLM Extraction?

| Traditional CSS Selectors | LLM Extraction |
|---------------------------|----------------|
| ❌ Breaks when layout changes | ✅ Works on any layout |
| ❌ Different selectors per page type | ✅ One method for all pages |
| ❌ Constant maintenance needed | ✅ Zero maintenance |
| ❌ Fails on edge cases | ✅ Handles missing/varied data |
| ✅ Fast (~1s per product) | ⚠️ Slower (~2-3s per product) |
| ✅ Free | ⚠️ Small cost ($0.0002/product) |

**Verdict:** LLM is worth it for reliability and zero maintenance!

---

## 💰 Cost Analysis

### Gemini API Pricing:

| Scenario | Products | Time | Cost | Use Case |
|----------|----------|------|------|----------|
| **Free Tier** | 450/day | 1 day | $0 | Testing, small batches |
| **Paid - Small** | 100 | 10 min | $0.02 | Quick scrapes |
| **Paid - Medium** | 1,000 | 2 hours | $0.20 | Daily scraping |
| **Paid - Large** | 10,000 | 20 hours | $2.00 | Bulk extraction |

**Free tier limits:** 15 requests/minute, 1M tokens/day

Get your free API key: https://makersuite.google.com/app/apikey

---

## 🚀 Setup Instructions

### 1. Install Python Dependencies

```bash
# Optional but recommended: Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
. venv/Scripts/activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
BASE_URL="https://www.1mg.com/search/all?name=mankind"
MAX_PRODUCTS=5
OUTPUT_FOLDER="mankind"
HEADLESS=False
GEMINI_API_KEY="your-gemini-api-key-here"
USE_PROXY_BYPASS=False
```

**Configuration Options:**
- `BASE_URL`: 1mg search URL to scrape
- `MAX_PRODUCTS`: Limit number of products (useful for testing)
- `OUTPUT_FOLDER`: Where to save results
- `HEADLESS`: `True` = background mode, `False` = visible browser
- `GEMINI_API_KEY`: Get from https://makersuite.google.com/app/apikey
- `USE_PROXY_BYPASS`: `True` = bypass proxy for localhost (corporate networks), `False` = use default settings

⚠️ **Important:** 
- Without `GEMINI_API_KEY`, the scraper falls back to CSS selectors (less reliable)
- Set `USE_PROXY_BYPASS=True` if you're behind a corporate proxy and getting connection errors

### 3. Ensure Chrome Browser is Installed

Selenium 4+ auto-manages ChromeDriver, but Chrome must be installed on your system.

---

## ▶️ Run the Scraper

```bash
python scraper.py
```

**Recommended first run:**
- Set `MAX_PRODUCTS=5` in `.env` for testing
- Set `HEADLESS=False` to watch the browser
- Monitor console logs for any errors

---

## 📦 Output Structure

```
mankind/
├── data.xlsx                    # Main Excel file
└── images/
    ├── ProductName.png          # First image
    ├── ProductName1.png         # Second image
    ├── ProductName2.png         # Third image
    └── ...
```

### Excel Columns (`data.xlsx`):

| Column | Description | Example |
|--------|-------------|---------|
| `companyName` | Manufacturer/Brand | Mankind Pharma |
| `medicineName` | Product name | Glucon-D Instant Energy |
| `composition` | Active ingredients | Glucose + Vitamin D |
| `price` | MRP price | 99.0 |
| `description` | Summary + Full description | "Glucon-D...\n\nProvides instant energy...\n\nRead More...\n\nFull description..." |
| `imageLink` | Local image paths | "./images/ProductName.png,\n./images/ProductName1.png" |

**Note:** Images are NOT embedded in Excel - paths are stored as text. Navigate to the `images/` folder to view actual images.

---

## 🔧 Tech Stack

- **Python 3.8+**
- **Selenium 4+**: Browser automation
- **BeautifulSoup4**: HTML parsing (for images)
- **Google Generative AI**: LLM-based extraction
- **Pandas + Openpyxl**: Excel generation
- **Requests**: Image downloading
- **Python-dotenv**: Environment configuration

---

## 📂 Project Structure

```
1mg-scraper/
├── scraper.py              # Main orchestrator
├── parser.py               # LLM + CSS extraction logic
├── link_fetcher.py         # Search page link collection
├── downloader.py           # Image downloader
├── excel_manager.py        # Excel formatting & saving
├── driver_manager.py       # Selenium WebDriver setup
├── session_manager.py      # HTTP session for downloads
├── utils.py                # Logger configuration
├── summarizer.py           # [DEPRECATED - merged into parser]
├── .env                    # Configuration (not in git)
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── 1mg-scraper-plan.md    # Detailed implementation plan
```

---

## ⚙️ Advanced Usage

### Change Search Query

Edit `BASE_URL` in `.env`:
```env
BASE_URL="https://www.1mg.com/search/all?name=himalaya"
```

### Scrape More Products

```env
MAX_PRODUCTS=1000
```

### Run in Background (Headless)

```env
HEADLESS=True
```

### Disable LLM (Use CSS Fallback)

Remove or comment out `GEMINI_API_KEY` in `.env`:
```env
# GEMINI_API_KEY="your-key"
```

---

## 🛡️ Anti-Bot Protection

1mg uses Cloudflare and other bot detection measures. To minimize blocks:

✅ **What the scraper does:**
- Adds realistic delays (3s scroll, 1s page load)
- Uses actual Chrome browser (not headless by default)
- Checks for Cloudflare warnings

⚠️ **What you should do:**
- Don't scrape too aggressively (keep delays)
- Use non-headless mode if blocked
- Consider scraping during off-peak hours
- For large-scale scraping, consider proxies

---

## 🐛 Troubleshooting

### "Cloudflare detected"
**Solution:** Run with `HEADLESS=False`, add longer delays, or try different times

### "GEMINI_API_KEY not found"
**Solution:** Add your API key to `.env` file. Get one at https://makersuite.google.com/app/apikey

### "ChromeDriver not found"
**Solution:** Selenium 4+ auto-manages this. Ensure Chrome browser is installed.

### "Failed to parse JSON from Gemini"
**Solution:** Gemini occasionally returns malformed JSON. The scraper has retry logic, but may fall back to CSS selectors for that product.

### "Rate limit exceeded"
**Solution:** Free tier has limits. Wait a few minutes or upgrade to paid tier.

### "Connection broken: ConnectionResetError(10054)" or "Proxy error"
**Solution:** You're likely behind a corporate proxy. Set `USE_PROXY_BYPASS=True` in `.env` file.
- This bypasses proxy for localhost connections (Selenium ↔ ChromeDriver)
- Still allows Chrome to use proxy for external websites (1mg.com)
- Common in corporate/enterprise network environments

### No images downloaded
**Solution:** Check console logs - may be network issues or broken image URLs on 1mg

---

## 📝 Legal & Ethical Considerations

⚠️ **Important:**
- Check 1mg's `robots.txt` and Terms of Service
- This tool is for **educational/personal use only**
- Do not republish scraped data commercially
- Respect rate limits and server load
- Be a responsible web scraper

---

## 🔄 Recent Updates

**v2.0 (June 2026) - LLM Extraction**
- ✅ Replaced CSS selectors with Gemini AI extraction
- ✅ Single API call for extraction + summarization
- ✅ Automatic fallback to CSS if no API key
- ✅ Better handling of inconsistent layouts
- ✅ Updated documentation and plan

**v1.0 (May 2026) - Initial Release**
- CSS selector-based extraction
- Separate summarization step
- Basic Excel export

---

## 🤝 Contributing

This is a personal educational project. If you find issues or have suggestions:
1. Check existing issues
2. Test with small `MAX_PRODUCTS` first
3. Include error logs when reporting problems

---

## 📚 Additional Resources

- **Detailed Plan:** See `1mg-scraper-plan.md` for architecture decisions
- **Gemini API Docs:** https://ai.google.dev/docs
- **Selenium Docs:** https://selenium-python.readthedocs.io/

---

**Author:** Mahima Jeeban  
**License:** Educational Use  
**Last Updated:** June 6, 2026
