from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def get_destination_now(timezone: str) -> datetime:
    """
    Return the current date and time in the destination timezone.
    """
    return datetime.now(ZoneInfo(timezone))


def get_destination_today(timezone: str) -> date:
    """
    Return today's date according to the destination's local timezone.
    """
    return get_destination_now(timezone).date()


def validate_start_date(start_date: date, timezone: str) -> bool:
    """
    A trip cannot start before the current date at the destination.
    """
    destination_today = get_destination_today(timezone)

    return start_date >= destination_today


def generate_trip_dates(
    start_date: date,
    number_of_days: int
) -> list[date]:
    """
    Generate the calendar date for every day of the trip.
    """

    if number_of_days < 1:
        raise ValueError("Trip must contain at least one day.")

    return [
        start_date + timedelta(days=offset)
        for offset in range(number_of_days)
    ]


def build_trip_days(
    start_date: date,
    number_of_days: int
) -> list[dict]:
    """
    Build structured trip-day information.
    """

    trip_dates = generate_trip_dates(
        start_date,
        number_of_days
    )

    return [
        {
            "day": index + 1,
            "date": trip_date,
        }
        for index, trip_date in enumerate(trip_dates)
    ]