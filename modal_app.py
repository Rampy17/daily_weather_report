"""Modal webhook for Daily Weather Report - Houston forecast.

This module provides HTTP endpoints for fetching Houston weather forecasts.
Deploy with: modal deploy modal_app.py
"""

import modal
from typing import Optional, Dict, Any
import json
import requests
import time
from datetime import datetime

# Create Modal app
app = modal.App("daily-weather-report")

# Define the Docker image with required dependencies
image = modal.Image.debian_slim().pip_install(
    "requests==2.31.0",
    "python-dotenv==1.0.0"
)


class WeatherFetcher:
    """Fetches weather data from Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1"
    
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1
    MAX_RETRY_DELAY = 8
    TIMEOUT = 10
    
    def _make_request_with_retry(self, url: str, params: Dict) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic."""
        retry_delay = self.INITIAL_RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.json()
            except (requests.Timeout, requests.ConnectionError, requests.RequestException):
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
                continue
            except Exception:
                continue
        
        return None
    
    def _extract_location_data(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Safely extract location data from API result with validation."""
        try:
            required_fields = ["latitude", "longitude"]
            if not all(field in result for field in required_fields):
                return None
            
            return {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "city": result.get("name", "Unknown"),
                "country": result.get("country", "Unknown"),
                "state": result.get("admin1", "")
            }
        except (KeyError, TypeError):
            return None
    
    def get_coordinates(self, city: str) -> Optional[Dict[str, Any]]:
        """Get latitude and longitude for a city."""
        try:
            params = {
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            data = self._make_request_with_retry(f"{self.GEOCODING_URL}/search", params)
            
            if not data:
                return None
            
            results = data.get("results")
            if not results or len(results) == 0:
                if "," in city:
                    city_name = city.split(",")[0].strip()
                    params["name"] = city_name
                    data = self._make_request_with_retry(f"{self.GEOCODING_URL}/search", params)
                    
                    if data and data.get("results") and len(data["results"]) > 0:
                        return self._extract_location_data(data["results"][0])
                
                return None
            
            return self._extract_location_data(results[0])
        
        except Exception:
            return None
    
    def _validate_forecast_data(self, data: Dict[str, Any]) -> bool:
        """Validate forecast data has required structure."""
        try:
            required_keys = ["daily"]
            if not all(key in data for key in required_keys):
                return False
            
            daily = data["daily"]
            required_daily_keys = ["time", "weather_code", "temperature_2m_max", "temperature_2m_min"]
            if not all(key in daily for key in required_daily_keys):
                return False
            
            lengths = {key: len(daily[key]) for key in required_daily_keys}
            if len(set(lengths.values())) > 1:
                return False
            
            return True
        except (KeyError, TypeError):
            return False
    
    def fetch_forecast(self, city: str) -> Optional[Dict[str, Any]]:
        """Fetch 7-day weather forecast for a city."""
        coords = self.get_coordinates(city)
        if not coords:
            return None
        
        try:
            params = {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "auto"
            }
            
            forecast_data = self._make_request_with_retry(f"{self.BASE_URL}/forecast", params)
            
            if not forecast_data:
                return None
            
            if not self._validate_forecast_data(forecast_data):
                return None
            
            result = {
                "location": coords,
                "forecast": forecast_data,
                "fetched_at": datetime.now().isoformat()
            }
            
            return result
        except Exception:
            return None


def _get_houston_weather():
    """Fetch 7-day weather forecast for Houston, Texas."""
    fetcher = WeatherFetcher()
    forecast = fetcher.fetch_forecast("Houston, Texas")
    
    if forecast:
        return {
            "status": "success",
            "data": {
                "city": forecast["location"]["city"],
                "state": forecast["location"]["state"],
                "latitude": forecast["location"]["latitude"],
                "longitude": forecast["location"]["longitude"],
                "timezone": forecast["forecast"]["timezone"],
                "forecast_summary": {
                    "high_temp_f": max(forecast["forecast"]["daily"]["temperature_2m_max"]),
                    "low_temp_f": min(forecast["forecast"]["daily"]["temperature_2m_min"]),
                    "avg_high_temp_f": sum(forecast["forecast"]["daily"]["temperature_2m_max"]) / len(forecast["forecast"]["daily"]["temperature_2m_max"]),
                    "days": len(forecast["forecast"]["daily"]["time"]),
                    "total_precipitation_inches": sum(forecast["forecast"]["daily"]["precipitation_sum"]),
                    "avg_wind_mph": sum(forecast["forecast"]["daily"]["wind_speed_10m_max"]) / len(forecast["forecast"]["daily"]["wind_speed_10m_max"])
                },
                "fetched_at": forecast["fetched_at"]
            }
        }
    else:
        return {
            "status": "error",
            "message": "Failed to fetch weather data for Houston, Texas"
        }


@app.function(image=image)
def get_houston_weather():
    """Fetch 7-day weather forecast for Houston, Texas."""
    return _get_houston_weather()


@app.function(image=image)
def weather_webhook():
    """HTTP webhook endpoint for Houston weather forecast (callable via Modal SDK)."""
    return _get_houston_weather()
