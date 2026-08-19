import re

import requests
import streamlit as st


OPENVERSE_API_URL = "https://api.openverse.org/v1/images/"

USER_AGENT = (
    "TravelBuddy/2.0 "
    "(travel itinerary application)"
)


# ---------------------------------------------------------
# Openverse image search
# ---------------------------------------------------------

@st.cache_data(
    ttl=86400,
    show_spinner=False,
)
def search_openverse_image(
    place_name: str,
    city: str,
) -> str | None:

    place_name = place_name.strip()
    city = city.strip()

    if not place_name or not city:
        return None

    params = {
        "q": f"{place_name} {city}",
        "page_size": 15,
    }

    headers = {
        "User-Agent": USER_AGENT,
    }

    try:
        response = requests.get(
            OPENVERSE_API_URL,
            params=params,
            headers=headers,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

    except (requests.RequestException, ValueError):
        return None

    results = data.get("results")

    if not isinstance(results, list):
        return None

    # -----------------------------------------------------
    # Normalize search terms
    # -----------------------------------------------------

    def normalize(text: str) -> str:
        return re.sub(
            r"[^a-z0-9]+",
            " ",
            text.lower(),
        ).strip()

    place_normalized = normalize(place_name)
    city_normalized = normalize(city)

    place_words = {
        word
        for word in place_normalized.split()
        if len(word) >= 3
    }

    city_words = {
        word
        for word in city_normalized.split()
        if len(word) >= 3
    }

    candidates = []

    # -----------------------------------------------------
    # Score candidates
    # -----------------------------------------------------

    for result in results:

        if not isinstance(result, dict):
            continue

        image_url = result.get("url")

        if not isinstance(image_url, str):
            continue

        if not image_url.startswith(
            ("http://", "https://")
        ):
            continue

        title = result.get("title", "")

        if not isinstance(title, str):
            title = ""

        description = result.get(
            "description",
            "",
        )

        if not isinstance(description, str):
            description = ""

        tags = result.get("tags", [])

        tag_names = []

        if isinstance(tags, list):
            for tag in tags:

                if not isinstance(tag, dict):
                    continue

                name = tag.get("name")

                if isinstance(name, str):
                    tag_names.append(
                        normalize(name)
                    )

        title_normalized = normalize(title)
        description_normalized = normalize(
            description
        )

        searchable_text = (
            title_normalized
            + " "
            + description_normalized
            + " "
            + " ".join(tag_names)
        )

        score = 0

        # -------------------------------------------------
        # Strong place-name matching
        # -------------------------------------------------

        if place_normalized == title_normalized:
            score += 30

        elif (
            place_normalized
            in title_normalized
        ):
            score += 25

        # Every important place word in title
        title_place_words = 0

        for word in place_words:

            if word in title_normalized:
                title_place_words += 1
                score += 7

        # Reward all place words appearing in title
        if (
            place_words
            and title_place_words
            == len(place_words)
        ):
            score += 10

        # -------------------------------------------------
        # Place words in tags
        # -------------------------------------------------

        tag_place_matches = 0

        for word in place_words:

            if any(
                word == tag
                or word in tag
                for tag in tag_names
            ):
                tag_place_matches += 1
                score += 5

        if (
            place_words
            and tag_place_matches
            == len(place_words)
        ):
            score += 8

        # -------------------------------------------------
        # Place words in description
        # -------------------------------------------------

        description_place_matches = 0

        for word in place_words:

            if word in description_normalized:
                description_place_matches += 1
                score += 2

        # -------------------------------------------------
        # City matching
        # -------------------------------------------------

        city_matches = 0

        for word in city_words:

            if word in title_normalized:
                city_matches += 1
                score += 4

            elif word in tag_names:
                city_matches += 1
                score += 2

            elif word in description_normalized:
                city_matches += 1
                score += 1

        # -------------------------------------------------
        # Openverse's own matching information
        # -------------------------------------------------

        fields_matched = result.get(
            "fields_matched",
            [],
        )

        if isinstance(fields_matched, list):

            if "title" in fields_matched:
                score += 5

            if "tags.name" in fields_matched:
                score += 3

            if "description" in fields_matched:
                score += 1

        # -------------------------------------------------
        # Image quality
        # -------------------------------------------------

        width = result.get("width")
        height = result.get("height")

        if (
            isinstance(width, int)
            and isinstance(height, int)
        ):

            if width >= 1000 and height >= 600:
                score += 4

            elif width >= 800 and height >= 500:
                score += 2

            elif width < 500 or height < 300:
                score -= 5

        # -------------------------------------------------
        # Penalize weak / generic matches
        # -------------------------------------------------

        # If none of the actual place words occur
        # anywhere in the metadata, reject it.
        if not any(
            word in searchable_text
            for word in place_words
        ):
            continue

        # If the place has multiple words and only one
        # weak word matches, penalize heavily.
        if (
            len(place_words) >= 2
            and title_place_words == 0
            and tag_place_matches == 0
            and description_place_matches < len(
                place_words
            )
        ):
            score -= 12

        # If city is completely absent from metadata,
        # reduce confidence.
        if city_words and city_matches == 0:
            score -= 5

        # -------------------------------------------------
        # Save candidate
        # -------------------------------------------------

        candidates.append(
            (
                score,
                image_url,
                title,
            )
        )

    # -----------------------------------------------------
    # No suitable candidates
    # -----------------------------------------------------

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score, best_url, best_title = (
        candidates[0]
    )

    # -----------------------------------------------------
    # Confidence threshold
    #
    # Important:
    # Wrong image > no image
    # -----------------------------------------------------

    if best_score < 20:
        return None

    return best_url


# ---------------------------------------------------------
# Download image
# ---------------------------------------------------------

@st.cache_data(
    ttl=86400,
    show_spinner=False,
)
def download_image(
    image_url: str,
) -> bytes | None:

    headers = {
        "User-Agent": USER_AGENT,
    }

    try:
        response = requests.get(
            image_url,
            headers=headers,
            timeout=15,
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        if not content_type.startswith(
            "image/"
        ):
            return None

        return response.content

    except requests.RequestException:
        return None


# ---------------------------------------------------------
# Fetch place content
# ---------------------------------------------------------

def fetch_place_content(
    place_name: str,
    city: str,
):
    image_url = search_openverse_image(
        place_name,
        city,
    )

    image_bytes = None

    if image_url is not None:
        image_bytes = download_image(
            image_url
        )

    return {
        "image": image_bytes,
        "description": "",
    }


# ---------------------------------------------------------
# Enrich itinerary
# ---------------------------------------------------------

def enrich_itinerary_content(
    itinerary: dict,
    city: str,
):
    """
    Add image and description information
    to every unique itinerary location.
    """

    content_cache = {}

    for day in itinerary.get(
        "days",
        [],
    ):

        for period in (
            "morning",
            "midday",
            "evening",
        ):

            section = day.get(period)

            if not isinstance(section, dict):
                continue

            location = section.get(
                "location"
            )

            if not isinstance(location, str):
                continue

            location = location.strip()

            if not location:
                continue

            key = location.lower()

            if key not in content_cache:

                content_cache[key] = (
                    fetch_place_content(
                        location,
                        city,
                    )
                )

            content = content_cache[key]

            section["image"] = content.get(
                "image"
            )

            if not section.get(
                "description"
            ):
                section["description"] = (
                    section.get(
                        "activity",
                        "",
                    )
                )

    return itinerary