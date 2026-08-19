import json
import requests
import streamlit as st
import folium
import cohere

from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

from config import config


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

COHERE_API_KEY = config.cohere_key
FOURSQUARE_API_KEY = config.foursquare_key
GOOGLE_CSE_API_KEY = config.google_cse_key
SEARCH_ENGINE_ID = config.search_id
WEATHERAPI_API_KEY = config.weather_key


# ---------------------------------------------------------
# API URLs
# ---------------------------------------------------------

OSRM_API_URL = "https://router.project-osrm.org/route/v1/driving/"
FOURSQUARE_URL = "https://api.foursquare.com/v3/places/search"
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"
WEATHERAPI_URL = "https://api.weatherapi.com/v1/forecast.json"


# ---------------------------------------------------------
# Cohere client
# ---------------------------------------------------------

co = cohere.ClientV2(api_key=COHERE_API_KEY)


# ---------------------------------------------------------
# AI itinerary generation
# ---------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def generate_itinerary(city, days, budget, focus_category):
    prompt = f"""
Create a {days}-day travel itinerary for a traveler visiting {city}.

Budget level: {budget}
Primary focus: {focus_category}

Return ONLY valid JSON.
Do not use markdown.
Do not add explanations before or after the JSON.

Use exactly this structure:

{{
  "Day 1": {{
    "morning": "Location",
    "midday": "Location",
    "evening": "Location"
  }}
}}

Rules:
- Generate exactly {days} days.
- Every day must contain morning, midday, and evening.
- Each time period must contain exactly ONE location.
- Use real places in {city}.
- Keep locations relevant to the requested focus.
- Avoid repeating the same location.
"""

    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=2500
    )

    text = response.message.content[0].text

    try:
        itinerary = json.loads(text)
    except json.JSONDecodeError:
        return None

    return itinerary


# ---------------------------------------------------------
# Foursquare - coordinates
# ---------------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def get_coordinates(place_name, city):
    if not FOURSQUARE_API_KEY:
        return None, None

    headers = {
        "Authorization": FOURSQUARE_API_KEY
    }

    params = {
        "query": place_name,
        "near": city,
        "limit": 1
    }

    try:
        response = requests.get(
            FOURSQUARE_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return None, None

        results = response.json().get("results", [])

        if not results:
            return None, None

        geocodes = results[0].get("geocodes", {})
        main = geocodes.get("main", {})

        lat = main.get("latitude")
        lng = main.get("longitude")

        if lat is None or lng is None:
            return None, None

        return lat, lng

    except requests.RequestException:
        return None, None


# ---------------------------------------------------------
# OSRM routing
# ---------------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def calculate_route(locations):
    if len(locations) < 2:
        return None

    coords = ";".join(
        f"{lng},{lat}"
        for lat, lng in locations
    )

    url = f"{OSRM_API_URL}{coords}"

    params = {
        "overview": "full",
        "geometries": "geojson"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return None

        data = response.json()

        routes = data.get("routes", [])

        if not routes:
            return None

        return routes[0]["geometry"]["coordinates"]

    except (requests.RequestException, KeyError, IndexError):
        return None


# ---------------------------------------------------------
# Google image search
# ---------------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_place_image(place_name, city):
    if not GOOGLE_CSE_API_KEY or not SEARCH_ENGINE_ID:
        return None

    params = {
        "q": f"{place_name} {city}",
        "cx": SEARCH_ENGINE_ID,
        "key": GOOGLE_CSE_API_KEY,
        "searchType": "image",
        "num": 1,
        "safe": "active"
    }

    try:
        response = requests.get(
            GOOGLE_CSE_URL,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return None

        results = response.json().get("items", [])

        if not results:
            return None

        return results[0].get("link")

    except requests.RequestException:
        return None


# ---------------------------------------------------------
# Weather
# ---------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_weather(city, days):
    if not WEATHERAPI_API_KEY:
        return None

    params = {
        "key": WEATHERAPI_API_KEY,
        "q": city,
        "days": min(days, 6),
        "aqi": "no",
        "alerts": "no"
    }

    try:
        response = requests.get(
            WEATHERAPI_URL,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        return data.get("forecast", {}).get("forecastday", [])

    except requests.RequestException:
        return None


def display_weather_forecast(city, days):
    weather_forecast = fetch_weather(city, days)

    if not weather_forecast:
        st.info("Weather data is currently unavailable.")
        return

    st.subheader(f"Weather Forecast — {city}")

    for day in weather_forecast:
        date = day.get("date", "")
        day_data = day.get("day", {})

        temperature = day_data.get("avgtemp_c")
        condition = day_data.get("condition", {}).get("text")

        if temperature is not None and condition:
            st.write(
                f"**{date}:** {condition} — {temperature:.1f}°C"
            )


# ---------------------------------------------------------
# Itinerary display
# ---------------------------------------------------------

def display_itinerary(itinerary, city):
    for day, schedule in itinerary.items():

        st.subheader(day)

        for time, location in schedule.items():

            st.write(
                f"**{time.capitalize()}:** {location}"
            )

            image_url = fetch_place_image(location, city)

            if image_url:
                st.image(
                    image_url,
                    caption=location,
                    use_container_width=True
                )

            st.write("---")


# ---------------------------------------------------------
# Map
# ---------------------------------------------------------

def plot_itinerary_on_map(itinerary, city):
    city_lat, city_lng = get_coordinates(city, city)

    if city_lat is None or city_lng is None:
        map_center = [28.6139, 77.2090]
    else:
        map_center = [city_lat, city_lng]

    itinerary_map = folium.Map(
        location=map_center,
        zoom_start=12
    )

    marker_cluster = MarkerCluster().add_to(itinerary_map)

    day_colors = [
        "red",
        "blue",
        "green",
        "orange",
        "purple",
        "darkred"
    ]

    for day_index, (day, schedule) in enumerate(itinerary.items()):

        day_coordinates = []

        for time, location in schedule.items():

            lat, lng = get_coordinates(location, city)

            if lat is None or lng is None:
                continue

            folium.Marker(
                location=[lat, lng],
                popup=f"{time.capitalize()}: {location}",
                tooltip=location,
                icon=folium.Icon(
                    color=day_colors[
                        day_index % len(day_colors)
                    ]
                )
            ).add_to(marker_cluster)

            day_coordinates.append((lat, lng))

        # Route only within this day
        if len(day_coordinates) > 1:

            route = calculate_route(
                tuple(day_coordinates)
            )

            if route:

                route_points = [
                    [lat, lng]
                    for lng, lat in route
                ]

                folium.PolyLine(
                    locations=route_points,
                    color=day_colors[
                        day_index % len(day_colors)
                    ],
                    weight=5,
                    opacity=0.7,
                    tooltip=day
                ).add_to(itinerary_map)

    folium_static(itinerary_map)


# ---------------------------------------------------------
# Main application
# ---------------------------------------------------------

def main():

    st.set_page_config(
        page_title="Travel Buddy",
        page_icon="✈️",
        layout="wide"
    )

    st.title("Travel Buddy — Travel Assistance")

    city = st.text_input(
        "Enter city name:",
        "Delhi"
    )

    days = st.slider(
        "Select number of days:",
        min_value=1,
        max_value=6,
        value=5
    )

    budget = st.selectbox(
        "Select budget level:",
        ["Low", "Medium", "High"]
    )

    focus_category = st.text_input(
        "Enter your category of focus:",
        "sightseeing"
    )

    if st.button(
        "Generate Itinerary",
        type="primary"
    ):

        if not city.strip():
            st.error("Please enter a city.")
            return

        with st.spinner("Generating your itinerary..."):

            itinerary = generate_itinerary(
                city.strip(),
                days,
                budget,
                focus_category.strip()
            )

        if not itinerary:
            st.error(
                "Unable to generate a valid itinerary. "
                "Please try again."
            )
            return

        st.subheader("Generated Itinerary")

        display_itinerary(
            itinerary,
            city.strip()
        )

        display_weather_forecast(
            city.strip(),
            days
        )

        st.subheader("Trip Map")

        plot_itinerary_on_map(
            itinerary,
            city.strip()
        )


if __name__ == "__main__":
    main()
