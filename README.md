# ✈️ Travel Buddy

Travel Buddy is an AI-assisted travel planning application that converts user preferences—destination, dates, budget, and interests—into a structured itinerary, enriched with verified real-world location data, weather forecasts, images, and driving routes.

The core philosophy of this project is to separate **AI-generated planning** from **external data verification**, ensuring reliable, deterministic results rather than relying on LLM hallucinations for factual data.

## 🏗️ Architecture & Pipeline

```text
                         ┌──────────────────────┐
                         │      User Input      │
                         │ Destination / Dates  │
                         │ Days / Budget /      │
                         │ Interests            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                     ┌──────────────────────────┐
                     │   Parallel Initial Work  │
                     ├──────────────────────────┤
                     │                          │
                     │  Groq                    │
                     │  Itinerary generation    │
                     │                          │
                     │  Nominatim / OSM         │
                     │  Destination lookup      │
                     │                          │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │ Structured Itinerary │
                       └──────────┬───────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              Foursquare      WeatherAPI     Openverse
              Place data      Forecast        Images
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │ Verified Coordinates │
                       └──────────┬───────────┘
                                  │
                                  ▼
                              OSRM Routes
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │       Final Output       │
                    ├──────────────────────────┤
                    │ Itinerary                │
                    │ Place information        │
                    │ Weather                  │
                    │ Images                   │
                    │ Daily routes             │
                    │ Interactive map          │
                    └──────────────────────────┘
```

Travel Buddy minimizes latency by executing independent network operations concurrently. The end-to-end pipeline functions as follows:

1. **Concurrent Initialization:** Groq generates a structured itinerary based on user parameters, while Nominatim simultaneously resolves the destination's geographic coordinates.
2. **Structural Validation:** The application validates the LLM's output structure (days, expected sequence, required fields) to prevent malformed data from propagating.
3. **Parallel Enrichment:** Foursquare (places), WeatherAPI (forecasts), and Openverse (images) are queried concurrently to attach factual data to the AI's suggested locations.
4. **Routing & Display:** OSRM calculates daily driving routes using the verified coordinates. The completely enriched dataset is rendered through an interactive Streamlit UI and Folium map.

## 🌐 API Ecosystem

To maintain factual boundaries, the application assigns strict roles to its external services.

- **Groq (LLM) - Itinerary Generation:** Handles planning and logic only; never treated as authoritative for coordinates or addresses.
- **Foursquare - Place Verification:** Resolves AI suggestions to canonical names, real IDs, and precise coordinates.
- **Nominatim/OSM - Geocoding:** Provides geographic context and map centering for the overall destination.
- **WeatherAPI - Forecasting:** Fetches trip-level weather concurrently to avoid redundant per-location requests.
- **Openverse - Image Discovery:** Sources openly licensed images, storing URLs to minimize memory overhead.
- **OSRM - Route Calculation:** Computes driving paths deterministically from Foursquare-verified coordinates.

## ⚙️ Setup & Configuration

This project requires API keys for Groq, Foursquare, and WeatherAPI. Add them to a `.streamlit/secrets.toml` file:

`GROQ_API_KEY = "your_key"`
`FOURSQUARE_API_KEY = "your_key"`
`WEATHERAPI_API_KEY = "your_key"`

**Installation and Execution:**
`pip install -r requirements.txt`
`streamlit run app.py`

> **Prototype Status & Limitations:** Travel Buddy is an engineering prototype demonstrating how LLMs, concurrency, and geospatial APIs can be integrated safely. It is an experimental project and lacks commercial scaling features such as persistent caching, automated testing, rate-limit management, and retry policies.
