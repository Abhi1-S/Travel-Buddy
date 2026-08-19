from datetime import date
from typing import Optional

import requests
import streamlit as st

from config import WEATHERAPI_API_KEY


WEATHERAPI_URL = "https://api.weatherapi.com/v1/forecast.json"


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather(city: str, days: int):
    """
    Fetch the destination forecast once for the entire trip.

    WeatherAPI currently supports forecasts for up to 6 days
    with the selected API plan.
    """

    if not WEATHERAPI_API_KEY:
        return None

    params = {
        "key": WEATHERAPI_API_KEY,
        "q": city,
        "days": min(days, 6),
        "aqi": "no",
        "alerts": "no",
    }

    try:
        response = requests.get(
            WEATHERAPI_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

    except (requests.RequestException, ValueError):
        return None

    return data.get("forecast", {}).get("forecastday", [])


def _find_forecast_day(
    forecast: list,
    target_date: date,
):
    """
    Find the forecast corresponding to a specific calendar date.
    """

    target = target_date.isoformat()

    for day in forecast:
        if day.get("date") == target:
            return day

    return None


def _find_hourly_weather(
    forecast_day: dict,
    hour: int,
):
    """
    Find the hourly forecast closest to the requested hour.
    """

    hours = forecast_day.get("hour", [])

    if not hours:
        return None

    return min(
        hours,
        key=lambda item: abs(
            int(item.get("time", "00:00").split(" ")[1].split(":")[0])
            - hour
        ),
    )


def get_period_weather(
    forecast: list,
    target_date: date,
    period: str,
) -> Optional[dict]:
    """
    Get weather for a specific itinerary period.

    Approximate periods:
        morning -> 09:00
        midday  -> 13:00
        evening -> 19:00
    """

    period_hours = {
        "morning": 9,
        "midday": 13,
        "evening": 19,
    }

    hour = period_hours.get(period.lower())

    if hour is None:
        return None

    forecast_day = _find_forecast_day(
        forecast,
        target_date,
    )

    if not forecast_day:
        return None

    hourly = _find_hourly_weather(
        forecast_day,
        hour,
    )

    if not hourly:
        return None

    return {
        "time": hourly.get("time"),
        "temperature_c": hourly.get("temp_c"),
        "feels_like_c": hourly.get("feelslike_c"),
        "condition": hourly.get("condition", {}).get("text"),
        "icon": hourly.get("condition", {}).get("icon"),
        "rain_chance": hourly.get("chance_of_rain"),
        "humidity": hourly.get("humidity"),
        "wind_kph": hourly.get("wind_kph"),
    }


def get_day_weather(
    forecast: list,
    target_date: date,
) -> Optional[dict]:
    """
    Get the overall weather summary for a specific trip day.
    """

    forecast_day = _find_forecast_day(
        forecast,
        target_date,
    )

    if not forecast_day:
        return None

    day_data = forecast_day.get("day", {})

    condition = day_data.get("condition", {})

    return {
        "date": forecast_day.get("date"),
        "max_temp_c": day_data.get("maxtemp_c"),
        "min_temp_c": day_data.get("mintemp_c"),
        "avg_temp_c": day_data.get("avgtemp_c"),
        "condition": condition.get("text"),
        "icon": condition.get("icon"),
        "rain_chance": day_data.get("daily_chance_of_rain"),
        "sunrise": forecast_day.get("astro", {}).get("sunrise"),
        "sunset": forecast_day.get("astro", {}).get("sunset"),
    }


def enrich_itinerary_weather(
    itinerary: dict,
    city: str,
):
    """
    Add weather information to every itinerary day and period.

    One forecast request is made for the entire trip.
    """

    days = itinerary.get("days", [])

    if not days:
        return itinerary

    forecast = fetch_weather(
        city,
        len(days),
    )

    if not forecast:
        return itinerary

    for day in days:

        try:
            target_date = date.fromisoformat(
                day["date"]
            )
        except (KeyError, TypeError, ValueError):
            continue

        day["weather"] = get_day_weather(
            forecast,
            target_date,
        )

        for period in (
            "morning",
            "midday",
            "evening",
        ):
            section = day.get(period)

            if not section:
                continue

            section["weather"] = get_period_weather(
                forecast,
                target_date,
                period,
            )

    return itinerary