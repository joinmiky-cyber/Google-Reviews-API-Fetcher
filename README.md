# Google Maps Scraper for Addis Ababa

A Python-based scraper using Selenium to extract business information from Google Maps.

## Features
- Scrapes business name, address, phone number, website, rating, and "About" info.
- Extracts GPS coordinates (Latitude/Longitude) and Google Maps URL.
- Detailed review extraction (Author, Rating, Date, Text).
- Photo URL extraction.
- **Neighborhood-based coverage**: Automatically iterates through 10 major neighborhoods in Addis Ababa (Bole, Piazza, Kazanchis, etc.) to ensure comprehensive data collection.
- Deduplication of results in-memory and on-disk.
- CLI interface for easy usage.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure you have Firefox and Geckodriver installed.

## Usage

Run the scraper via the command line. **By default, the browser will open so you can see the progress.**

```bash
python3 main.py --category "Restaurants" --max 10 --output addis_restaurants.csv
```

### Options
- `--category`: The type of business to search for (e.g., "Gyms", "Cafes"). Default is "Restaurants".
- `--location`: Specify a single location (e.g., "Bole, Addis Ababa"). If omitted, the scraper will loop through a predefined list of Addis Ababa neighborhoods.
- `--max`: Maximum number of results to scrape **per neighborhood**.
- `--output`: Output CSV filename (defaults to `google_maps_data.csv`).
- `--headless`: Run the scraper in the background (no browser window).

## Output
The data is saved to a CSV file with the following columns:
- `name`
- `google_maps_url`
- `latitude`
- `longitude`
- `address`
- `phone`
- `website`
- `rating`
- `about`
- `reviews`
- `photo_urls`
