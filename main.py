import csv
import time
import re
import argparse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException

# Predefined neighborhoods in Addis Ababa for better coverage
ADDIS_NEIGHBORHOODS = [
    "Bole, Addis Ababa",
    "Piazza, Addis Ababa",
    "Kazanchis, Addis Ababa",
    "Old Airport, Addis Ababa",
    "Sarbet, Addis Ababa",
    "Haya Hulet, Addis Ababa",
    "4 Kilo, Addis Ababa",
    "22 Mazoria, Addis Ababa",
    "Gerji, Addis Ababa",
    "Lebu, Addis Ababa"
]

class GoogleMapsSeleniumScraper:
    def __init__(self, headless=False):
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        self.options.set_preference("general.useragent.override", "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0")
        self.options.set_preference("intl.accept_languages", "en-US, en")

        self.driver = webdriver.Firefox(options=self.options)
        self.wait = WebDriverWait(self.driver, 15)
        self.seen_urls = set()

    def __del__(self):
        try:
            self.driver.quit()
        except:
            pass

    def bypass_cookies(self):
        try:
            buttons = self.driver.find_elements(By.XPATH, "//button")
            for btn in buttons:
                if any(text in btn.text.lower() for text in ["accept all", "agree", "i agree", "tout accepter"]):
                    btn.click()
                    time.sleep(2)
                    break
        except:
            pass

    def search_businesses(self, query, retries=2):
        for attempt in range(retries + 1):
            try:
                print(f"Searching for: {query} (Attempt {attempt + 1})")
                self.driver.get("https://www.google.com/maps?hl=en")
                self.bypass_cookies()

                search_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='q']")))
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.ENTER)
                time.sleep(5)

                if self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc") or self.driver.find_elements(By.XPATH, "//button[@role='tab']"):
                    if not self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc") and self.driver.find_elements(By.XPATH, "//button[@role='tab']"):
                        return ["DIRECT_MATCH"]
                    return self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
            except Exception:
                pass
            time.sleep(2)
        return []

    def scroll_results(self, max_results=20):
        try:
            results_container = None
            for xpath in ["//div[@role='feed']", "//div[contains(@aria-label, 'Results for')]", "//div[contains(@class, 'm6QErb')]"]:
                elems = self.driver.find_elements(By.XPATH, xpath)
                if elems:
                    results_container = elems[0]
                    break

            if results_container:
                for _ in range(10):
                    self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", results_container)
                    time.sleep(2)
                    if len(self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")) >= max_results: break
        except:
            pass

    def clean_text(self, text):
        if not text: return "N/A"
        cleaned = re.sub(r'^[^\w\s\+]+', '', text, flags=re.MULTILINE).strip()
        cleaned = cleaned.replace('', 'Yes:').replace('', 'No:')
        return cleaned

    def extract_gps(self, url):
        match = re.search(r'@([-.\d]+),([-.\d]+)', url)
        if match:
            return match.group(1), match.group(2)
        match_3d = re.search(r'!3d([-.\d]+)!4d([-.\d]+)', url)
        if match_3d:
            return match_3d.group(1), match_3d.group(2)
        return "N/A", "N/A"

    def scrape_business_details(self, business_element=None):
        if business_element and business_element != "DIRECT_MATCH":
            try:
                self.driver.execute_script("arguments[0].scrollIntoView();", business_element)
                try: business_element.click()
                except: self.driver.execute_script("arguments[0].click();", business_element)
                time.sleep(4)
            except:
                return None

        details = {}
        try:
            # Metadata
            details['google_maps_url'] = self.driver.current_url

            # Deduplication check using URL (cleaned of parameters that might change)
            url_id = details['google_maps_url'].split('/data=')[0]
            if url_id in self.seen_urls:
                print(f"Skipping duplicate URL: {url_id}")
                return "DUPLICATE"

            # Name
            try:
                details['name'] = self.driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
            except:
                h1s = self.driver.find_elements(By.TAG_NAME, "h1")
                details['name'] = "N/A"
                for h in h1s:
                    if h.text and h.text != "Results":
                        details['name'] = h.text
                        break

            details['latitude'], details['longitude'] = self.extract_gps(details['google_maps_url'])

            # Basic Info
            try: details['address'] = self.clean_text(self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Address')]").text)
            except: details['address'] = "N/A"
            try: details['phone'] = self.clean_text(self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Phone')]").text)
            except: details['phone'] = "N/A"
            try: details['website'] = self.driver.find_element(By.XPATH, "//a[contains(@aria-label, 'Website')]").get_attribute("href")
            except: details['website'] = "N/A"

            # Rating
            try:
                rating_elem = self.driver.find_element(By.XPATH, "//span[contains(@aria-label, 'stars') and string-length(@aria-label) > 6]")
                details['rating'] = rating_elem.get_attribute("aria-label")
            except:
                try: details['rating'] = self.driver.find_element(By.CSS_SELECTOR, "span.ce40Ff").text
                except: details['rating'] = "N/A"

            # About
            try:
                about_tab = self.driver.find_elements(By.XPATH, "//button[@role='tab' and contains(., 'About')]")
                if about_tab:
                    about_tab[0].click()
                    time.sleep(2)
                    sections = self.driver.find_elements(By.XPATH, "//div[@role='region']")
                    about_info = []
                    for sec in sections:
                        title = sec.get_attribute("aria-label") or "Info"
                        items = sec.find_elements(By.XPATH, ".//li | .//div[contains(@aria-label, ':')]")
                        if items:
                            item_texts = [self.clean_text(i.text or i.get_attribute("aria-label")) for i in items if (i.text or i.get_attribute("aria-label"))]
                            about_info.append(f"{title}: {', '.join(item_texts)}")
                    details['about'] = "; ".join(about_info)
                    overview_tab = self.driver.find_elements(By.XPATH, "//button[@role='tab' and contains(., 'Overview')]")
                    if overview_tab: overview_tab[0].click()
                    time.sleep(1)
                else:
                    details['about'] = "N/A"
            except:
                details['about'] = "N/A"

            # Reviews
            review_list = []
            try:
                review_tab = self.driver.find_elements(By.XPATH, "//button[@role='tab' and contains(., 'Reviews')]")
                if not review_tab:
                    review_tab = self.driver.find_elements(By.XPATH, "//button[contains(translate(@aria-label, 'REVIEWS', 'reviews'), 'reviews')]")

                if review_tab:
                    review_tab[0].click()
                    time.sleep(3)
                    review_containers = self.driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
                    for rc in review_containers[:10]:
                        try:
                            author = rc.find_element(By.CSS_SELECTOR, "div.d4r55").text
                            rating_val = rc.find_element(By.CSS_SELECTOR, "span.kvMY9b").get_attribute("aria-label")
                            date = rc.find_element(By.CSS_SELECTOR, "span.rsqawe").text
                            try:
                                more_btn = rc.find_element(By.CSS_SELECTOR, "button.w8Bnuf")
                                more_btn.click()
                                time.sleep(0.5)
                            except: pass
                            text = rc.find_element(By.CSS_SELECTOR, "span.wiI7Nr").text
                            review_list.append(f"{author} ({rating_val}, {date}): {text}")
                        except: pass
                    details['reviews'] = " | ".join(review_list) if review_list else "N/A"
                    overview_tab = self.driver.find_elements(By.XPATH, "//button[@role='tab' and contains(., 'Overview')]")
                    if overview_tab: overview_tab[0].click()
                    time.sleep(1)
                else:
                    details['reviews'] = "N/A"
            except:
                details['reviews'] = "N/A"

            # Photos
            def extract_urls_from_photo_container(limit=5):
                urls = []
                # Looking for images in the photo pane
                photo_elements = self.driver.find_elements(By.XPATH, "//div[contains(@style, 'background-image')]")
                if not photo_elements:
                    # Alternative for some layouts
                    photo_elements = self.driver.find_elements(By.TAG_NAME, "img")

                for pe in photo_elements:
                    url = None
                    if pe.tag_name == "img":
                        url = pe.get_attribute("src")
                    else:
                        style = pe.get_attribute("style")
                        url_match = re.search(r'url\("(.*?)"\)', style)
                        if url_match: url = url_match.group(1)

                    if url and "googleusercontent" in url: # Ensure it's a content URL
                        if url not in urls: urls.append(url)
                    if len(urls) >= limit: break
                return urls

            details['photo_urls_all'] = "N/A"
            details['photo_urls_menu'] = "N/A"
            try:
                photo_tab = self.driver.find_elements(By.XPATH, "//button[@role='tab' and contains(., 'Photos')]")
                if photo_tab:
                    photo_tab[0].click()
                    time.sleep(3)

                    # Default view is 'All'
                    details['photo_urls_all'] = "; ".join(extract_urls_from_photo_container(5))

                    # Try to find 'Menu' filter button/radio
                    menu_filter = self.driver.find_elements(By.XPATH, "//button[contains(., 'Menu')] | //div[@role='radio' and contains(., 'Menu')]")
                    if menu_filter:
                        menu_filter[0].click()
                        time.sleep(2)
                        details['photo_urls_menu'] = "; ".join(extract_urls_from_photo_container(5))

                    overview_tab = self.driver.find_elements(By.XPATH, "//button[@role='tab' and contains(., 'Overview')]")
                    if overview_tab: overview_tab[0].click()
                    time.sleep(1)
            except:
                pass

            self.seen_urls.add(url_id)

        except Exception as e:
            print(f"Error: {e}")
            return None

        return details

    def scrape_category(self, category, location, max_results=10):
        query = f"{category} in {location}"
        results = self.search_businesses(query)
        if not results: return []
        if results == ["DIRECT_MATCH"]:
            data = self.scrape_business_details("DIRECT_MATCH")
            if data == "DUPLICATE": return []
            return [data] if data else []

        self.scroll_results(max_results)
        results = self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        scraped_data = []
        for i in range(min(len(results), max_results)):
            try:
                results = self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
                if i >= len(results): break
                biz_info = self.scrape_business_details(results[i])
                if biz_info == "DUPLICATE": continue
                if biz_info:
                    scraped_data.append(biz_info)
                    print(f"Scraped: {biz_info.get('name')}")
            except StaleElementReferenceException:
                continue
        return scraped_data

def save_to_csv(data, filename):
    if not data: return
    df = pd.DataFrame(data)
    try:
        existing_df = pd.read_csv(filename)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        if 'google_maps_url' in combined_df.columns:
            combined_df['url_id'] = combined_df['google_maps_url'].str.split('/data=').str[0]
            combined_df = combined_df.drop_duplicates(subset=['url_id']).drop(columns=['url_id'])
        else:
            combined_df = combined_df.drop_duplicates(subset=['name'])
        combined_df.to_csv(filename, index=False, encoding='utf-8')
    except FileNotFoundError:
        df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Data updated in {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Google Maps Scraper for Addis Ababa')
    parser.add_argument('--category', type=str, default='Restaurants', help='Category to search')
    parser.add_argument('--location', type=str, help='Specific location (overrides neighborhood list)')
    parser.add_argument('--max', type=int, default=10, help='Max results per search location')
    parser.add_argument('--output', type=str, default='google_maps_data.csv', help='Output CSV')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')

    args = parser.parse_args()
    locations = [args.location] if args.location else ADDIS_NEIGHBORHOODS
    scraper = GoogleMapsSeleniumScraper(headless=args.headless)
    try:
        for loc in locations:
            print(f"Scraping {args.category} in {loc}...")
            data = scraper.scrape_category(args.category, loc, max_results=args.max)
            if data:
                save_to_csv(data, args.output)
        print("Scraping process completed.")
    finally:
        del scraper
