# 1mg Web Scraper

## Project Overview
This project is an automated, modular web scraping application that extracts product data and images from 1mg.com search pages. 

It handles dynamic loading (infinite scrolling) using Selenium, visits each individual product page to extract deep information, downloads associated product images, and compiles the result into a beautifully formatted Excel file. It also features **AI-powered summarization** using the Google Gemini API to generate concise summaries of long product descriptions.

## Features
- **Dynamic Scrolling Handling**: Uses Selenium to simulate infinite scrolling, fetching products beyond the initially visible ones.
- **Deep Data Extraction**: Visits each product page individually to collect comprehensive details (company name, product name, composition, price, and detailed description).
- **AI Description Summarization**: Optionally uses the Gemini API (`gemini-1.5-flash`) to generate a clean, 1-3 sentence summary of the product description, appending it to the original text.
- **Image Downloading**: Automatically downloads and names all available product images locally.
- **Clean Data Export**: Generates a formatted Excel file (`data.xlsx`) containing all collected data with properly adjusted column widths and text wrapping.
- **Modular OOP Design**: The codebase is neatly separated into managers and controllers (`driver_manager.py`, `excel_manager.py`, `summarizer.py`, etc.) for easy maintenance.
- **Configuration via `.env`**: Easily configure the base URL, target number of products, output folder, headless mode, and your API keys.

## Tech Stack
- **Python 3**
- **Selenium**: Used for browser automation and dynamic scrolling.
- **BeautifulSoup4**: Used for parsing and extracting data from HTML.
- **Requests**: Used for robust network calls and fast image downloading.
- **Pandas & Openpyxl**: Used for exporting data to structured Excel sheets.
- **Google Generative AI**: Used for LLM-based text summarization.
- **Python-dotenv**: Used for managing environment variables.

## Setup Instructions

### 1. Create Virtual Environment & Install Dependencies
It is highly recommended to use a virtual environment to prevent package conflicts with your system. Create and activate it using:

```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

Then install the required Python packages:
```bash
pip3 install -r requirements.txt
```
*(Make sure `google-generativeai` is in your `requirements.txt` if you plan to use the AI summarizer).*

### 2. Create `.env` file
A `.env` file must be created in the root directory to store configurable values. You can use the following format:

```env
BASE_URL="https://www.1mg.com/search/all?name=mankind"
MAX_PRODUCTS=100
OUTPUT_FOLDER="mankind"
HEADLESS=False
GEMINI_API_KEY="your_google_gemini_api_key_here"
```
- Set `HEADLESS=True` if you do not want the browser window to open during scraping.
- `GEMINI_API_KEY` is optional. If not provided, the script will skip the summarization step and just save the raw description.

## Run Instructions

Ensure your virtual environment is activated, then run the main scraper script:

```bash
python3 scraper.py
```

## Output Description

### Folder Structure
Upon successful execution, the script will create the following output structure based on your `OUTPUT_FOLDER` setting:

```text
mankind/
│
├── data.xlsx
└── images/
    ├── productname.png
    ├── productname1.png
    └── ...
```

### Excel Format (`mankind/data.xlsx`)
The generated Excel file contains the following columns for each extracted product:
- `companyName` (Brand Name)
- `medicineName` (Product Name)
- `composition` (Salt / Composition)
- `price` (MRP)
- `description` (Contains AI Summary + Full Detailed description)
- `imageLink` (Local file paths to the downloaded images, e.g., `./images/productname.png`)

## Notes on Anti-Bot Protections
1mg occasionally employs Cloudflare or similar bot-protection systems. The script utilizes custom headers and realistic User-Agents to mimic a real browser. However, prolonged or excessively rapid scraping may still be temporarily restricted. If you encounter blocks, consider increasing sleep intervals in the scraper logic.
