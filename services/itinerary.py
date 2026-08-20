import json
import re
from datetime import date, timedelta

import streamlit as st
from groq import Groq

from config import GROQ_API_KEY


# ---------------------------------------------------------
# Groq client
# ---------------------------------------------------------

client = Groq(
    api_key=GROQ_API_KEY
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MODEL = "openai/gpt-oss-20b"

MIN_DAYS = 1
MAX_DAYS = 6

LOCATIONS_PER_DAY = 3

REQUEST_TIMEOUT = 25
MAX_TOKENS = 1200


# ---------------------------------------------------------
# Location normalization
# ---------------------------------------------------------

def normalize_location_name(location: str) -> str:
    """
    Normalize a place name only for duplicate detection.

    The original AI-generated name is preserved for display.
    """

    if not isinstance(location, str):
        return ""

    value = location.casefold().strip()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    removable_words = {
        "arulmigu",
        "sri",
        "shri",
        "sree",
        "swamy",
        "swami",
        "temple",
        "museum",
        "beach",
        "park",
        "garden",
        "fort",
        "palace",
        "church",
        "cathedral",
        "mosque",
        "mandir",
        "masjid",
        "hall",
        "centre",
        "center",
    }

    words = value.split()

    meaningful_words = [
        word
        for word in words
        if word not in removable_words
    ]

    if not meaningful_words:
        meaningful_words = words

    return " ".join(meaningful_words)


# ---------------------------------------------------------
# AI itinerary generation
# ---------------------------------------------------------

@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def generate_itinerary(
    city: str,
    days: int,
    budget: str,
    focus_category: str,
    start_date: str,
):
    """
    Generate a structured multi-day travel itinerary.

    The AI generates only:

        location
        activity
        description

    Other services handle:

        place verification
        coordinates
        weather
        images
        routes
    """

    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if not isinstance(days, int):
        return None

    if days < MIN_DAYS or days > MAX_DAYS:
        return None

    if not isinstance(city, str):
        return None

    city = city.strip()

    if not city:
        return None

    if not isinstance(budget, str):
        budget = ""

    budget = budget.strip()

    if not isinstance(focus_category, str):
        focus_category = ""

    focus_category = focus_category.strip()

    try:
        start = date.fromisoformat(start_date)

    except (TypeError, ValueError):
        return None

    end = start + timedelta(days=days - 1)

    expected_dates = [
        (
            start + timedelta(days=index)
        ).isoformat()
        for index in range(days)
    ]

    # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    prompt = f"""
Create a {days}-day travel itinerary for {city}.

Dates:
{start.isoformat()} to {end.isoformat()}

Budget: {budget}
Interests: {focus_category}

Generate exactly 3 different real places for EACH day.

The three places for every day must be ordered:

1. morning
2. midday
3. evening

Rules:

- Use real, established places in {city}.
- Never invent a place.
- Never intentionally repeat a place anywhere in the trip.
- Never use alternate names for the same physical place.
- Prefer geographically nearby places on the same day.
- Arrange places in sensible travel order.
- Match the itinerary to the requested interests.
- Activity must be short and practical.
- Description must be one short factual sentence.
- Do not include addresses.
- Do not include coordinates.
- Do not include prices.
- Do not include weather.
- Do not include opening hours.
- Do not include images.
- Do not include routes.

The required dates are exactly:

{", ".join(expected_dates)}

Return exactly those dates.
Each date must contain exactly three places.
"""

    # -----------------------------------------------------
    # JSON Schema
    # -----------------------------------------------------

    date_properties = {}

    for expected_date in expected_dates:

        date_properties[expected_date] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string"
                    },
                    "activity": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                },
                "required": [
                    "location",
                    "activity",
                    "description",
                ],
                "additionalProperties": False,
            },
            "minItems": LOCATIONS_PER_DAY,
            "maxItems": LOCATIONS_PER_DAY,
        }

    itinerary_schema = {
        "type": "object",
        "properties": date_properties,
        "required": expected_dates,
        "additionalProperties": False,
    }

    # -----------------------------------------------------
    # Call Groq
    # -----------------------------------------------------

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a travel itinerary generator. "
                        "Return only the requested structured data. "
                        "Use real established places and never "
                        "intentionally invent locations."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "travel_itinerary",
                    "strict": True,
                    "schema": itinerary_schema,
                },
            },
            max_tokens=MAX_TOKENS,
            temperature=0,
            reasoning_effort="low",
            timeout=REQUEST_TIMEOUT,
        )

    except Exception as exc:
        print(
            f"Groq itinerary generation failed: {exc}"
        )
        return None

    # -----------------------------------------------------
    # Extract response
    # -----------------------------------------------------

    if not response.choices:
        return None

    message = response.choices[0].message

    text = message.content

    if not text:
        return None

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:
        raw_itinerary = json.loads(text)

    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(raw_itinerary, dict):
        return None

    # -----------------------------------------------------
    # Validate date keys
    # -----------------------------------------------------

    if set(raw_itinerary.keys()) != set(
        expected_dates
    ):
        return None

    # -----------------------------------------------------
    # Convert to application structure
    # -----------------------------------------------------

    generated_days = []

    # Tracks normalized names across the ENTIRE trip.
    seen_locations = set()

    for index, expected_date in enumerate(
        expected_dates
    ):

        places_for_day = raw_itinerary.get(
            expected_date
        )

        if not isinstance(
            places_for_day,
            list,
        ):
            return None

        if len(places_for_day) != LOCATIONS_PER_DAY:
            return None

        day_data = {
            "day": index + 1,
            "date": expected_date,
        }

        periods = (
            "morning",
            "midday",
            "evening",
        )

        for period, section in zip(
            periods,
            places_for_day,
        ):

            if not isinstance(section, dict):
                return None

            location = section.get(
                "location"
            )

            activity = section.get(
                "activity"
            )

            description = section.get(
                "description"
            )

            if not isinstance(
                location,
                str,
            ):
                return None

            if not isinstance(
                activity,
                str,
            ):
                return None

            if not isinstance(
                description,
                str,
            ):
                return None

            location = location.strip()
            activity = activity.strip()
            description = description.strip()

            if not location:
                return None

            if not activity:
                return None

            if not description:
                return None

            # -------------------------------------------------
            # Duplicate / alternate-name detection
            # -------------------------------------------------

            location_key = normalize_location_name(
                location
            )

            if not location_key:
                return None

            if location_key in seen_locations:
                return None

            seen_locations.add(
                location_key
            )

            day_data[period] = {
                "location": location,
                "activity": activity,
                "description": description,
            }

        generated_days.append(day_data)

    # ---------------------------------------------------------
    # Final itinerary
    # ---------------------------------------------------------

    itinerary = {
        "destination": city,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days": generated_days,
    }

    # ---------------------------------------------------------
    # Final structural validation
    # ---------------------------------------------------------

    if len(itinerary["days"]) != days:
        return None

    total_locations = 0

    for day in itinerary["days"]:

        for period in (
            "morning",
            "midday",
            "evening",
        ):

            if period not in day:
                return None

            section = day[period]

            if not isinstance(section, dict):
                return None

            if not section.get("location"):
                return None

            if not section.get("activity"):
                return None

            if not section.get("description"):
                return None

            total_locations += 1

    expected_total = (
        days * LOCATIONS_PER_DAY
    )

    if total_locations != expected_total:
        return None

    return itinerary