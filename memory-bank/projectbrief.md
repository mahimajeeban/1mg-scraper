# Project Brief: 1mg Product Scraper

## Project Goal
Scrape pharmaceutical product data from 1mg.com (search results page) and save structured data to Excel with downloaded product images.

## Core Objective
Extract product information for a specified brand (e.g., "Mankind") including:
- Product name
- Company/manufacturer
- Composition (active ingredients)
- Price
- Description with AI-generated summary
- Product images

## Key Requirements

### Input
- Search URL (e.g., `https://www.1mg.com/search/all?name=mankind`)
- Maximum number of products to scrape (configurable via `.env`)

### Output
1. **Excel file** (`data.xlsx`) with structured product data in specific column order
2. **Images folder** containing all downloaded product images
3. Output organized in brand-specific folder (e.g., `mankind/` or `shipla/`)

### Critical Constraints

#### 1. LLM is Optional (NOT Required)
- Gemini 1.5 Flash API used for intelligent extraction
- If API key missing or quota exceeded → **automatic fallback to CSS selectors**
- System must work without LLM (degraded but functional)

#### 2. Fixed Output Format
- Excel columns MUST be: `["companyName", "medicineName", "composition", "price", "description", "imageLink"]`
- No additional columns, no column reordering
- Description format: `"{medicineName}\n\n{summary}\n\nRead More...\n\n{description}"`

#### 3. Anti-Bot Protection
- Cloudflare detection must be preserved
- Human-like scrolling delays (3 seconds between actions)
- Retry logic for network failures
- Corporate proxy bypass support via `USE_PROXY_BYPASS`

#### 4. Error Handling
- Individual product failures don't stop the entire scrape
- Failed products are logged and counted
- Final summary shows success/failure ratio

## Success Criteria
- Successfully scrapes product data from paginated search results
- Handles dynamic loading (infinite scroll)
- Downloads all product images with deduplication
- Generates properly formatted Excel file
- Gracefully handles API rate limits and network errors
- Works in both headless and headed browser modes

## Non-Goals
- Not a real-time monitoring tool
- Not designed for scraping entire catalog (focuses on specific brands)
- Not responsible for legal compliance (user's responsibility)

## Current Status
✅ Fully functional production scraper
✅ LLM integration with automatic fallback
✅ Robust error handling and retry logic
✅ Professional Excel formatting with openpyxl
✅ Image deduplication
✅ Corporate proxy support
