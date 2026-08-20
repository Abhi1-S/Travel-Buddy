from concurrent.futures import ThreadPoolExecutor, as_completed
import re

import requests
import streamlit as st

from config import FOURSQUARE_API_KEY


FOURSQUARE_URL = "https://places-api.foursquare.com/places/search"
FOURSQUARE_API_VERSION = "2025-06-17"
FOURSQUARE_TIMEOUT = 6
MAX_PLACE_WORKERS = 8


def normalize_name(value: str) -> str:
    """Normalize a place name only for matching/cache keys."""
    if not isinstance(value, str):
        return ""

    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def place_name_matches(requested_name: str, returned_name: str) -> bool:
    """Conservative name match; never accept an unrelated result."""
    requested = normalize_name(requested_name)
    returned = normalize_name(returned_name)

    if not requested or not returned:
        return False

    if requested == returned:
        return True

    requested_words = set(requested.split())
    returned_words = set(returned.split())

    return bool(requested_words) and requested_words.issubset(returned_words)


def _search_foursquare(query: str, city: str):
    headers = {
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
        "X-Places-Api-Version": FOURSQUARE_API_VERSION,
        "Accept": "application/json",
    }

    params = {
        "query": query,
        "near": city,
        "limit": 5,
    }

    try:
        response = requests.get(
            FOURSQUARE_URL,
            headers=headers,
            params=params,
            timeout=FOURSQUARE_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    results = data.get("results", [])
    return results if isinstance(results, list) else []


@st.cache_data(ttl=86400, show_spinner=False)
def search_place(place_name: str, city: str):
    """
    Resolve one itinerary location to a verified Foursquare place.

    Targeted aliases handle known naming variants while conservative
    matching prevents unrelated results such as "St Thomas Hostel" from
    being accepted for "St. Thomas Mount".
    """
    if not FOURSQUARE_API_KEY:
        return None

    if not isinstance(place_name, str) or not isinstance(city, str):
        return None

    place_name = place_name.strip()
    city = city.strip()

    if not place_name or not city:
        return None

    normalized = normalize_name(place_name)

    aliases = {
        "santhome basilica": [
            "San Thome Basilica",
            "San Thome Cathedral",
        ],
        "st thomas mount": [
            "St Thomas Mount",
            "St Thomas Mount Chennai",
        ],
        "kapaleeshwarar temple": [
            "Kapaleeswarar Temple",
            "Mylapore Kapaleeshwarar Temple",
        ],
        "fort st george": [
            "Fort St George",
            "Fort St. George Chennai",
        ],
        "valluvar kottam": [
            "Valluvar Kottam Chennai",
        ],
        "anna nagar tower": [
            "Anna Nagar Tower Park",
            "Anna Nagar Tower Chennai",
        ],
    }

    search_queries = [place_name]
    for alias in aliases.get(normalized, []):
        if alias not in search_queries:
            search_queries.append(alias)

    for query in search_queries:
        for place in _search_foursquare(query, city):
            if not isinstance(place, dict):
                continue

            returned_name = place.get("name")
            if not isinstance(returned_name, str):
                continue

            if not place_name_matches(query, returned_name):
                continue

            fsq_place_id = place.get("fsq_place_id")
            latitude = place.get("latitude")
            longitude = place.get("longitude")

            if not fsq_place_id or latitude is None or longitude is None:
                continue

            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                continue

            location = place.get("location", {})
            if not isinstance(location, dict):
                location = {}

            return {
                "fsq_place_id": fsq_place_id,
                "name": returned_name,
                "latitude": latitude,
                "longitude": longitude,
                "address": location.get("formatted_address", ""),
            }

    return None


def _collect_unique_locations(itinerary: dict):
    """Return unique location requests while preserving itinerary order."""
    requests_list = []
    seen = set()

    for day in itinerary.get("days", []):
        for period in ("morning", "midday", "evening"):
            section = day.get(period)
            if not isinstance(section, dict):
                continue

            location = section.get("location")
            if not isinstance(location, str):
                continue

            location = location.strip()
            key = normalize_name(location)
            if not key or key in seen:
                continue

            seen.add(key)
            requests_list.append((key, location))

    return requests_list


def enrich_itinerary(itinerary: dict, city: str):
    """
    Resolve all unique itinerary locations concurrently, then attach the
    cached/verified result to every matching section.
    """
    unique_locations = _collect_unique_locations(itinerary)
    if not unique_locations:
        return itinerary

    place_cache = {}
    worker_count = min(MAX_PLACE_WORKERS, len(unique_locations))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(search_place, location, city): key
            for key, location in unique_locations
        }

        for future in as_completed(future_map):
            key = future_map[future]
            try:
                place_cache[key] = future.result()
            except Exception:
                place_cache[key] = None

    for day in itinerary.get("days", []):
        for period in ("morning", "midday", "evening"):
            section = day.get(period)
            if not isinstance(section, dict):
                continue

            location = section.get("location")
            if not isinstance(location, str):
                continue

            section["place"] = place_cache.get(normalize_name(location))

    return itinerary
