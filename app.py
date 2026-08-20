from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date

import streamlit as st

from services.location import resolve_destination
from services.itinerary import generate_itinerary
from services.places import enrich_itinerary
from services.weather import enrich_itinerary_weather
from services.routing import add_routes_to_itinerary
from services.content import enrich_itinerary_content
from services.maps import display_itinerary_map


st.set_page_config(
    page_title="Travel Buddy",
    page_icon="✈️",
    layout="wide",
)


def display_day_weather(weather):
    if not weather:
        st.info("Weather data is currently unavailable.")
        return

    parts = []
    max_temp = weather.get("max_temp_c")
    min_temp = weather.get("min_temp_c")
    condition = weather.get("condition")
    rain = weather.get("rain_chance")

    if max_temp is not None:
        parts.append(f"{max_temp:.1f}°C max")
    if min_temp is not None:
        parts.append(f"{min_temp:.1f}°C min")
    if condition:
        parts.append(condition)
    if rain is not None:
        parts.append(f"{rain}% rain")

    if parts:
        st.write(" • ".join(parts))

    sunlight = []
    sunrise = weather.get("sunrise")
    sunset = weather.get("sunset")
    if sunrise:
        sunlight.append(f"Sunrise: {sunrise}")
    if sunset:
        sunlight.append(f"Sunset: {sunset}")
    if sunlight:
        st.caption(" • ".join(sunlight))


def display_period_weather(weather):
    if not weather:
        return

    parts = []
    temperature = weather.get("temperature_c")
    condition = weather.get("condition")
    rain = weather.get("rain_chance")

    if temperature is not None:
        parts.append(f"{temperature:.1f}°C")
    if condition:
        parts.append(condition)
    if rain is not None:
        parts.append(f"{rain}% rain")

    if parts:
        st.caption(" • ".join(parts))


def display_day(day):
    st.header(f"Day {day.get('day')} — {day.get('date')}")

    with st.container(border=True):
        st.markdown("### 🌤️ Weather")
        display_day_weather(day.get("weather"))

    for period in ("morning", "midday", "evening"):
        section = day.get(period)
        if not section:
            continue

        location = section.get("location", "Unknown location")
        description = section.get("description", "")
        image = section.get("image")

        st.subheader(f"{period.capitalize()} — {location}")

        if image:
            st.image(image, caption=location, use_container_width=True)
        if description:
            st.write(description)

        display_period_weather(section.get("weather"))

        place = section.get("place")
        if place and place.get("address"):
            st.caption(f"📍 {place['address']}")

        st.divider()

    route = day.get("route")
    if route:
        parts = []
        distance = route.get("distance_km")
        duration = route.get("duration_min")
        if distance is not None:
            parts.append(f"{distance:.1f} km")
        if duration is not None:
            parts.append(f"{duration:.0f} min driving")
        if parts:
            st.markdown(f"🚗 **Day route:** {' • '.join(parts)}")


def show_progress(progress_bar, status_box, current, total, message):
    progress_bar.progress(current / total)
    status_box.markdown(f"**{message}**")


def _enrich_places_and_routes(itinerary: dict, city: str):
    """Resolve places first, then calculate routes immediately from those coordinates."""
    result = enrich_itinerary(deepcopy(itinerary), city)
    return add_routes_to_itinerary(result)


def enrich_trip_parallel(itinerary: dict, city: str):
    """
    Run enrichment concurrently.

    Branches:
      1. Foursquare -> routes (route starts as soon as places resolve)
      2. Weather
      3. Openverse image URLs
    """
    with ThreadPoolExecutor(max_workers=3) as executor:
        places_routes_future = executor.submit(
            _enrich_places_and_routes,
            itinerary,
            city,
        )
        weather_future = executor.submit(
            enrich_itinerary_weather,
            deepcopy(itinerary),
            city,
        )
        content_future = executor.submit(
            enrich_itinerary_content,
            deepcopy(itinerary),
            city,
        )

        places_routes_result = places_routes_future.result()
        weather_result = weather_future.result()
        content_result = content_future.result()

    return places_routes_result, weather_result, content_result


def merge_enrichment_results(
    itinerary: dict,
    places_result: dict,
    weather_result: dict,
    content_result: dict,
):
    """Merge enrichment data without replacing AI-generated fields."""
    original_days = itinerary.get("days", [])
    places_days = places_result.get("days", []) if places_result else []
    weather_days = weather_result.get("days", []) if weather_result else []
    content_days = content_result.get("days", []) if content_result else []

    for index, day in enumerate(original_days):
        if index < len(places_days):
            source_day = places_days[index]
            if "route" in source_day:
                day["route"] = source_day["route"]
            for period in ("morning", "midday", "evening"):
                if period in source_day:
                    day[period]["place"] = source_day[period].get("place")

        if index < len(weather_days):
            source_day = weather_days[index]
            if "weather" in source_day:
                day["weather"] = source_day["weather"]
            for period in ("morning", "midday", "evening"):
                if period in source_day:
                    weather = source_day[period].get("weather")
                    if weather is not None:
                        day[period]["weather"] = weather

        if index < len(content_days):
            source_day = content_days[index]
            for period in ("morning", "midday", "evening"):
                if period in source_day and "image" in source_day[period]:
                    day[period]["image"] = source_day[period]["image"]

    return itinerary


def _count_verified_places(itinerary: dict) -> int:
    return sum(
        1
        for day in itinerary.get("days", [])
        for period in ("morning", "midday", "evening")
        if isinstance(day.get(period, {}).get("place"), dict)
    )


def main():
    st.title("✈️ Travel Buddy")
    st.write(
        "Plan a personalized multi-day trip with AI-generated itineraries, "
        "real locations, weather forecasts, images, and daily routes."
    )

    with st.container(border=True):
        st.subheader("Plan your trip")

        city = st.text_input("Destination", placeholder="e.g. Delhi")
        today = date.today()
        start_date = st.date_input("Trip start date", min_value=today, value=today)
        days = st.slider("Number of days", min_value=1, max_value=6, value=3)
        budget = st.selectbox("Budget", ["Low", "Medium", "High"])
        focus_category = st.text_input(
            "Interests",
            value="sightseeing",
            placeholder="e.g. museums, food, history",
        )
        generate = st.button(
            "Generate Itinerary",
            type="primary",
            use_container_width=True,
        )

    if not generate:
        return

    city = city.strip()
    focus_category = focus_category.strip() or "sightseeing"

    if not city:
        st.error("Please enter a destination.")
        return

    if start_date < today:
        st.error("The trip start date cannot be earlier than today.")
        return

    st.subheader("✈️ Building your trip")
    progress_bar = st.progress(0)
    status_box = st.empty()

    # Destination lookup is useful only for the map. Start it at the same
    # time as Groq instead of blocking Groq behind another network request.
    show_progress(progress_bar, status_box, 1, 4, "🧠 Creating your itinerary...")

    with ThreadPoolExecutor(max_workers=2) as executor:
        destination_future = executor.submit(resolve_destination, city)
        itinerary_future = executor.submit(
            generate_itinerary,
            city=city,
            days=days,
            budget=budget,
            focus_category=focus_category,
            start_date=start_date.isoformat(),
        )

        itinerary = itinerary_future.result()
        destination = destination_future.result()

    if not itinerary:
        status_box.error("Unable to generate a valid itinerary.")
        return

    if len(itinerary.get("days", [])) != days:
        status_box.error("The generated itinerary did not contain the expected number of days.")
        return

    status_box.success("✓ Itinerary created")
    progress_bar.progress(0.25)

    # The core AI result is already available here; enrichment is optional
    # data augmentation and runs independently.
    st.divider()
    st.subheader("🗓️ Your itinerary")

    for day in itinerary["days"]:
        with st.container(border=True):
            st.markdown(f"### Day {day.get('day')} — {day.get('date')}")
            cols = st.columns(3)
            for column, period in zip(cols, ("morning", "midday", "evening")):
                section = day.get(period)
                if not section:
                    continue
                with column:
                    st.markdown(f"**{period.capitalize()}**")
                    st.write(section.get("location", "Unknown location"))
                    st.caption(section.get("activity", ""))

    show_progress(progress_bar, status_box, 2, 4, "⚡ Enriching places, weather, images, and routes...")

    places_result, weather_result, content_result = enrich_trip_parallel(itinerary, city)

    itinerary = merge_enrichment_results(
        itinerary,
        places_result,
        weather_result,
        content_result,
    )

    verified_count = _count_verified_places(itinerary)
    total_places = days * 3

    if verified_count == 0:
        status_box.warning(
            "Itinerary created, but no locations could be verified right now. "
            "External place services may be unavailable."
        )
    else:
        status_box.success(
            f"✓ Trip ready — {verified_count}/{total_places} locations verified"
        )

    progress_bar.progress(1.0)

    st.divider()
    st.header("📋 Detailed Itinerary")
    for day in itinerary["days"]:
        display_day(day)

    st.header("🗺️ Trip Map")

    city_coordinates = None
    if destination:
        city_coordinates = (
            destination["latitude"],
            destination["longitude"],
        )

    display_itinerary_map(itinerary, city_coordinates)


if __name__ == "__main__":
    main()
