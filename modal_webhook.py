"""Modal Webhook for Daily Weather Report - Houston forecast.

Deploy with: modal deploy modal_webhook.py
Run with: modal run modal_webhook.py::weather_webhook
"""

import modal
import json
import requests
import time
from datetime import datetime
from typing import Optional, Dict, Any

app = modal.App("weather-webhook")

image = modal.Image.debian_slim().pip_install(
    "requests==2.31.0"
)


class WeatherFetcher:
    """Fetches weather data from Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1"
    
    MAX_RETRIES = 3
    TIMEOUT = 10
    
    def _make_request_with_retry(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic."""
        backoff_times = [1, 2, 4, 8]
        
        for attempt, wait_time in enumerate(backoff_times[:self.MAX_RETRIES]):
            try:
                response = requests.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait_time)
                    continue
                return None
            except json.JSONDecodeError:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait_time)
                    continue
                return None
            except requests.exceptions.RequestException:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait_time)
                    continue
                return None
    
    def get_coordinates(self, city: str) -> Optional[Dict[str, Any]]:
        """Get coordinates for a city."""
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        data = self._make_request_with_retry(self.GEOCODING_URL + "/search", params)
        
        if not data or "results" not in data or not data["results"]:
            # Try fallback: remove state from city name
            if "," in city:
                city_only = city.split(",")[0].strip()
                params["name"] = city_only
                data = self._make_request_with_retry(self.GEOCODING_URL + "/search", params)
            
            if not data or "results" not in data or not data["results"]:
                return None
        
        result = data["results"][0]
        return {
            "city": result.get("name", "Unknown"),
            "state": result.get("admin1", ""),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude")
        }
    
    def _validate_forecast_data(self, forecast_data: Dict[str, Any]) -> bool:
        """Validate forecast data structure."""
        try:
            required_daily_keys = ["time", "temperature_2m_max", "temperature_2m_min", 
                                  "precipitation_sum", "wind_speed_10m_max"]
            
            if "daily" not in forecast_data:
                return False
            
            daily = forecast_data["daily"]
            for key in required_daily_keys:
                if key not in daily:
                    return False
            
            lengths = {key: len(daily[key]) for key in required_daily_keys}
            if len(set(lengths.values())) > 1:
                return False
            
            return True
        except (KeyError, TypeError):
            return False
    
    def _extract_location_data(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Safely extract location data with defaults."""
        return {
            "city": location.get("city", "Unknown"),
            "state": location.get("state", ""),
            "latitude": location.get("latitude", 0),
            "longitude": location.get("longitude", 0)
        }
    
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
            
            if not forecast_data or not self._validate_forecast_data(forecast_data):
                return None
            
            return {
                "location": self._extract_location_data(coords),
                "forecast": forecast_data,
                "fetched_at": datetime.now().isoformat()
            }
        except Exception:
            return None


@app.function(image=image)
def get_houston_weather() -> Dict[str, Any]:
    """Fetch Houston weather forecast."""
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
            "message": "Failed to fetch weather data"
        }


@app.function(image=image)
def weather_webhook() -> Dict[str, Any]:
    """Fetch Houston weather forecast.
    
    Access via: modal run modal_webhook.py::weather_webhook
    """
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
            "message": "Failed to fetch weather data"
        }
