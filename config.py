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


COHERE_API_KEY = get_secret("COHERE_API_KEY")
FOURSQUARE_API_KEY = get_secret("FOURSQUARE_API_KEY")
GOOGLE_CSE_API_KEY = get_secret("GOOGLE_CSE_API_KEY")
SEARCH_ENGINE_ID = get_secret("SEARCH_ENGINE_ID")
WEATHERAPI_API_KEY = get_secret("WEATHERAPI_API_KEY")