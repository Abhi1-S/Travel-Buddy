# ✈️ Travel Buddy

Travel Buddy is an AI-assisted travel itinerary planning application that has evolved from an earlier version of the project into a more complete end-to-end travel planning pipeline.

The project is designed primarily as a **portfolio and learning project** demonstrating how multiple services can be combined to turn a user's travel preferences into a structured, enriched itinerary.

## Purpose

Travel Buddy demonstrates an automated travel-planning workflow where a user provides:

- Destination
- Trip start date
- Number of days
- Budget level
- Interests

The application then generates and enriches an itinerary using multiple external services and APIs.

The goal is **not to provide a production-grade travel booking platform or guarantee perfectly accurate travel recommendations**. Instead, the project focuses on demonstrating practical integration of AI, APIs, data enrichment, routing, weather information, and interactive presentation in a single application.

## What the Application Does

The current pipeline follows this general flow:

**User Input → AI Itinerary Generation → Location Verification → Weather Enrichment → Image Enrichment → Route Calculation → Interactive Presentation**

### AI Itinerary Generation

The application uses Cohere to generate a structured multi-day itinerary based on the user's destination, trip duration, budget, interests, and start date.

The generated itinerary contains locations and activities for:

- Morning
- Midday
- Evening

The AI is instructed to use real locations and avoid unnecessary repetition while producing a geographically sensible schedule.

### Location Verification

Generated locations are enriched using Foursquare Places data.

This provides real-world information such as:

- Place name
- Coordinates
- Address
- Foursquare place identifier

This separates **AI-generated planning** from **real-world location data**.

### Weather

Weather information is added to the itinerary so that users can see expected conditions for each day and, where available, individual itinerary periods.

The application presents information such as:

- Temperature
- Weather condition
- Rain probability
- Sunrise
- Sunset

### Place Images

The application uses the Openverse image API to find openly licensed images associated with itinerary locations.

Images are treated as an enrichment layer rather than the source of truth for the itinerary. Because open image search depends on third-party metadata and community-contributed content, an image may occasionally be unavailable or less representative of the exact location.

The application therefore prioritizes having a functional enrichment pipeline rather than attempting to guarantee perfect image matching for every attraction.

### Routes

The itinerary is further enriched with route information between locations.

This allows the application to present an approximate daily travel route and associated distance/time information.

### Interactive Map

The final itinerary includes an interactive map showing the generated locations and their geographic relationships.

## Design Approach

A key design decision in Travel Buddy is separating responsibilities between the different services.

The AI is responsible for **planning**.

External APIs are responsible for **real-world enrichment and verification**.

The application combines these layers into a single user-facing itinerary.

This makes the project useful as an example of an **AI + API integration pipeline** rather than simply an application that generates text with an LLM.

## Current Scope

Travel Buddy is intentionally scoped as a portfolio project.

It is **not intended to replace dedicated travel platforms, navigation applications, booking services, or professional travel-planning systems**.

The generated itinerary should be treated as a useful starting point for trip planning. Users should independently verify:

- Opening hours
- Ticket availability
- Temporary closures
- Local conditions
- Travel times
- Weather
- Events
- Prices
- Other time-sensitive information

Third-party API availability, quotas, and response quality can also affect the final result.

## What This Project Demonstrates

The project demonstrates practical experience with:

- AI-assisted structured generation
- Prompt engineering
- JSON-based AI responses
- API integration
- External data enrichment
- Location resolution
- Geographic coordinates
- Weather APIs
- Open image search
- Route calculation
- Streamlit application development
- Python service separation
- Caching
- Error handling
- Combining multiple independent services into an end-to-end pipeline

The emphasis is on **building and integrating the pipeline**, rather than claiming perfect real-world accuracy.

## Project Status

Travel Buddy is currently in its **completed portfolio-project stage** and is being prepared for deployment.

A deployed version will be available here:

**Live Demo:** [Coming Soon]

The project continues to use external APIs and services, so functionality can vary depending on API availability, rate limits, quotas, and third-party data.

## Usage

Enter a destination, select the trip duration, budget, and interests, then generate the itinerary.

The application will progressively process the request and enrich the generated itinerary with available location, weather, image, route, and map information.

## Important Note

Travel Buddy should be viewed as an **AI-assisted itinerary generation and enrichment tool**, not an authoritative travel-information source.

Its purpose is to demonstrate how AI-generated planning can be combined with real-world APIs and application logic to create a useful travel-planning experience.

The project prioritizes a working, understandable, end-to-end pipeline and practical engineering decisions over claiming 100% accuracy or production-level reliability.
