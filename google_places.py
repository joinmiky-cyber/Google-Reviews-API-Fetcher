import os
import time
import googlemaps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GooglePlacesClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key not found. Please set it in .env or provide it directly.")
        self.gmaps = googlemaps.Client(key=self.api_key)

    def search_nearby(self, location, radius, type_filter=None, keyword=None):
        """
        Search for places in a given location and radius.
        Note: nearby_search can return up to 60 results (3 pages of 20).
        """
        results = []
        try:
            # First page
            response = self.gmaps.places_nearby(
                location=location,
                radius=radius,
                type=type_filter,
                keyword=keyword
            )
            results.extend(response.get('results', []))

            # Subsequent pages (if any)
            while 'next_page_token' in response:
                # Need to wait a bit for the next_page_token to become valid
                time.sleep(2)
                response = self.gmaps.places_nearby(
                    page_token=response['next_page_token']
                )
                results.extend(response.get('results', []))
        except Exception as e:
            print(f"Error during search: {e}")

        return results

    def get_details(self, place_id):
        """
        Fetch full details for a place, including photos and reviews.
        """
        fields = [
            'name', 'formatted_address', 'geometry', 'international_phone_number',
            'rating', 'user_ratings_total', 'reviews', 'photos', 'types', 'website'
        ]
        try:
            response = self.gmaps.place(place_id=place_id, fields=fields)
            return response.get('result', {})
        except Exception as e:
            print(f"Error fetching details for {place_id}: {e}")
            return None
