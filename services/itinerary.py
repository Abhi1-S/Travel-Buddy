import json
from datetime import date, timedelta

import cohere
import streamlit as st

from config import COHERE_API_KEY


# ---------------------------------------------------------
# Cohere client
# ---------------------------------------------------------

co = cohere.ClientV2(
    api_key=COHERE_API_KEY
)


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

    The AI determines:
        - locations
        - activities
        - short descriptions

    Other services later add:
        - real-world coordinates
        - weather
        - images
        - road routes
    """

    start = date.fromisoformat(start_date)
    end = start + timedelta(days=days - 1)

    prompt = f"""
Create a detailed {days}-day travel itinerary for a traveler
visiting {city}.

Trip start date: {start.isoformat()}
Trip end date: {end.isoformat()}

Budget level:
{budget}

Primary interests:
{focus_category}

Return ONLY one valid JSON object.

Do not use Markdown.
Do not add explanations before or after the JSON.

Use exactly this structure:

{{
  "destination": "{city}",
  "start_date": "{start.isoformat()}",
  "end_date": "{end.isoformat()}",
  "days": [
    {{
      "day": 1,
      "date": "{start.isoformat()}",
      "morning": {{
        "location": "Real place name",
        "activity": "What the traveler should do there",
        "description": "Short factual description of the location"
      }},
      "midday": {{
        "location": "Real place name",
        "activity": "What the traveler should do there",
        "description": "Short factual description of the location"
      }},
      "evening": {{
        "location": "Real place name",
        "activity": "What the traveler should do there",
        "description": "Short factual description of the location"
      }}
    }}
  ]
}}

Rules:

1. Generate exactly {days} days.

2. Day numbers must start at 1 and increase sequentially.

3. Dates must start at {start.isoformat()} and increase
   by exactly one calendar day.

4. Every day must contain exactly:
   - morning
   - midday
   - evening

5. Every time period must contain exactly ONE location.

6. Every location must contain:
   - location
   - activity
   - description

7. Use real, well-known places that actually exist in {city}.

8. Do not invent attractions, landmarks, museums,
   restaurants, neighborhoods, or other locations.

9. Keep locations relevant to the traveler's interests.

10. Do not repeat the same location during the trip.

11. Group geographically nearby locations together on
    the same day whenever reasonably possible.

12. Within each day, arrange the locations in a sensible
    geographic and travel order:
    morning -> midday -> evening.

13. Avoid unnecessary long-distance travel between
    consecutive locations on the same day.

14. Consider the normal character of each time period.
    For example:
    - morning: attractions, monuments, museums, parks
    - midday: nearby attractions, markets, food areas
    - evening: viewpoints, cultural areas, nightlife,
      evening attractions, or relaxed areas

15. Respect the requested budget level when selecting
    activities and locations.

16. Activities should be concise and practical.

17. Descriptions should be short, factual, and useful.
    Do not write marketing language.

18. Do not include coordinates, addresses, opening hours,
    weather, prices, travel times, or image URLs.
    Those are handled by other services.

19. Do not include additional JSON fields.

20. Do not include multiple locations inside one time period.

21. Prefer established attractions and places that are
    likely to be recognized by a real-world places API.
"""

    # -----------------------------------------------------
    # Call Cohere
    # -----------------------------------------------------

    try:
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[
                cohere.UserChatMessageV2(
                    role="user",
                    content=prompt,
                )
            ],
            response_format=cohere.JsonObjectResponseFormatV2(
                type="json_object"
            ),
            max_tokens=4000,
        )

    except Exception:
        return None

    # -----------------------------------------------------
    # Extract response text
    # -----------------------------------------------------

    content = response.message.content

    if not content:
        return None

    text = None

    for item in content:
        if isinstance(
            item,
            cohere.TextAssistantMessageResponseContentItem,
        ):
            text = item.text
            break

    if not text:
        return None

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:
        itinerary = json.loads(text)

    except json.JSONDecodeError:
        return None

    # -----------------------------------------------------
    # Validate structure
    # -----------------------------------------------------

    if not isinstance(itinerary, dict):
        return None

    generated_days = itinerary.get("days")

    if not isinstance(generated_days, list):
        return None

    if len(generated_days) != days:
        return None

    # -----------------------------------------------------
    # Validate destination metadata
    # -----------------------------------------------------

    if itinerary.get("destination") != city:
        return None

    if itinerary.get("start_date") != start.isoformat():
        return None

    if itinerary.get("end_date") != end.isoformat():
        return None

    # -----------------------------------------------------
    # Validate every day
    # -----------------------------------------------------

    required_periods = (
        "morning",
        "midday",
        "evening",
    )

    expected_date = start
    seen_locations = set()

    for index, day in enumerate(generated_days):

        if not isinstance(day, dict):
            return None

        expected_day_number = index + 1

        if day.get("day") != expected_day_number:
            return None

        if day.get("date") != expected_date.isoformat():
            return None

        for period in required_periods:

            section = day.get(period)

            if not isinstance(section, dict):
                return None

            location = section.get("location")
            activity = section.get("activity")
            description = section.get("description")

            if not isinstance(location, str):
                return None

            if not isinstance(activity, str):
                return None

            if not isinstance(description, str):
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

            location_key = location.casefold()

            if location_key in seen_locations:
                return None

            seen_locations.add(location_key)

        expected_date += timedelta(days=1)

    return itinerary