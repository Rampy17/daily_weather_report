"""Stress testing suite for weather API resilience."""

import json
import time
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from weather import WeatherFetcher


class StressTestResults:
    """Track stress test results."""
    
    def __init__(self):
        self.failures = []
        self.successes = []
    
    def add_failure(self, test_name, error):
        self.failures.append({"test": test_name, "error": str(error)})
    
    def add_success(self, test_name):
        self.successes.append(test_name)
    
    def print_report(self):
        print("\n" + "="*60)
        print("STRESS TEST REPORT")
        print("="*60)
        print(f"\n✓ Passed: {len(self.successes)}")
        for test in self.successes:
            print(f"  • {test}")
        
        print(f"\n✗ Failed: {len(self.failures)}")
        for failure in self.failures:
            print(f"  • {failure['test']}")
            print(f"    Error: {failure['error']}")
        
        print("\n" + "="*60 + "\n")
        return len(self.failures)


def test_timeout_error():
    """Test timeout handling."""
    results = StressTestResults()
    fetcher = WeatherFetcher()
    
    with patch('weather.requests.get') as mock_get:
        mock_get.side_effect = TimeoutError("Request timed out")
        try:
            result = fetcher.get_coordinates("Houston, Texas")
            if result is None:
                results.add_success("Timeout handling - returns None gracefully")
            else:
                results.add_failure("Timeout handling", "Did not return None on timeout")
        except Exception as e:
            results.add_failure("Timeout handling", f"Unhandled exception: {e}")
    
    return results


def test_connection_error():
    """Test connection error handling."""
    results = StressTestResults()
    fetcher = WeatherFetcher()
    
    with patch('weather.requests.get') as mock_get:
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        try:
            result = fetcher.get_coordinates("Houston, Texas")
            if result is None:
                results.add_success("Connection error handling - returns None gracefully")
            else:
                results.add_failure("Connection error handling", "Did not return None on error")
        except Exception as e:
            results.add_failure("Connection error handling", f"Unhandled exception: {e}")
    
    return results


def test_invalid_json():
    """Test malformed JSON response."""
    results = StressTestResults()
    fetcher = WeatherFetcher()
    
    with patch('weather.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        try:
            result = fetcher.get_coordinates("Houston, Texas")
            if result is None:
                results.add_success("Invalid JSON handling - returns None gracefully")
            else:
                results.add_failure("Invalid JSON handling", "Did not return None on invalid JSON")
        except Exception as e:
            results.add_failure("Invalid JSON handling", f"Unhandled exception: {e}")
    
    return results


def test_empty_results():
    """Test empty API results."""
    results = StressTestResults()
    fetcher = WeatherFetcher()
    
    with patch('weather.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        try:
            result = fetcher.get_coordinates("InvalidCityXYZ123")
            if result is None:
                results.add_success("Empty results handling - returns None gracefully")
            else:
                results.add_failure("Empty results handling", "Did not return None on empty results")
        except Exception as e:
            results.add_failure("Empty results handling", f"Unhandled exception: {e}")
    
    return results


def test_missing_fields():
    """Test missing fields in API response."""
    results = StressTestResults()
    fetcher = WeatherFetcher()
    
    with patch('weather.requests.get') as mock_get:
        mock_response = MagicMock()
        # Missing required fields
        mock_response.json.return_value = {
            "results": [{"name": "Houston"}]  # Missing latitude/longitude
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        try:
            result = fetcher.get_coordinates("Houston, Texas")
            if result is None:
                results.add_success("Missing fields handling - handles gracefully")
            else:
                # Check if all required fields are present
                if all(k in result for k in ["latitude", "longitude"]):
                    results.add_success("Missing fields handling - provides defaults")
                else:
                    results.add_failure("Missing fields handling", "Missing required fields in response")
        except KeyError as e:
            results.add_failure("Missing fields handling", f"KeyError on missing field: {e}")
        except Exception as e:
            results.add_failure("Missing fields handling", f"Unhandled exception: {e}")
    
    return results


def test_http_errors():
    """Test HTTP error responses."""
    results = StressTestResults()
    fetcher = WeatherFetcher()
    
    with patch('weather.requests.get') as mock_get:
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response
        
        try:
            result = fetcher.get_coordinates("Houston, Texas")
            if result is None:
                results.add_success("HTTP error handling - returns None gracefully")
            else:
                results.add_failure("HTTP error handling", "Did not return None on HTTP error")
        except Exception as e:
            results.add_failure("HTTP error handling", f"Unhandled exception: {e}")
    
    return results


def test_rate_limiting():
    """Test rate limiting scenario."""
    results = StressTestResults()
    fetcher = WeatherFetcher()
    
    with patch('weather.requests.get') as mock_get:
        import requests
        mock_response = MagicMock()
        mock_response.status_code = 429  # Too Many Requests
        mock_response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
        mock_get.return_value = mock_response
        
        try:
            result = fetcher.get_coordinates("Houston, Texas")
            if result is None:
                results.add_success("Rate limiting handling - returns None gracefully")
            else:
                results.add_failure("Rate limiting handling", "Did not handle 429 status")
        except Exception as e:
            results.add_failure("Rate limiting handling", f"Unhandled exception: {e}")
    
    return results


def run_all_stress_tests():
    """Run all stress tests."""
    all_results = StressTestResults()
    
    tests = [
        ("Timeout Error", test_timeout_error),
        ("Connection Error", test_connection_error),
        ("Invalid JSON", test_invalid_json),
        ("Empty Results", test_empty_results),
        ("Missing Fields", test_missing_fields),
        ("HTTP Errors", test_http_errors),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    print("\n" + "="*60)
    print("RUNNING STRESS TESTS")
    print("="*60)
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}...", end=" ")
        try:
            test_result = test_func()
            all_results.successes.extend(test_result.successes)
            all_results.failures.extend(test_result.failures)
            print("✓")
        except Exception as e:
            print(f"✗ {e}")
            all_results.add_failure(test_name, str(e))
    
    return all_results.print_report()


if __name__ == "__main__":
    failed_tests = run_all_stress_tests()
    sys.exit(min(failed_tests, 1))
