#!/usr/bin/env python
"""Local HTTP server for testing the weather webhook.

Run with: python local_server.py
Then visit: http://localhost:5000/
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from modal_app import _get_houston_weather


class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to the weather endpoint."""
        if self.path == "/" or self.path == "/weather":
            # Get the weather data
            result = _get_houston_weather()
            
            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": "Endpoint not found. Use GET /weather or GET /"
            }).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        print(f"[{self.client_address[0]}] {format % args}")


if __name__ == "__main__":
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, WeatherHandler)
    print("🌤️  Local Weather Webhook Server")
    print("=" * 50)
    print("Starting server on http://localhost:8080")
    print("\nAccess endpoints:")
    print("  • http://localhost:8080/          - Get weather data")
    print("  • http://localhost:8080/weather   - Get weather data")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    httpd.serve_forever()
