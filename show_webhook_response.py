"""Show webhook integration with the project."""

import json

# Load the actual forecast data
with open("data/houston,_texas_forecast.json", "r") as f:
    forecast = json.load(f)

# Format it as the webhook would return
response = {
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

print(json.dumps(response, indent=2))
