import folium
import streamlit as st

from streamlit_folium import folium_static


DAY_COLORS = [
    "red",
    "blue",
    "green",
    "orange",
    "purple",
    "darkred",
]


def create_itinerary_map(itinerary: dict, city_coordinates=None):
    """
    Create a Folium map containing all itinerary locations
    and one route per day.
    """

    if city_coordinates:
        map_center = [
            city_coordinates[0],
            city_coordinates[1],
        ]
    else:
        map_center = [20.5937, 78.9629]

    itinerary_map = folium.Map(
        location=map_center,
        zoom_start=12,
        control_scale=True,
    )

    for day_index, day in enumerate(
        itinerary.get("days", [])
    ):

        color = DAY_COLORS[
            day_index % len(DAY_COLORS)
        ]

        locations = []

        for period in (
            "morning",
            "midday",
            "evening",
        ):
            section = day.get(period)

            if not section:
                continue

            location_name = section.get("location")
            place = section.get("place")

            if not place:
                continue

            latitude = place.get("latitude")
            longitude = place.get("longitude")

            if latitude is None or longitude is None:
                continue

            locations.append(
                {
                    "period": period,
                    "name": location_name,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

        # -------------------------------------------------
        # Markers
        # -------------------------------------------------

        for stop_index, location in enumerate(locations):

            popup = folium.Popup(
                f"""
                <b>{location["name"]}</b><br>
                {location["period"].capitalize()}<br>
                Stop {stop_index + 1}
                """,
                max_width=300,
            )

            folium.Marker(
                location=[
                    location["latitude"],
                    location["longitude"],
                ],
                popup=popup,
                tooltip=location["name"],
                icon=folium.Icon(
                    color=color,
                    icon="map-marker",
                ),
            ).add_to(itinerary_map)

        # -------------------------------------------------
        # Route
        # -------------------------------------------------

        route = day.get("route")

        if route and route.get("geometry"):

            route_points = [
                [latitude, longitude]
                for longitude, latitude
                in route["geometry"]
            ]

            folium.PolyLine(
                locations=route_points,
                color=color,
                weight=5,
                opacity=0.75,
                tooltip=day.get(
                    "title",
                    f"Day {day_index + 1}",
                ),
            ).add_to(itinerary_map)

    return itinerary_map


def display_itinerary_map(
    itinerary: dict,
    city_coordinates=None,
):
    """
    Render the itinerary map inside Streamlit.
    """

    itinerary_map = create_itinerary_map(
        itinerary,
        city_coordinates,
    )

    folium_static(
        itinerary_map,
        width=None,
        height=650,
    )