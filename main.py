import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

# Neighborhoods in Addis Ababa
ADDIS_NEIGHBORHOODS = [
    "Bole", "Kazanchis", "Piazza", "Old Airport", "Sarbet",
    "Haya Hulet", "22 Mazoria", "Merkato", "Kirkos", "Akaki Kality",
    "Nifas Silk Lafto", "Kolfe Keranio", "Gullele", "Lideta", "Yeka"
]

class GoogleMapsScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.results = []

    async def scrape_category(self, category, neighborhoods=None):
        if neighborhoods is None:
            neighborhoods = ADDIS_NEIGHBORHOODS

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()

            for neighborhood in neighborhoods:
                search_query = f"{category} in {neighborhood}, Addis Ababa"
                print(f"Searching for: {search_query}")

                await page.goto(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}")

                # Wait for results to load
                try:
                    await page.wait_for_selector('div[role="feed"]', timeout=10000)
                except:
                    print(f"No results feed found for {neighborhood}")
                    continue

                # Scroll the feed to load more results
                await self.scroll_feed(page)

                # Get all result links
                links = await page.query_selector_all('a.hfpxzc')
                print(f"Found {len(links)} potential listings in {neighborhood}")

                for link in links:
                    try:
                        # Click the listing
                        await link.click()
                        # Wait for the details pane to update
                        await page.wait_for_timeout(2000)

                        data = await self.extract_business_details(page)
                        if data:
                            self.results.append(data)
                    except Exception as e:
                        print(f"Error extracting listing: {e}")

            await browser.close()

        return self.results

    async def scroll_feed(self, page):
        # Find the scrollable feed element
        feed_selector = 'div[role="feed"]'
        last_height = await page.evaluate(f'document.querySelector("{feed_selector}").scrollHeight')

        while True:
            await page.evaluate(f'document.querySelector("{feed_selector}").scrollTo(0, document.querySelector("{feed_selector}").scrollHeight)')
            await page.wait_for_timeout(2000)
            new_height = await page.evaluate(f'document.querySelector("{feed_selector}").scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height
            # Limit scroll for now to avoid endless loops or too many results
            if last_height > 10000:
                break

    async def extract_business_details(self, page):
        try:
            name_el = await page.query_selector('h1.DUwDvf')
            name = await name_el.inner_text() if name_el else "N/A"

            # Check for duplicates by name (simple for now)
            if any(r['Name'] == name for r in self.results):
                return None

            phone_el = await page.query_selector('button[data-tooltip="Copy phone number"]')
            phone = await phone_el.inner_text() if phone_el else "N/A"

            address_el = await page.query_selector('button[data-tooltip="Copy address"]')
            address = await address_el.inner_text() if address_el else "N/A"

            website_el = await page.query_selector('a[data-tooltip="Open website"]')
            website = await website_el.get_attribute('href') if website_el else "N/A"

            rating_el = await page.query_selector('div.F7kYSe span.ce4YCe') # This selector might change
            # Alternative rating selector
            if not rating_el:
                rating_el = await page.query_selector('span.TTNQpf')

            rating = "N/A"
            if rating_el:
                rating_text = await rating_el.inner_text()
                rating = rating_text.split('\n')[0]

            # Photos
            photo_elements = await page.query_selector_all('button.g27YNc img')
            photo_urls = []
            for img in photo_elements[:5]:
                src = await img.get_attribute('src')
                if src:
                    photo_urls.append(src)

            # Reviews
            reviews = await self.extract_reviews(page)

            # Extract coordinates from URL
            url = page.url
            lat, lon = "N/A", "N/A"
            if "!3d" in url and "!4d" in url:
                try:
                    parts = url.split("!3d")[1].split("!4d")
                    lat = parts[0]
                    lon = parts[1].split("!")[0]
                except:
                    pass
            elif "@" in url:
                try:
                    coords = url.split("@")[1].split(",")[0:2]
                    lat, lon = coords[0], coords[1]
                except:
                    pass

            return {
                'Name': name,
                'Phone': phone,
                'Address': address,
                'Website': website,
                'Rating': rating,
                'Latitude': lat,
                'Longitude': lon,
                'Photo URLs': " | ".join(photo_urls),
                'Top Reviews': " || ".join(reviews),
            }
        except Exception as e:
            print(f"Failed to extract details: {e}")
            return None

    async def extract_reviews(self, page):
        reviews_list = []
        try:
            # Click the 'Reviews' tab if it exists
            reviews_tab = await page.query_selector('button[role="tab"]:has-text("Reviews")')
            if reviews_tab:
                await reviews_tab.click()
                await page.wait_for_timeout(2000)

                # Scroll in the reviews pane
                review_pane_selector = 'div.m6B62' # Common selector for reviews container
                # Wait for some reviews to appear
                await page.wait_for_selector('.wiI79', timeout=5000)

                # Simple scroll to get more
                for _ in range(2):
                    await page.mouse.wheel(0, 1000)
                    await page.wait_for_timeout(1000)

                # Try to click "More" for each review if it exists
                more_buttons = await page.query_selector_all('button:has-text("More")')
                for btn in more_buttons[:10]:
                    try:
                        await btn.click()
                        await page.wait_for_timeout(500)
                    except:
                        pass

                review_elements = await page.query_selector_all('.wiI79')
                for r in review_elements[:10]:
                    text = await r.inner_text()
                    if text:
                        reviews_list.append(text.replace('\n', ' ').strip())

            # Switch back to 'About' or 'Overview' tab?
            # Not strictly necessary if we click the next listing link from the feed.
        except Exception as e:
            print(f"Error getting reviews: {e}")

        return reviews_list

def save_to_csv(data, category):
    if not data:
        print("No data to save.")
        return
    df = pd.DataFrame(data)
    # Deduplicate just in case
    df = df.drop_duplicates(subset=['Name', 'Address'])
    filename = f"addis_ababa_{category.replace(' ', '_')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} results to {filename}")

async def main():
    import argparse
    import sys

    # Check for DISPLAY on Linux
    has_display = True
    if sys.platform.startswith('linux'):
        if not os.environ.get('DISPLAY'):
            has_display = False

    parser = argparse.ArgumentParser(description="Google Maps Scraper for Addis Ababa")
    parser.add_argument("--category", type=str, default="restaurants", help="Category to search for (e.g., restaurants, gyms)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--neighborhoods", nargs="+", help="Specific neighborhoods to search in")

    args = parser.parse_args()

    headless_mode = args.headless
    if not has_display and not args.headless:
        print("Warning: No display detected. Switching to headless mode automatically.")
        headless_mode = True

    scraper = GoogleMapsScraper(headless=headless_mode)
    print(f"Starting scrape for {args.category}...")
    results = await scraper.scrape_category(args.category, neighborhoods=args.neighborhoods)
    save_to_csv(results, args.category)

if __name__ == "__main__":
    asyncio.run(main())
