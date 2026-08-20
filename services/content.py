from concurrent.futures import ThreadPoolExecutor, as_completed
import re

import requests
import streamlit as st


OPENVERSE_API_URL = "https://api.openverse.org/v1/images/"
USER_AGENT = "TravelBuddy/2.0 (travel itinerary application)"
OPENVERSE_TIMEOUT = 5
MAX_IMAGE_WORKERS = 8


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


@st.cache_data(ttl=86400, show_spinner=False)
def search_openverse_image(place_name: str, city: str) -> str | None:
    """Find a reasonably confident Openverse image URL without downloading it."""
    place_name = place_name.strip()
    city = city.strip()

    if not place_name or not city:
        return None

    params = {
        "q": f"{place_name} {city}",
        "page_size": 10,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(
            OPENVERSE_API_URL,
            params=params,
            headers=headers,
            timeout=OPENVERSE_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    results = data.get("results")
    if not isinstance(results, list):
        return None

    place_normalized = _normalize(place_name)
    city_normalized = _normalize(city)
    place_words = {w for w in place_normalized.split() if len(w) >= 3}
    city_words = {w for w in city_normalized.split() if len(w) >= 3}

    candidates = []

    for result in results:
        if not isinstance(result, dict):
            continue

        image_url = result.get("url")
        if not isinstance(image_url, str) or not image_url.startswith(("http://", "https://")):
            continue

        title = result.get("title", "")
        description = result.get("description", "")
        if not isinstance(title, str):
            title = ""
        if not isinstance(description, str):
            description = ""

        tags = result.get("tags", [])
        tag_names = []
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict) and isinstance(tag.get("name"), str):
                    tag_names.append(_normalize(tag["name"]))

        title_normalized = _normalize(title)
        description_normalized = _normalize(description)
        searchable_text = f"{title_normalized} {description_normalized} {' '.join(tag_names)}"

        score = 0

        if place_normalized == title_normalized:
            score += 30
        elif place_normalized in title_normalized:
            score += 25

        title_place_words = sum(word in title_normalized for word in place_words)
        score += title_place_words * 7
        if place_words and title_place_words == len(place_words):
            score += 10

        tag_place_matches = sum(
            any(word == tag or word in tag for tag in tag_names)
            for word in place_words
        )
        score += tag_place_matches * 5
        if place_words and tag_place_matches == len(place_words):
            score += 8

        description_place_matches = sum(
            word in description_normalized for word in place_words
        )
        score += description_place_matches * 2

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

        fields_matched = result.get("fields_matched", [])
        if isinstance(fields_matched, list):
            if "title" in fields_matched:
                score += 5
            if "tags.name" in fields_matched:
                score += 3
            if "description" in fields_matched:
                score += 1

        width = result.get("width")
        height = result.get("height")
        if isinstance(width, int) and isinstance(height, int):
            if width >= 1000 and height >= 600:
                score += 4
            elif width >= 800 and height >= 500:
                score += 2
            elif width < 500 or height < 300:
                score -= 5

        if not any(word in searchable_text for word in place_words):
            continue

        if (
            len(place_words) >= 2
            and title_place_words == 0
            and tag_place_matches == 0
            and description_place_matches < len(place_words)
        ):
            score -= 12

        if city_words and city_matches == 0:
            score -= 5

        candidates.append((score, image_url))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, best_url = candidates[0]

    return best_url if best_score >= 20 else None


def _collect_unique_locations(itinerary: dict):
    requests_list = []
    seen = set()

    for day in itinerary.get("days", []):
        for period in ("morning", "midday", "evening"):
            section = day.get(period)
            if not isinstance(section, dict):
                continue

            location = section.get("location")
            if not isinstance(location, str):
                continue

            location = location.strip()
            key = location.casefold()
            if not location or key in seen:
                continue

            seen.add(key)
            requests_list.append((key, location))

    return requests_list


def enrich_itinerary_content(itinerary: dict, city: str):
    """Find image URLs for unique places concurrently; no image bytes are downloaded."""
    unique_locations = _collect_unique_locations(itinerary)
    if not unique_locations:
        return itinerary

    image_cache = {}
    worker_count = min(MAX_IMAGE_WORKERS, len(unique_locations))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(search_openverse_image, location, city): key
            for key, location in unique_locations
        }

        for future in as_completed(future_map):
            key = future_map[future]
            try:
                image_cache[key] = future.result()
            except Exception:
                image_cache[key] = None

    for day in itinerary.get("days", []):
        for period in ("morning", "midday", "evening"):
            section = day.get(period)
            if not isinstance(section, dict):
                continue

            location = section.get("location")
            if not isinstance(location, str):
                continue

            section["image"] = image_cache.get(location.strip().casefold())

    return itinerary
