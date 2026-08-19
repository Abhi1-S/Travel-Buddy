from datetime import date

import streamlit as st

from services.location import resolve_destination
from services.itinerary import generate_itinerary
from services.places import enrich_itinerary
from services.weather import enrich_itinerary_weather
from services.routing import add_routes_to_itinerary
from services.content import enrich_itinerary_content
from services.maps import display_itinerary_map


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Travel Buddy",
    page_icon="✈️",
    layout="wide",
)


# ---------------------------------------------------------
# Display helpers
# ---------------------------------------------------------

def display_day_weather(weather):
    if not weather:
        st.info("Weather data is currently unavailable.")
        return

    max_temp = weather.get("max_temp_c")
    min_temp = weather.get("min_temp_c")
    condition = weather.get("condition")
    rain = weather.get("rain_chance")

    parts = []

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

    sunrise = weather.get("sunrise")
    sunset = weather.get("sunset")

    if sunrise or sunset:
        sunlight = []

        if sunrise:
            sunlight.append(f"Sunrise: {sunrise}")

        if sunset:
            sunlight.append(f"Sunset: {sunset}")

        st.caption(" • ".join(sunlight))


def display_period_weather(weather):
    if not weather:
        return

    temperature = weather.get("temperature_c")
    condition = weather.get("condition")
    rain = weather.get("rain_chance")

    parts = []

    if temperature is not None:
        parts.append(f"{temperature:.1f}°C")

    if condition:
        parts.append(condition)

    if rain is not None:
        parts.append(f"{rain}% rain")

    if parts:
        st.caption(" • ".join(parts))


def display_day(day):
    day_number = day.get("day")
    trip_date = day.get("date")

    st.header(
        f"Day {day_number} — {trip_date}"
    )

    # -----------------------------------------------------
    # Whole-day weather
    # -----------------------------------------------------

    with st.container(border=True):
        st.markdown("### 🌤️ Weather")
        display_day_weather(
            day.get("weather")
        )

    # -----------------------------------------------------
    # Morning / Midday / Evening
    # -----------------------------------------------------

    for period in (
        "morning",
        "midday",
        "evening",
    ):
        section = day.get(period)

        if not section:
            continue

        location = section.get(
            "location",
            "Unknown location",
        )

        description = section.get(
            "description",
            "",
        )

        image = section.get("image")

        st.subheader(
            f"{period.capitalize()} — {location}"
        )

        if image:
            st.image(
                image,
                caption=location,
                use_container_width=True,
            )

        if description:
            st.write(description)

        display_period_weather(
            section.get("weather")
        )

        place = section.get("place")

        if place:
            address = place.get("address")

            if address:
                st.caption(
                    f"📍 {address}"
                )

        st.divider()

    # -----------------------------------------------------
    # Daily route
    # -----------------------------------------------------

    route = day.get("route")

    if route:
        distance = route.get("distance_km")
        duration = route.get("duration_min")

        parts = []

        if distance is not None:
            parts.append(
                f"{distance:.1f} km"
            )

        if duration is not None:
            parts.append(
                f"{duration:.0f} min driving"
            )

        if parts:
            st.markdown(
                f"🚗 **Day route:** "
                f"{' • '.join(parts)}"
            )


# ---------------------------------------------------------
# Progress helper
# ---------------------------------------------------------

def show_progress(
    progress_bar,
    status_box,
    current,
    total,
    message,
):
    progress_bar.progress(
        current / total
    )

    status_box.markdown(
        f"**{message}**"
    )


# ---------------------------------------------------------
# Main application
# ---------------------------------------------------------

def main():

    st.title("✈️ Travel Buddy")

    st.write(
        "Plan a personalized multi-day trip with "
        "AI-generated itineraries, real locations, "
        "weather forecasts, images, and daily routes."
    )

    # -----------------------------------------------------
    # Inputs
    # -----------------------------------------------------

    with st.container(border=True):

        st.subheader("Plan your trip")

        city = st.text_input(
            "Destination",
            placeholder="e.g. Delhi",
        )

        today = date.today()

        start_date = st.date_input(
            "Trip start date",
            min_value=today,
            value=today,
        )

        days = st.slider(
            "Number of days",
            min_value=1,
            max_value=6,
            value=3,
        )

        budget = st.selectbox(
            "Budget",
            [
                "Low",
                "Medium",
                "High",
            ],
        )

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
    focus_category = focus_category.strip()

    if not city:
        st.error(
            "Please enter a destination."
        )
        return

    if start_date < today:
        st.error(
            "The trip start date cannot be earlier "
            "than today."
        )
        return

    if not focus_category:
        focus_category = "sightseeing"

    # -----------------------------------------------------
    # Progress UI
    # -----------------------------------------------------

    st.subheader("✈️ Building your trip")

    progress_bar = st.progress(0)

    status_box = st.empty()

    # -----------------------------------------------------
    # Step 1 — Resolve destination
    # -----------------------------------------------------

    show_progress(
        progress_bar,
        status_box,
        1,
        6,
        "📍 Finding your destination...",
    )

    destination = resolve_destination(
        city
    )

    if not destination:
        status_box.error(
            "Could not resolve that destination."
        )
        st.error(
            "Please check the city name and try again."
        )
        return

    st.success(
        f"✓ Destination found: {destination['name']}"
    )

    # -----------------------------------------------------
    # Step 2 — Generate itinerary
    # -----------------------------------------------------

    show_progress(
        progress_bar,
        status_box,
        2,
        6,
        "🧠 Creating your itinerary...",
    )

    itinerary = generate_itinerary(
        city=city,
        days=days,
        budget=budget,
        focus_category=focus_category,
        start_date=start_date.isoformat(),
    )

    if not itinerary:
        status_box.error(
            "Unable to generate a valid itinerary."
        )
        return

    generated_days = itinerary.get(
        "days",
        [],
    )

    if len(generated_days) != days:
        status_box.error(
            "The generated itinerary did not contain "
            "the expected number of days."
        )
        return

    # -----------------------------------------------------
    # SHOW AI ITINERARY IMMEDIATELY
    # -----------------------------------------------------

    status_box.success(
        "✓ Itinerary created"
    )

    st.divider()

    st.subheader("🗓️ Your itinerary")

    for day in itinerary["days"]:

        with st.container(border=True):

            st.markdown(
                f"### Day {day.get('day')} — "
                f"{day.get('date')}"
            )

            cols = st.columns(3)

            for column, period in zip(
                cols,
                (
                    "morning",
                    "midday",
                    "evening",
                ),
            ):

                section = day.get(period)

                if not section:
                    continue

                with column:

                    st.markdown(
                        f"**{period.capitalize()}**"
                    )

                    st.write(
                        section.get(
                            "location",
                            "Unknown location",
                        )
                    )

                    st.caption(
                        section.get(
                            "activity",
                            "",
                        )
                    )

    # -----------------------------------------------------
    # Step 3 — Verify locations
    # -----------------------------------------------------

    show_progress(
        progress_bar,
        status_box,
        3,
        6,
        "📍 Verifying places and coordinates...",
    )

    itinerary = enrich_itinerary(
        itinerary,
        city,
    )

    status_box.success(
        "✓ Locations verified"
    )

    # -----------------------------------------------------
    # Step 4 — Weather
    # -----------------------------------------------------

    show_progress(
        progress_bar,
        status_box,
        4,
        6,
        "🌤️ Checking weather forecasts...",
    )

    itinerary = enrich_itinerary_weather(
        itinerary,
        city,
    )

    status_box.success(
        "✓ Weather loaded"
    )

    # -----------------------------------------------------
    # Step 5 — Images
    # -----------------------------------------------------

    show_progress(
        progress_bar,
        status_box,
        5,
        6,
        "🖼️ Finding images for your destinations...",
    )

    itinerary = enrich_itinerary_content(
        itinerary,
        city,
    )

    status_box.success(
        "✓ Images loaded"
    )

    # -----------------------------------------------------
    # Step 6 — Routes
    # -----------------------------------------------------

    show_progress(
        progress_bar,
        status_box,
        6,
        6,
        "🗺️ Calculating daily routes...",
    )

    itinerary = add_routes_to_itinerary(
        itinerary
    )

    progress_bar.progress(1.0)

    status_box.success(
        f"✓ Your {days}-day trip is ready!"
    )

    # -----------------------------------------------------
    # Final enriched itinerary
    # -----------------------------------------------------

    st.divider()

    st.header("📋 Detailed Itinerary")

    for day in itinerary["days"]:
        display_day(day)

    # -----------------------------------------------------
    # Map
    # -----------------------------------------------------

    st.header("🗺️ Trip Map")

    display_itinerary_map(
        itinerary,
        (
            destination["latitude"],
            destination["longitude"],
        ),
    )


if __name__ == "__main__":
    main()