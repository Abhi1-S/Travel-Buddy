import requests
from timezonefinder import TimezoneFinder


GEOCODING_URL = "https://nominatim.openstreetmap.org/search"

timezone_finder = TimezoneFinder()


def resolve_destination(city: str):
    """
    Resolve a city name into coordinates and timezone.

    Returns:
        {
            "name": str,
            "latitude": float,
            "longitude": float,
            "timezone": str
        }

    Returns None if the destination cannot be resolved.
    """

    city = city.strip()

    if not city:
        return None

    params = {
        "q": city,
        "format": "json",
        "limit": 1,
    }

    headers = {
        "User-Agent": "TravelBuddy/2.0"
    }

    try:
        response = requests.get(
            GEOCODING_URL,
            params=params,
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        results = response.json()

    except (requests.RequestException, ValueError):
        return None

    if not results:
        return None

    result = results[0]

    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    timezone = timezone_finder.timezone_at(
        lat=latitude,
        lng=longitude
    )

    if not timezone:
        return None

    return {
        "name": result.get("display_name", city),
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
    }