"""Weather data fetching module using Open-Meteo API."""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class WeatherFetcher:
    """Fetches weather data from Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1"
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1  # seconds
    MAX_RETRY_DELAY = 8  # seconds
    TIMEOUT = 10  # seconds
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the weather fetcher.
        
        Args:
            data_dir: Directory to save weather data files.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def _make_request_with_retry(self, url: str, params: Dict) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response data or None on failure
        """
        retry_delay = self.INITIAL_RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.Timeout:
                print(f"Timeout on attempt {attempt + 1}/{self.MAX_RETRIES}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
                continue
            except (requests.ConnectionError, requests.RequestException) as e:
                print(f"Request error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
                continue
            except json.JSONDecodeError as e:
                print(f"Invalid JSON response: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
                continue
        
        return None
    
    def get_coordinates(self, city: str) -> Optional[Dict[str, Any]]:
        """Get latitude and longitude for a city.
        
        Args:
            city: City name to search for.
            
        Returns:
            Dictionary with latitude, longitude, and city info, or None if not found.
        """
        try:
            params = {
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            data = self._make_request_with_retry(f"{self.GEOCODING_URL}/search", params)
            
            if not data:
                print("Failed to fetch coordinates after all retries")
                return None
            
            results = data.get("results")
            if not results or len(results) == 0:
                # Try with just the first part (before comma)
                if "," in city:
                    city_name = city.split(",")[0].strip()
                    print(f"City not found, retrying with: {city_name}")
                    params["name"] = city_name
                    data = self._make_request_with_retry(f"{self.GEOCODING_URL}/search", params)
                    
                    if data and data.get("results") and len(data["results"]) > 0:
                        return self._extract_location_data(data["results"][0])
                
                print(f"City '{city}' not found in any search attempt")
                return None
            
            return self._extract_location_data(results[0])
        
        except Exception as e:
            print(f"Unexpected error in get_coordinates: {e}")
            return None
    
    def _extract_location_data(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Safely extract location data from API result with validation.
        
        Args:
            result: Raw result from API
            
        Returns:
            Validated location dictionary or None if required fields missing
        """
        try:
            # Validate required fields
            required_fields = ["latitude", "longitude"]
            if not all(field in result for field in required_fields):
                print(f"Warning: Missing required fields in API response")
                return None
            
            return {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "city": result.get("name", "Unknown"),
                "country": result.get("country", "Unknown"),
                "state": result.get("admin1", "")
            }
        except (KeyError, TypeError) as e:
            print(f"Error extracting location data: {e}")
            return None
    
    def fetch_forecast(self, city: str) -> Optional[Dict[str, Any]]:
        """Fetch 7-day weather forecast for a city.
        
        Args:
            city: City name to fetch forecast for.
            
        Returns:
            Dictionary with forecast data, or None if fetch fails.
        """
        # Get coordinates for the city
        coords = self.get_coordinates(city)
        if not coords:
            print(f"Cannot fetch forecast: coordinates for '{city}' not found.")
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
                print("Failed to fetch forecast after all retries")
                return None
            
            # Validate forecast data
            if not self._validate_forecast_data(forecast_data):
                print("Forecast data validation failed")
                return None
            
            # Combine location and forecast data
            result = {
                "location": coords,
                "forecast": forecast_data,
                "fetched_at": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            print(f"Unexpected error in fetch_forecast: {e}")
            return None
    
    def _validate_forecast_data(self, data: Dict[str, Any]) -> bool:
        """Validate forecast data has required structure.
        
        Args:
            data: Forecast data from API
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_keys = ["daily"]
            if not all(key in data for key in required_keys):
                print("Missing required keys in forecast data")
                return False
            
            daily = data["daily"]
            required_daily_keys = ["time", "weather_code", "temperature_2m_max", "temperature_2m_min"]
            if not all(key in daily for key in required_daily_keys):
                print("Missing required daily forecast keys")
                return False
            
            # Check that all arrays have same length
            lengths = {key: len(daily[key]) for key in required_daily_keys}
            if len(set(lengths.values())) > 1:
                print("Forecast arrays have mismatched lengths")
                return False
            
            return True
        except (KeyError, TypeError) as e:
            print(f"Error validating forecast data: {e}")
            return False
    
    def save_forecast(self, forecast_data: Dict[str, Any], city: str) -> Optional[str]:
        """Save forecast data to JSON file.
        
        Args:
            forecast_data: Weather forecast data to save.
            city: City name (used for filename).
            
        Returns:
            Path to saved file, or None if save fails.
        """
        if not forecast_data:
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
