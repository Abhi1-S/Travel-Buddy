import requests
import streamlit as st

from config import FOURSQUARE_API_KEY


FOURSQUARE_URL = "https://places-api.foursquare.com/places/search"

FOURSQUARE_API_VERSION = "2025-06-17"


@st.cache_data(ttl=86400, show_spinner=False)
def search_place(place_name: str, city: str):
    """
    Resolve an itinerary location to a real Foursquare place.

    Returns:
        {
            "fsq_place_id": str,
            "name": str,
            "latitude": float,
            "longitude": float,
            "address": str
        }

    Returns None if the place cannot be found.
    """

    if not FOURSQUARE_API_KEY:
        return None

    place_name = place_name.strip()
    city = city.strip()

    if not place_name or not city:
        return None

    headers = {
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
        "X-Places-Api-Version": FOURSQUARE_API_VERSION,
        "Accept": "application/json",
    }

    params = {
        "query": place_name,
        "near": city,
        "limit": 1,
    }

    try:
        response = requests.get(
            FOURSQUARE_URL,
            headers=headers,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

    except (requests.RequestException, ValueError):
        return None

    results = data.get("results", [])

    if not results:
        return None

    place = results[0]

    fsq_place_id = place.get("fsq_place_id")

    if not fsq_place_id:
        return None

    latitude = place.get("latitude")
    longitude = place.get("longitude")

    if latitude is None or longitude is None:
        return None

    location = place.get("location", {})

    return {
        "fsq_place_id": fsq_place_id,
        "name": place.get("name", place_name),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "address": location.get("formatted_address", ""),
    }


def enrich_itinerary(itinerary: dict, city: str):
    """
    Resolve every unique itinerary location once.

    Adds verified Foursquare place information to
    each itinerary section.
    """

    place_cache = {}

    for day in itinerary.get("days", []):

        for period in (
            "morning",
            "midday",
            "evening",
        ):

            section = day.get(period)

            if not section:
                continue

            location = section.get("location")

            if not location:
                continue

            key = location.strip().lower()

            if key not in place_cache:
                place_cache[key] = search_place(
                    location,
                    city,
                )

            section["place"] = place_cache[key]

    return itinerary