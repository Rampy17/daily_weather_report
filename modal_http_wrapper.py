"""Minimal HTTP wrapper to call Modal webhook function.

This creates a public HTTPS endpoint by using Modal's serve capability.
"""

import modal
from typing import Dict, Any

app = modal.App("weather-webhook-http")

# Define the Docker image
image = modal.Image.debian_slim().pip_install(
    "fastapi==0.104.1",
    "uvicorn==0.24.0",
    "requests==2.31.0"
)


@app.function(image=image)
def fetch_weather() -> Dict[str, Any]:
    """Fetch weather from the modal_webhook app."""
    # Call the deployed weather-webhook app
    try:
        stub = modal.App.lookup("weather-webhook")
        weather_fn = stub.lookup_function("weather_webhook")
        return weather_fn.remote()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch: {str(e)}"
        }


# Create FastAPI app for web endpoint
from fastapi import FastAPI

web_app = FastAPI()


@web_app.get("/")
@web_app.get("/weather")
async def weather_endpoint() -> Dict[str, Any]:
    """Public HTTP GET endpoint for Houston weather."""
    return fetch_weather()


@app.function(image=image)
def asgi():
    """ASGI server for FastAPI app."""
    import uvicorn
    uvicorn.run(web_app, host="0.0.0.0", port=8000)
