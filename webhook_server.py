#!/usr/bin/env python
"""Simple webhook server for testing Houston weather forecast locally.

Usage:
    python webhook_server.py

Then visit:
    http://localhost:3000/weather
    http://localhost:3000/
"""

from flask import Flask, jsonify
import requests
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any

app = Flask(__name__)


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
            except (requests.exceptions.Timeout, json.JSONDecodeError, requests.exceptions.RequestException):
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait_time)
                    continue
                return None
    
    def get_coordinates(self, city: str) -> Optional[Dict[str, Any]]:
        """Get coordinates for a city."""
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        data = self._make_request_with_retry(self.GEOCODING_URL + "/search", params)
        
        if not data or "results" not in data or not data["results"]:
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
                "location": coords,
                "forecast": forecast_data,
                "fetched_at": datetime.now().isoformat()
            }
        except Exception:
            return None


def _get_houston_weather() -> Dict[str, Any]:
    """Get Houston weather forecast."""
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


@app.route("/", methods=["GET"])
@app.route("/weather", methods=["GET"])
def weather_webhook():
    """Return Houston weather forecast as JSON."""
    try:
        result = _get_houston_weather()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch weather: {str(e)}"
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "weather-webhook"})


if __name__ == "__main__":
    print("🌤️  Weather Webhook Server")
    print("=" * 60)
    print("Server starting on http://localhost:3000")
    print("\nAvailable endpoints:")
    print("  • http://localhost:3000/          - Get weather data")
    print("  • http://localhost:3000/weather   - Get weather data")
    print("  • http://localhost:3000/health    - Health check")
    print("\nPress Ctrl+C to stop")
    print("=" * 60 + "\n")
    app.run(debug=True, port=3000, use_reloader=False)
