import requests
import streamlit as st


OSRM_API_URL = "https://router.project-osrm.org/route/v1/driving/"


@st.cache_data(ttl=86400, show_spinner=False)
def calculate_route(locations: tuple):
    """
    Calculate a driving route through the supplied locations.

    locations:
        (
            (latitude, longitude),
            (latitude, longitude),
            ...
        )

    Returns:
        {
            "geometry": [...],
            "distance_km": float,
            "duration_min": float
        }

    Returns None if a route cannot be calculated.
    """

    if len(locations) < 2:
        return None

    coordinates = ";".join(
        f"{longitude},{latitude}"
        for latitude, longitude in locations
    )

    url = f"{OSRM_API_URL}{coordinates}"

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

    except (requests.RequestException, ValueError):
        return None

    routes = data.get("routes", [])

    if not routes:
        return None

    route = routes[0]

    geometry = route.get("geometry", {}).get("coordinates", [])

    if not geometry:
        return None

    return {
        "geometry": geometry,
        "distance_km": round(
            route.get("distance", 0) / 1000,
            2,
        ),
        "duration_min": round(
            route.get("duration", 0) / 60,
            1,
        ),
    }


def add_routes_to_itinerary(itinerary: dict):
    """
    Calculate one route for each day.

    The order is the itinerary order:
        morning -> midday -> evening

    Routes never connect locations belonging to different days.
    """

    for day in itinerary.get("days", []):

        day_locations = []

        for period in (
            "morning",
            "midday",
            "evening",
        ):
            section = day.get(period)

            if not section:
                continue

            place = section.get("place")

            if not place:
                continue

            latitude = place.get("latitude")
            longitude = place.get("longitude")

            if latitude is None or longitude is None:
                continue

            day_locations.append(
                (
                    float(latitude),
                    float(longitude),
                )
            )

        route = calculate_route(
            tuple(day_locations)
        )

        day["route"] = route

    return itinerary