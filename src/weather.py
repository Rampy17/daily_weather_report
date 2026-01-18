"""Weather data fetching module using Open-Meteo API."""

import json
import logging
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WeatherFetcher:
    """Fetches weather data from Open-Meteo API with resilience and error handling."""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1"
    
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1
    MAX_RETRY_DELAY = 8
    TIMEOUT = 10
    
    def __init__(self, data_dir: str = "data") -> None:
        """Initialize the weather fetcher."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        logger.debug(f"WeatherFetcher initialized with data_dir={data_dir}")
    
    def _calculate_backoff(self, attempt: int) -> int:
        """Calculate exponential backoff delay."""
        delay = self.INITIAL_RETRY_DELAY * (2 ** attempt)
        return min(delay, self.MAX_RETRY_DELAY)
    
    def _handle_retry(self, attempt: int, error_msg: str) -> bool:
        """Log retry attempt and sleep if not final attempt."""
        if attempt < self.MAX_RETRIES - 1:
            delay = self._calculate_backoff(attempt)
            logger.warning(f"{error_msg} Retrying in {delay}s...")
            time.sleep(delay)
            return True
        logger.error(f"{error_msg} Max retries exceeded")
        return False
    
    def _make_request_with_retry(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic.
        
        Differentiates between retryable (5xx, network) and non-retryable (4xx) errors.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                logger.debug(f"Request succeeded on attempt {attempt + 1}")
                return response.json()
                
            except requests.HTTPError as e:
                if 400 <= e.response.status_code < 500:
                    logger.error(f"Client error {e.response.status_code}: {str(e)}")
                    return None
                elif 500 <= e.response.status_code < 600:
                    if not self._handle_retry(attempt, f"Server error {e.response.status_code}:"):
                        return None
                        
            except requests.Timeout:
                if not self._handle_retry(attempt, f"Request timeout ({self.TIMEOUT}s):"):
                    return None
                    
            except requests.ConnectionError:
                if not self._handle_retry(attempt, "Connection error:"):
                    return None
                    
            except json.JSONDecodeError:
                if not self._handle_retry(attempt, "Invalid JSON response:"):
                    return None
                    
            except requests.RequestException as e:
                if not self._handle_retry(attempt, f"Request failed: {str(e)}"):
                    return None
        
        logger.error(f"All {self.MAX_RETRIES} retry attempts exhausted")
        return None
    
    def get_coordinates(self, city: str) -> Optional[Dict[str, Any]]:
        """Get latitude and longitude for a city."""
        if not city or not isinstance(city, str) or len(city) > 100:
            logger.error(f"Invalid city name: {repr(city)}")
            return None
        
        city = city.strip()
        if not city:
            logger.error("City name cannot be empty")
            return None
        
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        data = self._make_request_with_retry(f"{self.GEOCODING_URL}/search", params)
        
        if not data or "results" not in data or not data["results"]:
            if "," in city:
                city_only = city.split(",")[0].strip()
                logger.info(f"Geocoding retry with city-only: {city_only}")
                params["name"] = city_only
                data = self._make_request_with_retry(f"{self.GEOCODING_URL}/search", params)
            
            if not data or "results" not in data or not data["results"]:
                logger.error(f"Geocoding failed for city: {city}")
                return None
        
        result = data["results"][0]
        coords = {
            "city": result.get("name", "Unknown"),
            "state": result.get("admin1", ""),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude")
        }
        logger.debug(f"Geocoding result: {coords}")
        return coords
    
    def _validate_forecast_data(self, forecast_data: Dict[str, Any]) -> bool:
        """Validate forecast data has required structure and consistency."""
        try:
            required_daily_keys = ["time", "temperature_2m_max", "temperature_2m_min", 
                                  "precipitation_sum", "wind_speed_10m_max"]
            
            if "daily" not in forecast_data:
                logger.error("Forecast data missing 'daily' key")
                return False
            
            daily = forecast_data["daily"]
            for key in required_daily_keys:
                if key not in daily:
                    logger.error(f"Forecast data missing daily key: {key}")
                    return False
            
            # Check all daily arrays have same length
            first_len = len(daily[required_daily_keys[0]])
            if not all(len(daily[key]) == first_len for key in required_daily_keys[1:]):
                logger.error("Forecast daily arrays have inconsistent lengths")
                return False
            
            logger.debug(f"Forecast validation passed ({first_len} days)")
            return True
        except (KeyError, TypeError) as e:
            logger.error(f"Forecast validation error: {e}")
            return False
    
    def fetch_forecast(self, city: str) -> Optional[Dict[str, Any]]:
        """Fetch 7-day weather forecast for a city."""
        coords = self.get_coordinates(city)
        if not coords:
            logger.error(f"Could not get coordinates for {city}")
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
                logger.error("Forecast data validation failed")
                return None
            
            result = {
                "location": coords,
                "forecast": forecast_data,
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully fetched forecast for {coords['city']}, {coords['state']}")
            return result
        except Exception as e:
            logger.error(f"Forecast fetch exception: {e}", exc_info=True)
            return None
    
    def save_forecast(self, forecast_data: Dict[str, Any], city: str) -> Optional[str]:
        """Save forecast data to JSON file.
        
        Args:
            forecast_data: Forecast dictionary
            city: City name for filename
            
        Returns:
            Path to saved file or None on error
        """
        if not forecast_data:
            logger.warning("No forecast data to save")
            return None
        
        try:
            filename = f"{city.lower().replace(' ', '_').replace(',', '')}_forecast.json"
            filepath = self.data_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(forecast_data, f, indent=2)
            
            logger.info(f"Forecast saved to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save forecast: {e}")
            return None
            print("No forecast data to save.")
            return None
        
        try:
            filename = self.data_dir / f"{city.lower().replace(' ', '_')}_forecast.json"
            with open(filename, "w") as f:
                json.dump(forecast_data, f, indent=2)
            print(f"Forecast saved to {filename}")
            return str(filename)
        except IOError as e:
            print(f"Error saving forecast: {e}")
            return None
    
    def fetch_and_save(self, city: str) -> Optional[str]:
        """Fetch forecast and save it to a file.
        
        Args:
            city: City name to fetch forecast for.
            
        Returns:
            Path to saved file, or None if operation fails.
        """
        print(f"Fetching 7-day forecast for {city}...")
        forecast = self.fetch_forecast(city)
        if forecast:
            return self.save_forecast(forecast, city)
        return None


if __name__ == "__main__":
    # Example usage
    fetcher = WeatherFetcher()
    
    # Fetch forecast for a city (change "New York" to your desired city)
    city_name = "New York"
    fetcher.fetch_and_save(city_name)
