"""Main entry point for the Daily Weather Report application."""

import os
import sys
from dotenv import load_dotenv
from weather import WeatherFetcher


def main():
    """Main application function."""
    load_dotenv()
    
    # Get city from environment or command line argument
    city = os.getenv("WEATHER_CITY", "Houston, Texas")
    
    if len(sys.argv) > 1:
        city = " ".join(sys.argv[1:])
    
    print("Daily Weather Report - Starting...")
    print(f"Fetching weather for: {city}")
    
    # Fetch and save weather forecast
    fetcher = WeatherFetcher(data_dir="data")
    result = fetcher.fetch_and_save(city)
    
    if result:
        print(f"✓ Weather data successfully saved to {result}")
    else:
        print("✗ Failed to fetch weather data")
        sys.exit(1)


if __name__ == "__main__":
    main()
