#!/usr/bin/env python
"""Simple webhook server for testing Houston weather forecast locally.

Usage:
    python webhook_server.py

Then visit:
    http://localhost:5000/weather
    http://localhost:5000/
"""

from flask import Flask, jsonify
from modal_app import _get_houston_weather

app = Flask(__name__)


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
