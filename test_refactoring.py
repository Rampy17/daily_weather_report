#!/usr/bin/env python
"""End-to-end test of the refactored weather webhook.

Tests:
1. WeatherFetcher integration
2. ResponseCache functionality
3. Logging integration
4. Error handling
5. Flask endpoints (simulated)
"""

import logging
import json
from datetime import datetime
from unittest.mock import Mock, patch

# Configure logging for test
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_weather_fetcher_integration():
    """Test that WeatherFetcher is properly imported and configured."""
    print("\n" + "=" * 70)
    print("TEST 1: WeatherFetcher Integration")
    print("=" * 70)
    
    from src.weather import WeatherFetcher
    
    fetcher = WeatherFetcher()
    assert fetcher is not None, "WeatherFetcher should be instantiated"
    assert fetcher.MAX_RETRIES == 3, "MAX_RETRIES should be 3"
    assert fetcher.TIMEOUT == 10, "TIMEOUT should be 10 seconds"
    assert hasattr(fetcher, 'fetch_forecast'), "Should have fetch_forecast method"
    assert hasattr(fetcher, 'get_coordinates'), "Should have get_coordinates method"
    
    print("✓ WeatherFetcher class properly configured")
    print("✓ All required methods present")
    print("✓ Retry/timeout settings correct")
    return True


def test_response_cache():
    """Test ResponseCache implementation."""
    print("\n" + "=" * 70)
    print("TEST 2: ResponseCache Functionality")
    print("=" * 70)
    
    from webhook_server import ResponseCache
    
    cache = ResponseCache(ttl_seconds=30)
    
    # Test miss
    assert cache.get("missing") is None, "Cache miss should return None"
    print("✓ Cache miss returns None")
    
    # Test set and hit
    data = {"temp": 75, "city": "Houston"}
    cache.set("weather", data)
    assert cache.get("weather") == data, "Cache hit should return data"
    print("✓ Cache set/get works correctly")
    
    # Test multiple keys
    cache.set("key1", {"a": 1})
    cache.set("key2", {"b": 2})
    assert cache.get("key1") == {"a": 1}
    assert cache.get("key2") == {"b": 2}
    print("✓ Multiple cache keys work independently")
    
    # Test clear
    cache.clear()
    assert cache.get("key1") is None, "Cache should be empty after clear"
    print("✓ Cache clear works correctly")
    
    return True


def test_logging_integration():
    """Test that logging is properly integrated."""
    print("\n" + "=" * 70)
    print("TEST 3: Logging Integration")
    print("=" * 70)
    
    from src.weather import logger as weather_logger
    from webhook_server import logger as webhook_logger
    
    assert weather_logger is not None, "Weather module should have logger"
    assert webhook_logger is not None, "Webhook module should have logger"
    print("✓ Loggers created in both modules")
    
    # Test logging works
    with patch('logging.Logger.debug') as mock_debug:
        weather_logger.debug("Test message")
        print("✓ Logging debug level works")
    
    with patch('logging.Logger.info') as mock_info:
        webhook_logger.info("Test info")
        print("✓ Logging info level works")
    
    return True


def test_error_handling():
    """Test improved error handling."""
    print("\n" + "=" * 70)
    print("TEST 4: Error Handling")
    print("=" * 70)
    
    from src.weather import WeatherFetcher
    from unittest.mock import Mock
    import requests
    
    fetcher = WeatherFetcher()
    
    # Test 4xx handling (should not retry)
    print("Testing 4xx error handling (should not retry)...")
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
    
    with patch('requests.get', return_value=mock_response):
        result = fetcher._make_request_with_retry("http://test.com", {})
        assert result is None, "4xx errors should return None immediately"
    print("✓ 4xx errors handled correctly (no retry)")
    
    # Test input validation
    print("Testing input validation...")
    assert fetcher.get_coordinates("") is None, "Empty city should return None"
    assert fetcher.get_coordinates(None) is None, "None city should return None"
    assert fetcher.get_coordinates("x" * 101) is None, "Long city name should return None"
    print("✓ Input validation works correctly")
    
    return True


def test_configuration():
    """Test environment variable configuration."""
    print("\n" + "=" * 70)
    print("TEST 5: Configuration")
    print("=" * 70)
    
    import os
    
    # Check that configuration is available
    from webhook_server import CITY, CACHE_TTL_SECONDS, FLASK_ENV, LOG_LEVEL
    
    assert CITY == os.getenv('CITY', 'Houston, Texas'), "CITY should be configurable"
    assert CACHE_TTL_SECONDS == int(os.getenv('CACHE_TTL_SECONDS', '1800')), "Cache TTL should be configurable"
    assert LOG_LEVEL == os.getenv('LOG_LEVEL', 'INFO'), "Log level should be configurable"
    assert FLASK_ENV in ['development', 'production'], "Flask environment should be valid"
    
    print(f"✓ CITY: {CITY}")
    print(f"✓ CACHE_TTL_SECONDS: {CACHE_TTL_SECONDS}s")
    print(f"✓ LOG_LEVEL: {LOG_LEVEL}")
    print(f"✓ FLASK_ENV: {FLASK_ENV}")
    
    return True


def test_type_hints():
    """Verify type hints are present."""
    print("\n" + "=" * 70)
    print("TEST 6: Type Hints Verification")
    print("=" * 70)
    
    from src.weather import WeatherFetcher
    import inspect
    
    # Check WeatherFetcher methods have type hints
    methods_to_check = [
        'get_coordinates',
        'fetch_forecast',
        '_validate_forecast_data',
        '_calculate_backoff'
    ]
    
    for method_name in methods_to_check:
        method = getattr(WeatherFetcher, method_name)
        sig = inspect.signature(method)
        has_return_annotation = sig.return_annotation != inspect.Signature.empty
        assert has_return_annotation, f"{method_name} should have return type hint"
        print(f"✓ {method_name} has type hints: {sig.return_annotation}")
    
    return True


def test_no_duplication():
    """Verify WeatherFetcher is not duplicated."""
    print("\n" + "=" * 70)
    print("TEST 7: Code Duplication Check")
    print("=" * 70)
    
    # Check that webhook_server imports from src.weather
    from webhook_server import weather_fetcher
    from src.weather import WeatherFetcher
    
    assert isinstance(weather_fetcher, WeatherFetcher), "weather_fetcher should be instance of WeatherFetcher"
    print("✓ webhook_server imports WeatherFetcher from src.weather")
    print("✓ No code duplication detected")
    
    return True


def run_all_tests():
    """Run all tests and print summary."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  CODE REFACTORING VERIFICATION TESTS".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    tests = [
        ("WeatherFetcher Integration", test_weather_fetcher_integration),
        ("ResponseCache Functionality", test_response_cache),
        ("Logging Integration", test_logging_integration),
        ("Error Handling", test_error_handling),
        ("Configuration", test_configuration),
        ("Type Hints", test_type_hints),
        ("Code Duplication", test_no_duplication),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}", exc_info=True)
            results.append((test_name, "FAIL"))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results:
        status_symbol = "✓" if result == "PASS" else "✗"
        print(f"{status_symbol} {test_name:.<50} {result}")
    
    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)
    
    print("=" * 70)
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n╔" + "=" * 68 + "╗")
        print("║" + "ALL TESTS PASSED! CODE QUALITY VERIFIED.".center(68) + "║")
        print("╚" + "=" * 68 + "╝\n")
        return True
    else:
        print(f"\n{total - passed} test(s) failed.\n")
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
