
🌍 Travel Buddy:
Uses Cohere to auto-generate itineraries.
Integrates Foursquare locations, WeatherAPI forecasts, and OSRM routing. Features interactive maps with optimized routes . Mobile-friendly trip planning made easy!


An intelligent travel planning system that creates personalized itineraries using **Cohere's AI** and real-time data from **Foursquare**, **Google Maps**, and **WeatherAPI**.

## ✨ Features

- 🧠 **AI-Powered Itineraries** - Generate multi-day plans using Cohere's Command-R
- 🗺️ **Interactive Map Visualization** - Folium maps with optimal OSRM routing
- ⛅ **6-Day Weather Forecast** - Integrated WeatherAPI predictions
- 📸 **Automatic Place Images** - Google Custom Search image integration
- 📱 **Mobile-Optimized** - Full responsive design for all devices

## 🛠️ Installation

```bash
git clone https://github.com/Abhisatr/travel-buddy.git
cd travel-buddy
pip install -r requirements.txt
```

## 🔑 Configuration

1. Create `.env` file:
```env
COHERE_API_KEY="your_cohere_key"
FOURSQUARE_API_KEY="your_fsq_key"
GOOGLE_CSE_API_KEY="your_google_cse_key"
SEARCH_ENGINE_ID="your_search_engine_id"
WEATHERAPI_API_KEY="your_weather_key"
```

2. Get API keys:
- [Cohere Dashboard](https://dashboard.cohere.com/)
- [Foursquare Developers](https://foursquare.com/developers/)
- [Google CSE](https://programmablesearchengine.google.com/)
- [WeatherAPI](https://www.weatherapi.com/)

## 🚀 Usage

```bash
streamlit run app.py
```

**Input Format**:
1. City Name (e.g "Delhi")
2. Trip Duration (1-6 days)
3. Budget Level (Low/Medium/High)
4. Focus Categories (e.g "museums, street food")

**Example**:
```python
City: Paris
Days: 4 
Budget: Medium
Focus: Art galleries, cafes
```

## ☁️ Deployment

1. **Streamlit Sharing**:
```toml
# secrets.toml
[secrets]
COHERE_API_KEY = "..."
FOURSQUARE_API_KEY = "..."
GOOGLE_CSE_API_KEY = "..."
SEARCH_ENGINE_ID = "..."
WEATHERAPI_API_KEY = "..."
```

2. **Other Platforms**:
- Set environment variables matching `.env` format
- Add `secrets.toml` to your deployment's configuration

## 🤝 Contributing

1. Fork the repository
2. Create feature branch:
```bash
git checkout -b feature/amazing-feature
```
3. Commit changes:
```bash
git commit -m 'Add amazing feature'
```
4. Push to branch:
```bash
git push origin feature/amazing-feature
```
5. Open a Pull Request

## 📜 License

Distributed under MIT License. See `LICENSE` for details.

## 🙏 Acknowledgments

- [Cohere](https://cohere.com) for AI capabilities
- [Foursquare API](https://developer.foursquare.com/) for location data
- [WeatherAPI](https://www.weatherapi.com/) for weather forecasts
- [Streamlit](https://streamlit.io) for deployment framework
- [OSRM](http://project-osrm.org/) for routing engine


## Can Access At below link:
- https://travel-buddy-oqcs7cdz8dhf3t3c3h58eu.streamlit.app/

```

**To Use**:
1. Replace placeholder image URL with actual screenshots
2. Update Streamlit app URL when deployed
3. Add real API keys in configuration
4. Customize acknowledgments as needed

This README includes:
- Mobile-friendly formatting
- Clear installation/usage instructions
- API key management guidance
- Deployment instructions
- Contribution guidelines
- Proper licensing
- Badges for quick reference

For complete functionality, ensure you have:
1. Valid API keys for all services
2. Python 3.9+ environment
3. Active internet connection during use
