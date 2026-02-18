# Addis Ababa Business Data Scraper (Selenium)

This Python tool allows you to collect detailed information about business listings in Addis Ababa, Ethiopia, by scraping Google Maps using Selenium and Firefox.

## Features

- **Neighborhood Search**: Covers Addis Ababa by searching in multiple neighborhoods (Bole, Piazza, Kazanchis, etc.).
- **Detailed Information**: Collects names, phone numbers, addresses, GPS coordinates, ratings, and websites.
- **Photos & Reviews**: Retrieves URLs for up to 5 photos and up to 10 reviews for each business.
- **Export to CSV**: Saves all collected data into a CSV file.

---

## Prerequisites

1. **Python 3.8+**
2. **Firefox Browser**
3. **Geckodriver**: The driver for Firefox.

---

## Setup Instructions

1. **Clone or Download** this repository.
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Driver Paths**:
   Open `main.py` and ensure the following paths match your local system:
   - `self.profile_path`: Path to your Firefox profile.
   - `self.geckodriver_path`: Path to your `geckodriver` executable.

---

## How to Run

```bash
python main.py
```

### Options

- **Change Category**:
  ```bash
  python main.py --category gyms
  ```
- **Search Specific Neighborhoods**:
  ```bash
  python main.py --neighborhoods Bole Piazza
  ```

---

## Important Notes

- **Driver Compatibility**: Ensure your `geckodriver` version matches your Firefox version.
- **Scraping Fragility**: If Google updates their UI, selectors in `main.py` may need adjustment.
