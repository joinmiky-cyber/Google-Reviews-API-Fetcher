# Google Maps Scraper for Addis Ababa

A Python-based scraper using Selenium to extract business information from Google Maps.

## Features
- Scrapes business name, address, phone number, website, rating, and "About" info.
- Extracts GPS coordinates (Latitude/Longitude) and Google Maps URL.
- Detailed review extraction (Author, Rating, Date, Text).
- Photo URL extraction.
- Deduplication of results in-memory and on-disk.
- CLI interface for easy usage.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure you have Firefox and Geckodriver installed.

## Usage

Run the scraper via the command line:

```bash
python3 main.py --category "Restaurants" --location "Bole, Addis Ababa" --max 20 --output bole_restaurants.csv
```

### Options
- `--category`: The type of business to search for (e.g., "Gyms", "Cafes").
- `--location`: The area to search in (e.g., "Piazza, Addis Ababa").
- `--max`: Maximum number of results to scrape.
- `--output`: Output CSV filename (defaults to `google_maps_data.csv`).
- `--gui`: Run with the browser visible (not headless).

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
