# 1mg Web Scraper

## Project Overview
This project is an automated web scraping solution that extracts product data and images from the 1mg e-commerce search page. It handles dynamic loading (infinite scrolling) using Selenium, visits each individual product page to extract deep information, downloads associated product images, and compiles the result into a clean Excel file.

## Features
- **Dynamic Scrolling Handling**: Uses Selenium to simulate infinite scrolling, fetching products beyond the initially visible ones.
- **Deep Data Extraction**: Visits each product page individually to collect comprehensive details (company name, product name, composition, price, and detailed description).
- **Image Downloading**: Automatically downloads and names all available product images.
- **Data Export**: Generates a formatted Excel file (`data.xlsx`) containing all collected data.
- **Configuration via `.env`**: Easily configure the base URL, target number of products, output folder, and browser headless mode.
- **Robust Execution**: Includes retries for network failures and explicit waits for element loading to minimize breakages.

## Tech Stack
- **Python 3**
- **Selenium**: Used for browser automation and dynamic scrolling.
- **BeautifulSoup**: Used for parsing and extracting data from HTML.
- **Requests**: Used for robust network calls and fast image downloading.
- **Pandas & Openpyxl**: Used for exporting data to structured Excel sheets.
- **Python-dotenv**: Used for managing environment variables.

## Setup Instructions

### 1. Clone Repo
Clone this repository to your local machine:
```bash
git clone <repository_url>
cd 1mg-scraper
```

### 2. Install Dependencies
Install the required Python packages using pip:
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
A `.env` file must be created in the root directory to store configurable values. You can use the provided `.env` format:
```env
BASE_URL="https://www.1mg.com/search/all?name=mankind"
MAX_PRODUCTS=100
OUTPUT_FOLDER="mankind"
HEADLESS=False
```
*(Set `HEADLESS=True` if you do not want the browser window to open during scraping).*

## Run Instructions
Run the main script using python:
```bash
python scraper.py
```

## Output Description
### Folder Structure
Upon successful execution, the script will create the following output structure:
```text
mankind/
│
├── data.xlsx
└── images/
    ├── productname.png
    ├── productname1.png
    ├── productname2.png
    └── ...
```

### Excel Format (`mankind/data.xlsx`)
The generated Excel file contains the following columns for each extracted product:
- `companyName` (Brand Name)
- `medicineName` (Product Name)
- `composition` (Salt / Composition)
- `price` (MRP)
- `description` (Detailed description from the product page)
- `imageName` (Comma-separated filenames of the downloaded images)

## Notes
- **Dynamic Scrolling Handling**: The script uses a JavaScript execution strategy to scroll down the page. It waits for new product cards to load in the DOM, keeping track of unique product links until the `MAX_PRODUCTS` threshold is reached.
- **Anti-Bot Protections**: 1mg occasionally employs Cloudflare or similar bot-protection systems. The script utilizes custom headers and realistic User-Agents, but prolonged or excessively rapid scraping may still be restricted.
