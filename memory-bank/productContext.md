# Product Context: Why This Scraper Exists

## Problem Being Solved

### Business Need
Pharmaceutical companies and distributors need to:
1. **Monitor competitor pricing** on 1mg.com
2. **Analyze product portfolios** by brand/manufacturer
3. **Track product descriptions** and marketing content
4. **Collect product images** for catalogs or competitive analysis
5. **Build datasets** for business intelligence

### Technical Challenges
1. **Dynamic content loading**: 1mg.com uses infinite scroll - products load as user scrolls
2. **Anti-bot protection**: Cloudflare and rate limiting require human-like behavior
3. **Inconsistent HTML structure**: Different product pages may have varying layouts
4. **Corporate network restrictions**: Proxy issues prevent Selenium from connecting to ChromeDriver
5. **API quotas**: Free Gemini API has rate limits requiring fallback mechanisms

## How It Should Work

### User Experience Flow
1. User configures `.env` file with:
   - Brand to search (via `BASE_URL`)
   - Number of products to scrape (via `MAX_PRODUCTS`)
   - Output folder name (via `OUTPUT_FOLDER`)
   - Gemini API key (optional)
   - Headless mode preference
   - Proxy bypass if needed

2. User runs `python scraper.py`

3. System automatically:
   - Opens Chrome browser (or headless)
   - Scrolls through search results collecting product links
   - Visits each product page
   - Extracts data using LLM (or CSS fallback)
   - Downloads images with deduplication
   - Saves to formatted Excel file

4. User receives:
   - Console progress updates
   - Final success/failure summary
   - Excel file with all data
   - Images folder with downloaded photos

### Expected Behavior

#### Success Path
- Browser opens and loads search page
- Console shows: "Collected X links so far..."
- For each product: "[N/M] Scraping: {URL}"
- Images download with retry logic
- Excel file generated with professional formatting
- Summary printed with success/failure counts

#### Failure Handling
- If Cloudflare detected → error logged, graceful exit
- If individual product fails → logged, continue with next
- If LLM quota exceeded → automatic fallback to CSS
- If network timeout → retry with exponential backoff
- If ChromeDriver fails → 3 retry attempts with helpful error messages

## User Experience Goals

### Must Have
1. **Reliability**: Don't crash on single product failures
2. **Transparency**: Clear console logging of progress
3. **Speed**: Reasonable performance (3-5 seconds per product)
4. **Accuracy**: Correct data extraction with formatting
5. **Graceful degradation**: Work without LLM if needed

### Should Have
1. **Resume capability**: Skip already downloaded images
2. **Corporate network support**: Proxy bypass option
3. **Headless mode**: Run without visible browser
4. **Professional output**: Well-formatted Excel with borders, wrapping, column widths

### Nice to Have
1. **Customizable delays**: Configure scroll timing for different network speeds
2. **Multiple output formats**: CSV fallback if openpyxl not installed
3. **Detailed logs**: File-based logging for debugging

## Key Product Decisions

### Why Gemini 1.5 Flash (not GPT or Claude)?
- **Cost-effective**: Free tier available, cheap at scale
- **Fast**: 1-2 second response times
- **Good enough**: Adequate accuracy for structured extraction
- **Fallback ready**: Can work without it

### Why Excel (not JSON/CSV)?
- **Business users**: Non-technical stakeholders prefer Excel
- **Professional appearance**: Formatting matters for reports
- **Built-in features**: Wrap text, auto-width, borders enhance readability

### Why Selenium (not Requests/Scrapy)?
- **Dynamic content**: Infinite scroll requires JavaScript execution
- **Anti-bot bypass**: Full browser mimics human behavior
- **Cloudflare handling**: More likely to pass bot detection

### Why Local Images (not URLs only)?
- **Persistence**: URLs may break or change
- **Offline access**: Users can view data without internet
- **Control**: Local copies prevent future loss

## Target Users
- Pharmaceutical business analysts
- Competitive intelligence teams
- Data scientists building ML datasets
- E-commerce price monitoring services
- Market research firms
