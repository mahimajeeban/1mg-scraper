# Active Context: Current State & Recent Work

## Current Project Status

### ✅ What's Working
1. **Core Scraping Pipeline**: Fully functional end-to-end
   - Link collection from infinite scroll search pages
   - Individual product page extraction
   - Image downloading with deduplication
   - Excel file generation with professional formatting

2. **LLM Integration**: Gemini 1.5 Flash successfully extracting structured data
   - JSON parsing with markdown cleanup
   - Automatic fallback to CSS selectors
   - Retry logic handling rate limits
   - Description formatting with inline summaries

3. **Robustness Features**:
   - Exponential backoff retry logic across all network operations
   - Cloudflare detection at multiple checkpoints
   - Graceful handling of individual product failures
   - Corporate proxy bypass support
   - WebDriver auto-recovery and health checks

4. **Output Quality**:
   - Fixed column order Excel schema
   - Professional cell formatting (borders, wrapping, alignment)
   - Proper image path references (relative `./images/` format)
   - Success/failure summary reporting

### 🎯 Current Focus
- **Maintaining stability**: No active development, system is production-ready
- **Documentation**: Creating Memory Bank for multi-model AI handoff
- **Known Good State**: Latest codebase scrapes successfully with both LLM and CSS fallback

### 🔄 Recent Changes

#### Latest Updates (Current Session - June 6, 2026)
**Memory Bank Creation**
- Created comprehensive Memory Bank documentation structure
- Documented all critical constraints and design decisions
- Captured architectural patterns and data flow
- Prepared system for handoff to other AI models

**Parser Enhancements (Latest Commit: 25a15ea)**
- Added automatic "Read More" button clicking via JavaScript injection
- Enhanced CSS price extraction with 3-tiered approach (slashed-price → best-price → fallback)
- Added filtering to exclude "substitute" item prices from extraction
- Enhanced description extraction to find "Product Introduction" sections
- Added cleanup to remove leftover button texts ("read more", "show more", etc.)
- Increased LLM page text limit from 6000 to 12000 chars for better composition detection

**New Documentation File**
- Created `llm_rules.md` - Comprehensive LLM extraction guidelines
- Documents composition detection patterns (SALT COMPOSITION vs Key Ingredients)
- Enforces strict description length limits (3-4 sentences, max 60 words)
- Defines field extraction rules for Gemini model
- Version 1.1 with strengthened composition extraction

**README Updates**
- Enhanced documentation reflecting LLM-first approach
- Added cost analysis and API pricing details
- Improved troubleshooting section

#### Previous Updates (Before Latest Commit)
- Migrated from separate `summarizer.py` to inline summary in `parser.py`
- LLM now generates both summary and full description in single API call
- Description format: `"{medicineName}\n\n{summary}\n\nRead More...\n\n{description}"`
- `summarizer.py` kept as legacy but not imported/used

#### Historical Updates (From Git History)
- Added proxy bypass support for corporate networks
- Implemented image deduplication (skip existing files)
- Enhanced Excel formatting (column widths, borders, wrapping)
- Added Cloudflare detection
- Implemented exponential backoff for all retry logic

## Important Patterns & Preferences

### Code Style
- **Error Handling**: Try-except with specific exception types, always log errors
- **Logging**: Use `setup_logger(__name__)` pattern consistently
- **Retries**: Always implement exponential backoff (not linear)
- **Constants**: Read from `.env`, provide sensible defaults

### Module Organization
- **Single Responsibility**: Each class does one thing well
- **Dependency Injection**: Pass dependencies via constructor
- **Orchestration**: `scraper.py` coordinates, doesn't implement details
- **Stateless Operations**: Most methods are stateless (except DriverManager)

### Data Flow Conventions
```python
# Product data structure (internal format)
{
    "companyName": str,
    "medicineName": str,
    "composition": str,
    "price": float | str,  # float or "N/A"
    "description": str,     # Formatted with summary
    "image_urls": list      # Temporary, converted to imageLink
}

# Excel output format (final format)
{
    "companyName": str,
    "medicineName": str,
    "composition": str,
    "price": float | str,
    "description": str,
    "imageLink": str        # Comma-newline separated paths
}
```

### Naming Conventions
- Classes: PascalCase (e.g., `ProductParser`)
- Methods: snake_case (e.g., `_extract_with_llm`)
- Private methods: Leading underscore (e.g., `_is_driver_alive`)
- Constants: UPPER_SNAKE_CASE from `.env` (e.g., `MAX_PRODUCTS`)

## Next Steps (If Development Resumes)

### Potential Enhancements
1. **Async Image Downloads**: Use `asyncio` to parallelize image downloads
2. **Database Support**: Optional SQLite/PostgreSQL output in addition to Excel
3. **Resume Capability**: Save progress, resume from last successful product
4. **Multiple Brands**: Scrape multiple brands in single run
5. **Scheduled Runs**: Cron/Task Scheduler integration
6. **Webhook Notifications**: Notify on completion/failure

### Known Improvement Areas
1. **Cloudflare Handling**: Could implement CAPTCHA solving (e.g., 2captcha API)
2. **CSS Fallback**: Could be more robust with better selectors
3. **Error Reporting**: Could save failed URLs to separate file for retry
4. **Logging**: Could add file-based logging in addition to console
5. **Configuration**: Could use YAML/JSON config instead of `.env` for complex scenarios

### Breaking Changes to Avoid
- **Do NOT change Excel column order** without coordinating with downstream consumers
- **Do NOT make LLM mandatory** - fallback must always work
- **Do NOT remove proxy bypass** - breaks enterprise users
- **Do NOT change description format** - business logic may parse this
- **Do NOT alter image path format** - Excel formulas may reference these

## Active Decisions & Considerations

### Design Trade-offs Made

#### 1. Single WebDriver Instance
**Trade-off**: Speed vs. fault isolation
**Decision**: Reuse driver for performance
**Reasoning**: Scraping is batch job, acceptable to fail fast if driver crashes
**Future**: Could implement driver pool for parallel scraping

#### 2. Synchronous Image Downloads
**Trade-off**: Simplicity vs. speed
**Decision**: Sequential downloads
**Reasoning**: Easier to reason about, rate limiting concerns
**Future**: Async downloads could 5-10x speed

#### 3. 3-Second Scroll Delays
**Trade-off**: Speed vs. reliability
**Decision**: Conservative timing
**Reasoning**: Reduce Cloudflare risk, allow content to load
**Future**: Could make configurable via `.env`

#### 4. First 12000 Chars for LLM
**Trade-off**: Completeness vs. cost/speed
**Decision**: Truncate page text to 12000 chars (~3000 tokens)
**Reasoning**: Product info is typically at top, but increased from 6000 to ensure composition sections aren't cut off
**Evolution**: Originally 6000 chars, increased after discovering composition data was sometimes missed
**Future**: Could use smart truncation (keep specific sections)

#### 5. Gemini (not GPT/Claude)
**Trade-off**: Accuracy vs. cost
**Decision**: Gemini 1.5 Flash
**Reasoning**: Free tier, good enough accuracy, fast
**Future**: Could make model configurable

### Current Assumptions
1. **1mg.com HTML structure** is relatively stable
2. **Cloudflare** doesn't update detection algorithms frequently
3. **Product pages** load within 15-second timeout
4. **Images** are publicly accessible (no auth required)
5. **Excel output** opened by Microsoft Excel or compatible software
6. **Users** run on machines with Chrome installed

### Environment Assumptions
- Python 3.8+ available
- Chrome browser installed
- Internet connection stable
- Write permissions in project directory
- `.env` file properly configured

## Project Insights & Learnings

### What Works Well
1. **Two-strategy extraction**: LLM + CSS fallback is robust
2. **Exponential backoff**: Handles rate limits gracefully
3. **Cloudflare early detection**: Saves time vs. failing per product
4. **Image deduplication**: Allows reruns without re-downloading
5. **Professional Excel formatting**: Users appreciate visual quality

### What's Tricky
1. **Infinite scroll**: Detecting "end of page" is imperfect
2. **Dynamic HTML classes**: 1mg.com may use generated class names
3. **Cloudflare**: Unpredictable, sometimes triggered randomly
4. **Corporate proxies**: Many edge cases, hard to debug remotely
5. **LLM JSON parsing**: Models sometimes add markdown formatting

### Lessons Learned
1. **Always provide fallback**: LLM optional was critical decision
2. **Log everything**: Debugging scraper issues requires detailed logs
3. **Retry with backoff**: Linear retries waste time
4. **Human-like timing**: Too fast triggers bot detection
5. **Test in corporate environment**: Proxy issues are common

## Model Handoff Notes

### For Future AI Assistants (Claude, GPT, Gemini, etc.)

When you start working on this project:

1. **READ ALL MEMORY BANK FILES FIRST**
   - Start with `projectbrief.md` for high-level understanding
   - Review `systemPatterns.md` for architecture and constraints
   - Check `techContext.md` for setup and dependencies

2. **CRITICAL CONSTRAINTS TO RESPECT**
   - Excel column order is fixed (don't change)
   - LLM must be optional (fallback always works)
   - Description format has specific structure (don't alter)
   - 3-second delays are non-negotiable (anti-bot)
   - Proxy bypass is essential for some users (don't remove)

3. **BEFORE MAKING CHANGES**
   - Understand the full data flow (see `systemPatterns.md`)
   - Check if change affects Excel output schema
   - Verify LLM fallback still works
   - Test with `MAX_PRODUCTS=5` first
   - Consider corporate environment impact

4. **WHEN DEBUGGING**
   - Check console logs first
   - Run with `HEADLESS=False` to watch execution
   - Test `python test_driver.py` for setup issues
   - Review `techContext.md` for common issues

5. **IF EXTENDING FUNCTIONALITY**
   - Keep two-strategy pattern (primary + fallback)
   - Add new env vars to `techContext.md`
   - Update Memory Bank files to document changes
   - Maintain backward compatibility

### Current Working State Snapshot
- **Last Known Good Run**: June 6, 2026 (post-parser enhancements)
- **Latest Commit**: 25a15ea "update code"
- **Test Configuration**: `BASE_URL=1mg.com/search/all?name=mankind`, `MAX_PRODUCTS=100`
- **Environment**: Windows 11, Python 3.x, Chrome browser, Gemini API active
- **Output**: `shipla/data.xlsx` with 100 products successfully scraped
- **Status**: Production-ready with enhanced CSS fallback and composition extraction
- **Recent Improvements**: Better price detection, automatic content expansion, cleaner descriptions
