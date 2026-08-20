import os
import streamlit as st


def get_secret(name: str):
    """Get a secret from Streamlit secrets or environment variables."""
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name)


GROQ_API_KEY = get_secret("GROQ_API_KEY")

FOURSQUARE_API_KEY = get_secret("FOURSQUARE_API_KEY")
WEATHERAPI_API_KEY = get_secret("WEATHERAPI_API_KEY")