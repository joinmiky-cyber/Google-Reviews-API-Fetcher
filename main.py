import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Neighborhoods in Addis Ababa
ADDIS_NEIGHBORHOODS = [
    "Bole", "Kazanchis", "Piazza", "Old Airport", "Sarbet",
    "Haya Hulet", "22 Mazoria", "Merkato", "Kirkos", "Akaki Kality",
    "Nifas Silk Lafto", "Kolfe Keranio", "Gullele", "Lideta", "Yeka"
]

class GoogleMapsSeleniumScraper:
    def __init__(self, category, neighborhoods=None):
        self.category = category
        self.neighborhoods = neighborhoods or ADDIS_NEIGHBORHOODS
        self.results = []

        # User-provided paths
        self.profile_path = "/Users/michaeldinku/Library/Application Support/Firefox/Profiles/bvnl8r56.default-release"
        self.geckodriver_path = "/Users/michaeldinku/Downloads/geckodriver 2"

        self.setup_driver()

    def setup_driver(self):
        options = Options()
        # Correct way to load an existing Firefox profile directory
        options.add_argument("-profile")
        options.add_argument(self.profile_path)

        service = Service(executable_path=self.geckodriver_path)
        self.driver = webdriver.Firefox(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def scrape(self):
        try:
            for neighborhood in self.neighborhoods:
                search_query = f"{self.category} in {neighborhood}, Addis Ababa"
                print(f"Searching for: {search_query}")

                url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
                self.driver.get(url)

                # Wait for results
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
                except:
                    print(f"No results feed found for {neighborhood}")
                    continue

                self.scroll_feed()

                # Get all result links
                links = self.driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
                print(f"Found {len(links)} potential listings in {neighborhood}")

                for i in range(len(links)):
                    try:
                        # Re-find links to avoid stale element reference
                        links = self.driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
                        if i >= len(links): break

                        link = links[i]
                        self.driver.execute_script("arguments[0].click();", link)
                        time.sleep(3) # Wait for details to load

                        data = self.extract_business_details()
                        if data:
                            self.results.append(data)
                    except Exception as e:
                        print(f"Error extracting listing: {e}")
        finally:
            self.driver.quit()

        return self.results

    def scroll_feed(self):
        feed_selector = 'div[role="feed"]'
        try:
            feed = self.driver.find_element(By.CSS_SELECTOR, feed_selector)
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", feed)

            while True:
                self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", feed)
                time.sleep(2)
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", feed)
                if new_height == last_height:
                    break
                last_height = new_height
                if last_height > 10000: break
        except Exception as e:
            print(f"Error scrolling: {e}")

    def extract_business_details(self):
        try:
            name = "N/A"
            try:
                name_el = self.driver.find_element(By.CSS_SELECTOR, 'h1.DUwDvf')
                name = name_el.text
            except: pass

            # Check for duplicates
            if any(r['Name'] == name for r in self.results):
                return None

            phone = "N/A"
            try:
                phone_el = self.driver.find_element(By.CSS_SELECTOR, 'button[data-tooltip="Copy phone number"]')
                phone = phone_el.text
            except: pass

            address = "N/A"
            try:
                address_el = self.driver.find_element(By.CSS_SELECTOR, 'button[data-tooltip="Copy address"]')
                address = address_el.text
            except: pass

            website = "N/A"
            try:
                website_el = self.driver.find_element(By.CSS_SELECTOR, 'a[data-tooltip="Open website"]')
                website = website_el.get_attribute('href')
            except: pass

            rating = "N/A"
            try:
                rating_el = self.driver.find_element(By.CSS_SELECTOR, 'div.F7kYSe span.ce4YCe')
                rating = rating_el.text.split('\n')[0]
            except:
                try:
                    rating_el = self.driver.find_element(By.CSS_SELECTOR, 'span.TTNQpf')
                    rating = rating_el.text
                except: pass

            # Photos
            photo_urls = []
            try:
                photo_elements = self.driver.find_elements(By.CSS_SELECTOR, 'button.g27YNc img')
                for img in photo_elements[:5]:
                    src = img.get_attribute('src')
                    if src: photo_urls.append(src)
            except: pass

            # Coordinates from URL
            url = self.driver.current_url
            lat, lon = "N/A", "N/A"
            if "!3d" in url and "!4d" in url:
                try:
                    parts = url.split("!3d")[1].split("!4d")
                    lat = parts[0]
                    lon = parts[1].split("!")[0]
                except: pass
            elif "@" in url:
                try:
                    coords = url.split("@")[1].split(",")[0:2]
                    lat, lon = coords[0], coords[1]
                except: pass

            # Reviews
            reviews = self.extract_reviews()

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

    def extract_reviews(self):
        reviews_list = []
        try:
            # Click Reviews tab
            tabs = self.driver.find_elements(By.CSS_SELECTOR, 'button[role="tab"]')
            for tab in tabs:
                if "Reviews" in tab.text:
                    tab.click()
                    time.sleep(2)
                    break

            # Scroll in reviews
            for _ in range(2):
                ActionChains(self.driver).scroll_by_amount(0, 1000).perform()
                time.sleep(1)

            # More buttons
            more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'More')]")
            for btn in more_buttons[:10]:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
                except: pass

            review_elements = self.driver.find_elements(By.CSS_SELECTOR, '.wiI79')
            for r in review_elements[:10]:
                text = r.text
                if text:
                    reviews_list.append(text.replace('\n', ' ').strip())
        except Exception as e:
            print(f"Error getting reviews: {e}")

        return reviews_list

def save_to_csv(data, category):
    if not data:
        print("No data to save.")
        return
    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=['Name', 'Address'])
    filename = f"addis_ababa_{category.replace(' ', '_')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} results to {filename}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Google Maps Selenium Scraper for Addis Ababa")
    parser.add_argument("--category", type=str, default="restaurants", help="Category to search for")
    parser.add_argument("--neighborhoods", nargs="+", help="Specific neighborhoods to search in")

    args = parser.parse_args()

    scraper = GoogleMapsSeleniumScraper(category=args.category, neighborhoods=args.neighborhoods)
    print(f"Starting scrape for {args.category}...")
    results = scraper.scrape()
    save_to_csv(results, args.category)

if __name__ == "__main__":
    main()
