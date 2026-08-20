import requests
import streamlit as st
from timezonefinder import TimezoneFinder


GEOCODING_URL = "https://nominatim.openstreetmap.org/search"
GEOCODING_TIMEOUT = 6

timezone_finder = TimezoneFinder()


@st.cache_data(ttl=86400, show_spinner=False)
def resolve_destination(city: str):
    """Resolve a city to coordinates/timezone for map centering."""
    if not isinstance(city, str):
        return None

    city = city.strip()
    if not city:
        return None

    params = {
        "q": city,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": "TravelBuddy/2.0"}

    try:
        response = requests.get(
            GEOCODING_URL,
            params=params,
            headers=headers,
            timeout=GEOCODING_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not isinstance(results, list) or not results:
        return None

    result = results[0]
    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    timezone = timezone_finder.timezone_at(
        lat=latitude,
        lng=longitude,
    )

    return {
        "name": result.get("display_name", city),
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone or "",
    }
