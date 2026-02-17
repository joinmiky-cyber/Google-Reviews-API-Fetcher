import pandas as pd
from google_places import GooglePlacesClient
import time

def generate_grid(min_lat, max_lat, min_lon, max_lon, step=0.03):
    """Generates a grid of (lat, lon) coordinates."""
    points = []
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            points.append((lat, lon))
            lon += step
        lat += step
    return points

def main():
    # Configuration
    CATEGORIES = ['restaurant'] # Can add 'gym', 'cafe', etc.
    # Addis Ababa Bounding Box
    MIN_LAT, MAX_LAT = 8.83, 9.10
    MIN_LON, MAX_LON = 38.65, 38.90
    STEP = 0.04 # Increase/decrease for more/less density
    SEARCH_RADIUS = 3000 # in meters

    client = GooglePlacesClient()

    all_places = {} # Use dict keyed by place_id to deduplicate

    grid_points = generate_grid(MIN_LAT, MAX_LAT, MIN_LON, MAX_LON, STEP)
    print(f"Generated {len(grid_points)} grid points for Addis Ababa.")

    for category in CATEGORIES:
        print(f"Searching for category: {category}")
        for lat, lon in grid_points:
            print(f"  Searching near {lat}, {lon}...")
            # We use 'keyword' instead of 'type' for some cases,
            # but 'restaurant' is a valid Google type.
            results = client.search_nearby(
                location=(lat, lon),
                radius=SEARCH_RADIUS,
                type_filter=category
            )

            for place in results:
                place_id = place['place_id']
                if place_id not in all_places:
                    all_places[place_id] = {
                        'place_id': place_id,
                        'name': place.get('name'),
                        'vicinity': place.get('vicinity'),
                        'rating': place.get('rating'),
                        'user_ratings_total': place.get('user_ratings_total'),
                    }

            # API hygiene
            time.sleep(0.5)

    print(f"Found {len(all_places)} unique places. Fetching details...")

    # Fetch details for each unique place
    detailed_data = []
    for i, (place_id, basic_info) in enumerate(all_places.items()):
        print(f"[{i+1}/{len(all_places)}] Fetching details for: {basic_info['name']}")
        details = client.get_details(place_id)
        if not details:
            continue

        # Extract Photo References
        photo_refs = []
        if 'photos' in details:
            for photo in details['photos'][:5]: # Limit to 5 photos
                photo_refs.append(photo.get('photo_reference'))

        # Extract Reviews
        reviews_list = []
        if 'reviews' in details:
            for r in details['reviews']:
                reviews_list.append(f"[{r.get('rating')}*] {r.get('author_name')}: {r.get('text')[:200]}...")

        row = {
            'Name': details.get('name'),
            'Phone': details.get('international_phone_number'),
            'Address': details.get('formatted_address'),
            'Latitude': details.get('geometry', {}).get('location', {}).get('lat'),
            'Longitude': details.get('geometry', {}).get('location', {}).get('lng'),
            'Rating': details.get('rating'),
            'Total Ratings': details.get('user_ratings_total'),
            'Types': ", ".join(details.get('types', [])),
            'Website': details.get('website'),
            'Photo References': " | ".join(photo_refs),
            'Top Reviews': " || ".join(reviews_list),
            'Place ID': place_id
        }
        detailed_data.append(row)

        # Avoid hitting rate limits
        time.sleep(0.2)

    # Save to CSV
    if detailed_data:
        df = pd.DataFrame(detailed_data)
        filename = f"addis_ababa_restaurants_{int(time.time())}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Data saved to {filename}")
    else:
        print("No data collected.")

if __name__ == "__main__":
    main()
