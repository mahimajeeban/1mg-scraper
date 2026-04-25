# 1mg Web Scraper

This project contains a web scraping script (`scraper.py`) inside the `1mg-scraper` directory. It uses `Selenium` and `BeautifulSoup` to navigate 1mg.com and extract information and images for various products. 

## Prerequisites
- Python 3 installed on your system.
- Google Chrome browser (required for Selenium to navigate the site).

## Installation Steps

Follow these steps to set up the project on your local machine. This ensures that everyone checking out the code gets the exact versions of the libraries required.

**1. Open your terminal and navigate to the project directory:**
```bash
cd 1mg-scraper
```

**2. Create a Python Virtual Environment:**
A virtual environment keeps the dependencies isolated specifically for this project.
```bash
python3 -m venv venv
```

**3. Activate the Virtual Environment:**
- **On Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```
- **On Windows:**
  ```bash
  .\venv\Scripts\activate
  ```

**4. Install Project Dependencies:**
Make sure your virtual environment is active (your terminal prompt will usually show `(venv)` on the left side). Then, install all required packages:
```bash
pip install -r requirements.txt
```

## Running the Scraper

Once your dependencies are installed and the virtual environment is activated, you can execute the script:

```bash
python scraper.py
```

### Expected Output
- A Google Chrome browser window will automatically launch to navigate the pages. Let it run so it can process the pages and avoid bot protections.
- The terminal will display live progress logs.
- The script will create a new folder containing all downloaded item images.
- A final `data.xlsx` spreadsheet will be generated capturing all product details (Name, MRP, Price, Description).
