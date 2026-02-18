# Addis Ababa Business Data Scraper (Web Scraper)

This Python tool allows you to collect detailed information about business listings in Addis Ababa, Ethiopia, by scraping Google Maps using Playwright. It searches by neighborhood to ensure high coverage of the city.

## Features

- **Neighborhood Search**: Automatically covers Addis Ababa by searching in multiple neighborhoods (Bole, Piazza, Kazanchis, etc.).
- **Detailed Information**: Collects names, phone numbers, full addresses, GPS coordinates, ratings, and websites.
- **Photos & Reviews**: Retrieves URLs for up to 5 photos and up to 10 reviews for each business.
- **Deduplication**: Automatically removes duplicate results found across different searches.
- **Export to CSV**: Saves all collected data into a clean CSV file.
- **Extensible**: Easy to add more categories like gyms, cafes, hotels, etc.

---

## Prerequisites

1. **Python 3.8+**
2. **Playwright Browsers**: You need to install the Chromium browser used by Playwright.

---

## Setup Instructions

1. **Clone or Download** this repository to your local machine.
2. **Create a Virtual Environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

---

## How to Run

By default, the script runs in **headed mode** (browser window visible) so you can see the progress.

```bash
python main.py
```

### Options

You can customize the search using command-line arguments:

- **Change Category**:
  ```bash
  python main.py --category gyms
  ```
- **Run in Headless Mode** (background):
  ```bash
  python main.py --headless
  ```
- **Search Specific Neighborhoods**:
  ```bash
  python main.py --neighborhoods Bole Piazza "Old Airport"
  ```

The results will be saved to a file named `addis_ababa_[CATEGORY].csv`.

---

## How it Works

1. **Search**: The script iterates through a list of major Addis Ababa neighborhoods and searches for your chosen category.
2. **Scrolling**: It scrolls through the results feed to load as many listings as possible.
3. **Extraction**: It clicks on each listing, waits for the details to load, and extracts the business information.
4. **Reviews**: It switches to the "Reviews" tab, scrolls slightly, and grabs up to 10 reviews.
5. **Deduplication**: It keeps track of `Name` and `Address` to ensure the same business isn't saved twice if it appears in multiple searches.

---

## Important Notes & Limitations

- **Scraping Fragility**: Web scraping depends on the visual structure of Google Maps. If Google updates their UI, selectors in `main.py` might need to be updated.
- **Speed**: Scraping is slower than using an API because it mimics human interaction (clicking, waiting for loads).
- **Ethical Note**: Please use this tool responsibly and respect Google's Terms of Service. This script is intended for educational purposes and data analysis.
