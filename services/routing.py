from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st


OSRM_API_URL = (
    "https://router.project-osrm.org/route/v1/driving/"
)

ROUTE_TIMEOUT = 6


@st.cache_data(
    ttl=86400,
    show_spinner=False,
)
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

    Returns None if a route cannot be calculated quickly.
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
            timeout=ROUTE_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

    except (
        requests.RequestException,
        ValueError,
    ):
        return None

    routes = data.get("routes", [])

    if not routes:
        return None

    route = routes[0]

    geometry = (
        route
        .get("geometry", {})
        .get("coordinates", [])
    )

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


def _get_day_locations(day: dict):
    """
    Extract route coordinates for one itinerary day.
    """

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

        try:
            coordinates = (
                float(latitude),
                float(longitude),
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        day_locations.append(coordinates)

    return tuple(day_locations)


def _calculate_day_route(day: dict):
    """
    Calculate the route for one day.
    """

    locations = _get_day_locations(day)

    if len(locations) < 2:
        return None

    return calculate_route(locations)


def add_routes_to_itinerary(itinerary: dict):
    """
    Calculate routes for all itinerary days concurrently.

    Each day's OSRM request is independent, so a 6-day trip
    can calculate up to 6 routes concurrently.
    """

    days = itinerary.get("days", [])

    if not days:
        return itinerary

    # -----------------------------------------------------
    # Calculate daily routes concurrently
    # -----------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=min(6, len(days))
    ) as executor:

        futures = [
            executor.submit(
                _calculate_day_route,
                day,
            )
            for day in days
        ]

        routes = [
            future.result()
            for future in futures
        ]

    # -----------------------------------------------------
    # Attach routes to their corresponding days
    # -----------------------------------------------------

    for day, route in zip(days, routes):
        day["route"] = route

    return itinerary