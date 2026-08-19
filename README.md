# ✈️ Travel Buddy

Travel Buddy is an AI-assisted travel planning application that creates personalized multi-day itineraries based on a user's destination, travel dates, budget, and interests.

The project started as a simpler travel-planning application and has since been expanded into a more complete pipeline that combines AI-generated planning with real-world location data, weather information, images, routes, and an interactive map.

## What It Does

A user provides:

- Destination
- Trip start date
- Number of days
- Budget
- Interests

Travel Buddy then builds an itinerary with activities for the morning, midday, and evening of each day.

The generated locations are subsequently enriched with information from external services, so the final result is more than just an AI-generated list of places.

The current workflow is:

**User Input → AI Planning → Location Enrichment → Weather → Images → Routes → Map**

## How It Works

### AI Itinerary Generation

The itinerary is generated using Cohere.

The AI considers the destination, trip duration, budget, and the user's interests to create a structured itinerary. It is instructed to use real places, avoid unnecessary repetition, and organize activities into a sensible daily schedule.

### Real Location Data

The locations suggested by the AI are passed through Foursquare Places to obtain real-world information such as coordinates, addresses, and place identifiers.

This allows the application to connect the AI's suggestions with actual locations.

### Weather

Weather information is added to the itinerary based on the destination and travel dates.

The application can display details such as temperature, conditions, rain probability, sunrise, and sunset.

### Images

Travel Buddy uses Openverse to find openly licensed images related to the places in the itinerary.

Images are used to make the itinerary more visual and useful when exploring the generated destinations. Since the images come from an open image index, availability and relevance can vary between locations.

### Routes

The application calculates routes between the locations planned for each day and presents approximate travel distance and duration.

### Interactive Map

The final itinerary is also displayed geographically on an interactive map, giving the user a quick view of where the planned locations are in relation to one another.

## Why I Built It

The main idea behind Travel Buddy was to explore what happens when an AI-generated plan is combined with real-world data and application logic.

Instead of stopping at:

> "Here are some places you could visit."

the project takes those suggestions through several stages of enrichment and turns them into a more complete travel-planning experience.

It also provided a practical way to work with AI APIs, third-party services, structured data, caching, geographic information, and Streamlit in one project.

## Technology

- **Python**
- **Streamlit**
- **Cohere** — itinerary generation
- **Foursquare Places** — location data
- **Open-Meteo / weather service** — weather information
- **Openverse** — openly licensed images
- **Routing service** — route and travel information

## Current State

Travel Buddy is currently at a working end-to-end stage and is being prepared for deployment.

The application can take a user's trip preferences, generate an itinerary, enrich the locations with external data, calculate routes, and present the result through a Streamlit interface.

It is primarily a portfolio project focused on demonstrating the integration of AI and external services into a practical application.

The system depends on several third-party APIs, so results can vary depending on API availability, quotas, and the data returned by those services. The generated itinerary is therefore best viewed as a planning aid rather than a replacement for checking current travel information before a trip.

## Live Demo

**Coming soon:** [Travel Buddy Demo](#)

## Project Focus

Travel Buddy is less about building a perfect travel recommendation engine and more about building a complete, working application around an AI-generated plan.

The project brings together:

**AI + APIs + Data Enrichment + Routing + Maps + Streamlit**

into one travel-planning workflow.
