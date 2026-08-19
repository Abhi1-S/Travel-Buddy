import os
import streamlit as st


class Config:

    def __init__(self):
        self.cohere_key = self._get_secret(
            "COHERE_API_KEY"
        )

        self.foursquare_key = self._get_secret(
            "FOURSQUARE_API_KEY"
        )

        self.google_cse_key = self._get_secret(
            "GOOGLE_CSE_API_KEY"
        )

        self.search_id = self._get_secret(
            "SEARCH_ENGINE_ID"
        )

        self.weather_key = self._get_secret(
            "WEATHERAPI_API_KEY"
        )

    @staticmethod
    def _get_secret(name):
        return st.secrets.get(
            name,
            os.getenv(name)
        )


config = Config()
