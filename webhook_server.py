#!/usr/bin/env python
"""Production-ready weather webhook server with resilience and caching.

Usage:
    python webhook_server.py

Environment Variables:
    FLASK_ENV: 'development' or 'production'
    CITY: City to fetch weather for (default: 'Houston, Texas')
    CACHE_TTL_SECONDS: Cache time-to-live in seconds (default: 1800 - 30 minutes)
    LOG_LEVEL: Logging level (default: 'INFO')

Endpoints:
    GET /              - Get weather data
    GET /weather       - Get weather data
    GET /health        - Health check
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from flask import Flask, jsonify
from src.weather import WeatherFetcher

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
CITY = os.getenv('CITY', 'Houston, Texas')
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '1800'))  # 30 minutes default
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

app = Flask(__name__)


class ResponseCache:
    """Simple response caching with TTL."""
    
    def __init__(self, ttl_seconds: int = 1800) -> None:
        """Initialize cache with TTL in seconds."""
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, datetime] = {}
        logger.debug(f"Cache initialized with TTL={ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key not in self.cache:
            return None
        
        if datetime.now() > self.timestamps[key]:
            logger.debug(f"Cache entry '{key}' expired, removing")
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        logger.debug(f"Cache hit for '{key}'")
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set cache value with expiration time."""
        self.cache[key] = value
        self.timestamps[key] = datetime.now() + timedelta(seconds=self.ttl_seconds)
        logger.debug(f"Cache set for '{key}', expires in {self.ttl_seconds}s")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
        logger.debug("Cache cleared")


# Initialize services
weather_fetcher = WeatherFetcher()
response_cache = ResponseCache(ttl_seconds=CACHE_TTL_SECONDS)


def _get_weather(city: str) -> Dict[str, Any]:
    """Get weather forecast with caching and error handling.
    
    Args:
        city: City name to fetch weather for
        
    Returns:
        Response dictionary with status and data
    """
    cache_key = f"forecast_{city}"
    
    # Check cache first
    cached = response_cache.get(cache_key)
    if cached:
        logger.info(f"Returning cached forecast for {city}")
        cached['from_cache'] = True
        return cached
    
    logger.info(f"Fetching fresh forecast for {city}")
    forecast = weather_fetcher.fetch_forecast(city)
    
    if not forecast:
        logger.error(f"Failed to fetch forecast for {city}")
        return {
            "status": "error",
            "message": f"Failed to fetch weather data for {city}",
            "city": city
        }
    
    try:
        response = {
            "status": "success",
            "from_cache": False,
            "data": {
                "city": forecast["location"]["city"],
                "state": forecast["location"]["state"],
                "latitude": forecast["location"]["latitude"],
                "longitude": forecast["location"]["longitude"],
                "timezone": forecast["forecast"].get("timezone", "auto"),
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
        
        # Cache the response
        response_cache.set(cache_key, response)
        logger.debug(f"Forecast cached for {city}")
        return response
        
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error processing forecast data: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Error processing weather data",
            "city": city
        }


@app.route("/", methods=["GET"])
@app.route("/weather", methods=["GET"])
def weather_webhook() -> tuple:
    """Return weather forecast as JSON.
    
    Supports query parameter:
        ?city=<city_name>  - Custom city (default: Houston, Texas)
    """
    try:
        from flask import request
        city = request.args.get('city', CITY)
        
        if not city or not isinstance(city, str) or len(city) > 100:
            logger.warning(f"Invalid city parameter: {repr(city)}")
            return jsonify({
                "status": "error",
                "message": "Invalid city parameter"
            }), 400
        
        result = _get_weather(city)
        
        if result["status"] == "error":
            logger.warning(f"Weather fetch error for {city}")
            return jsonify(result), 503
        
        logger.info(f"Weather endpoint responded successfully for {city}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Unhandled error in weather endpoint: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500


@app.route("/health", methods=["GET"])
def health() -> tuple:
    """Health check endpoint.
    
    Returns:
        JSON with service status
    """
    logger.debug("Health check called")
    return jsonify({
        "status": "ok",
        "service": "weather-webhook",
        "environment": FLASK_ENV,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error: Exception) -> tuple:
    """Handle 404 errors."""
    logger.warning(f"404 error: {error}")
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available_endpoints": ["/", "/weather", "/health"]
    }), 404


@app.errorhandler(500)
def internal_error(error: Exception) -> tuple:
    """Handle 500 errors."""
    logger.error(f"500 error: {error}", exc_info=True)
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🌤️  Weather Webhook Server")
    logger.info("=" * 70)
    logger.info(f"Environment: {FLASK_ENV}")
    logger.info(f"City: {CITY}")
    logger.info(f"Cache TTL: {CACHE_TTL_SECONDS}s")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("")
    logger.info("Available endpoints:")
    logger.info("  • GET /              - Get weather data (or ?city=<name>)")
    logger.info("  • GET /weather       - Get weather data (or ?city=<name>)")
    logger.info("  • GET /health        - Health check")
    logger.info("=" * 70)
    
    # Run with appropriate settings
    debug_mode = FLASK_ENV == 'development'
    app.run(
        debug=debug_mode,
        port=int(os.getenv('PORT', '3000')),
        use_reloader=False
    )
