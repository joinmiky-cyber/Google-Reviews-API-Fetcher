# Addis Ababa Business Data Scraper (Google Places API)

This Python tool allows you to collect detailed information about business listings in Addis Ababa, Ethiopia, using the official Google Places API. It implements a grid-search algorithm to maximize the number of results found within the city.

## Features

- **Grid Search**: Automatically covers Addis Ababa by searching multiple overlapping areas to overcome the 60-result limit of a single search.
- **Detailed Information**: Collects names, phone numbers, full addresses, GPS coordinates, ratings, and websites.
- **Photos & Reviews**: Retrieves photo references and the top 5 most helpful reviews for each business.
- **Deduplication**: Automatically removes duplicate results found during the grid search.
- **Export to CSV**: Saves all collected data into a clean CSV file.
- **Extensible**: Easy to add more categories like gyms, cafes, hotels, etc.

---

## Prerequisites

1. **Python 3.7+**
2. **Google Maps API Key**: You need an API key with the "Places API" enabled.

### How to get a Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "Addis Scraper").
3. Navigate to **APIs & Services > Library**.
4. Search for **"Places API"** and click **Enable**.
5. Navigate to **APIs & Services > Credentials**.
6. Click **Create Credentials > API key**.
7. (Optional but recommended) Restrict your API key to only the Places API to secure it.
8. **Note**: You must have a billing account linked to your Google Cloud project, although Google provides a free monthly credit ($200) which covers thousands of requests.

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
4. **Configure Environment Variables**:
   - Rename `.env.example` to `.env`.
   - Open `.env` and paste your Google Maps API key:
     ```
     GOOGLE_MAPS_API_KEY=your_actual_api_key_here
     ```

---

## How to Run

Simply run the `main.py` script:

```bash
python main.py
```

The script will:
1. Generate a grid of coordinates over Addis Ababa.
2. Search for restaurants near each point.
3. Fetch full details for every unique restaurant found.
4. Save the results to a file named `addis_ababa_restaurants_[TIMESTAMP].csv`.

---

## How to Extend

### Adding More Categories

To search for gyms, cafes, or other businesses, open `main.py` and modify the `CATEGORIES` list:

```python
# Example: Search for both restaurants and gyms
CATEGORIES = ['restaurant', 'gym']
```

For a full list of supported types, refer to the [Google Places Types documentation](https://developers.google.com/maps/documentation/places/web-service/supported_types).

### Adjusting Search Density

If you want to find even more businesses, you can make the grid more dense by decreasing the `STEP` value in `main.py`:

```python
STEP = 0.02  # Default is 0.04. Smaller value = more searches = more cost/time.
```

---

## Important Notes & Limitations

- **Photos**: For security reasons, the script saves **Photo References** instead of direct URLs. Direct URLs would require embedding your private API key in the CSV file, which is unsafe for sharing. To view a photo, you can use the following URL format, replacing `YOUR_API_KEY` and `PHOTO_REFERENCE`:
  `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=PHOTO_REFERENCE&key=YOUR_API_KEY`
- **Review Limit**: The official Google Places API only returns the **5 most helpful reviews** per business.
- **API Costs**: Each "Place Details" request and "Nearby Search" request incurs a small cost on your Google Cloud billing. The free $200 monthly credit is usually more than enough for a few full city scrapes.
- **Rate Limiting**: The script includes `time.sleep()` calls to respect Google's rate limits and ensure the `next_page_token` is valid.
