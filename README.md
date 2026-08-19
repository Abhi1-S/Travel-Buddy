# 🌍 Travel Buddy

Travel Buddy is a Python-based travel planning application that generates multi-day itineraries based on the destination, budget, and travel interests.

The project uses Cohere to generate the itinerary and combines it with external APIs for places, images, weather information, and route visualization.

## Features

- Generate multi-day travel itineraries using Cohere
- Choose the trip duration, budget, and area of interest
- Find locations using the Foursquare Places API
- Display images of recommended locations using Google Custom Search
- Show weather forecasts for the selected city
- Display destinations on an interactive Folium map
- Generate driving routes between locations using OSRM
- Cache external API results to reduce repeated requests

## Tech Stack

- Python
- Streamlit
- Cohere
- Foursquare Places API
- Google Custom Search API
- WeatherAPI
- OSRM
- Folium
- Streamlit-Folium

## Project Structure

    travel-buddy/
    │
    ├── .devcontainer/
    │   └── devcontainer.json
    │
    ├── app.py
    ├── config.py
    ├── requirements.txt
    └── README.md

## Installation

Clone the repository and install the required packages:

    git clone https://github.com/Abhisatr/travel-buddy.git
    cd travel-buddy
    pip install -r requirements.txt

Python 3.11 is recommended.

## API Configuration

The application requires API keys for the following services:

- Cohere
- Foursquare
- Google Custom Search
- WeatherAPI

The application reads the keys from Streamlit secrets or environment variables.

For local Streamlit development, create:

    .streamlit/secrets.toml

and add:

    COHERE_API_KEY = "your_cohere_key"
    FOURSQUARE_API_KEY = "your_fsq_key"
    GOOGLE_CSE_API_KEY = "your_google_cse_key"
    SEARCH_ENGINE_ID = "your_search_engine_id"
    WEATHERAPI_API_KEY = "your_weather_key"

Do not commit real API keys to the repository.

### API Documentation

- [Cohere](https://docs.cohere.com/)
- [Foursquare Places API](https://docs.foursquare.com/)
- [Google Programmable Search](https://programmablesearchengine.google.com/)
- [WeatherAPI](https://www.weatherapi.com/)

## Running the Application

Start the Streamlit application with:

    streamlit run app.py

The application will open in the browser at:

    http://localhost:8501

## Using Travel Buddy

The application asks for four inputs:

1. **City** - The destination city.
2. **Number of days** - Trip duration from 1 to 6 days.
3. **Budget** - Low, Medium, or High.
4. **Focus category** - The type of places or activities you are interested in.

For example:

    City: Paris
    Days: 4
    Budget: Medium
    Focus: Art galleries, cafes

After generating the itinerary, the application displays the suggested locations, images, weather information, and an interactive map.

## Maps and Routes

Travel Buddy uses Foursquare to obtain coordinates for locations and OSRM to calculate driving routes.

Routes are generated separately for each day instead of connecting locations across different days.

## Performance

External API requests are cached where appropriate to avoid making the same request repeatedly during Streamlit reruns.

Weather information is retrieved for the selected city rather than making separate weather requests for every attraction.

## Deployment

The application can be deployed on Streamlit Community Cloud or another platform that supports Python and Streamlit.

For Streamlit deployment, add the required API keys to the application's Secrets configuration.

Example:

    COHERE_API_KEY = "..."
    FOURSQUARE_API_KEY = "..."
    GOOGLE_CSE_API_KEY = "..."
    SEARCH_ENGINE_ID = "..."
    WEATHERAPI_API_KEY = "..."

## Live Application

[Live Demo](YOUR_STREAMLIT_APP_URL)

The live application link will be added after the updated version is deployed.

## License

This project is distributed under the MIT License. See `LICENSE` for details.

## Acknowledgments

- [Cohere](https://cohere.com/) for the language model
- [Foursquare](https://foursquare.com/) for place information
- [Google](https://developers.google.com/custom-search/) for image search
- [WeatherAPI](https://www.weatherapi.com/) for weather data
- [OSRM](https://project-osrm.org/) for route calculation
- [Streamlit](https://streamlit.io/) for the application framework
