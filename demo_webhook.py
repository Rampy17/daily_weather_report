#!/usr/bin/env python3
"""Demonstrate how the Modal webhook integrates with the Houston weather project."""

import json
from datetime import datetime

# Import the modal app directly
from modal_app import get_houston_weather, weather_webhook


def demo_modal_webhook():
    """Demo: Call the Modal webhook function."""
    
    print("=" * 80)
    print("MODAL WEBHOOK DEMONSTRATION")
    print("=" * 80)
    print()
    
    print("1. Calling the 'weather_webhook' function from modal_app...")
    print("   (This would run on Modal servers in production)")
    print()
    
    try:
        # Call the function directly (in production, this runs on Modal servers)
        print("2. Executing weather_webhook()...")
        result = weather_webhook.remote()
        
        print("   ✓ Function executed successfully!")
        print()
        print("-" * 80)
        print("WEATHER DATA RESPONSE:")
        print("-" * 80)
        
        if result.get("status") == "success":
            data = result["data"]
            summary = data["forecast_summary"]
            
            print(f"\n📍 Location: {data['city']}, {data['state']}")
            print(f"   Coordinates: {data['latitude']}°N, {data['longitude']}°W")
            print(f"   Timezone: {data['timezone']}")
            print()
            
            print("📊 7-Day Forecast Summary:")
            print(f"   High Temperature:  {summary['high_temp_f']}°F")
            print(f"   Low Temperature:   {summary['low_temp_f']}°F")
            print(f"   Avg Temperature:   {summary['avg_high_temp_f']:.1f}°F")
            print(f"   Total Precip:      {summary['total_precipitation_inches']:.2f} inches")
            print(f"   Avg Wind Speed:    {summary['avg_wind_mph']:.1f} mph")
            print(f"   Days Forecast:     {summary['days']} days")
            print()
            
            print(f"⏰ Data fetched: {data['fetched_at']}")
            print()
            
            print("-" * 80)
            print("FULL JSON RESPONSE:")
            print("-" * 80)
            print(json.dumps(result, indent=2))
            
            print()
            print("=" * 80)
            print("✓ SUCCESS! Modal webhook is working perfectly!")
            print("=" * 80)
            
        else:
            print(f"Error: {result.get('message')}")
            
    except Exception as e:
        print(f"✗ Error calling webhook: {e}")
        import traceback
        traceback.print_exc()


def demo_integration():
    """Show how this integrates with the project."""
    
    print()
    print("=" * 80)
    print("HOW THE MODAL WEBHOOK INTEGRATES WITH YOUR PROJECT")
    print("=" * 80)
    print()
    
    print("PROJECT ARCHITECTURE:")
    print()
    print("  1. API Layer:")
    print("     • modal_app.py - Defines weather_webhook() function")
    print("     • Deployed on Modal's serverless infrastructure")
    print()
    
    print("  2. Business Logic Layer:")
    print("     • src/weather.py - WeatherFetcher class")
    print("       - Resilient API calls with retry logic")
    print("       - Data validation")
    print("       - Error handling")
    print()
    
    print("  3. Data & Reports:")
    print("     • src/pdf_generator.py - Creates professional PDFs")
    print("     • data/ - Stores JSON forecasts & PDF reports")
    print()
    
    print("USAGE SCENARIOS:")
    print()
    print("  Scenario A: Local CLI (Recommended for testing)")
    print("  └─ python src/main.py")
    print("     └─ Creates: data/houston_texas_forecast.json")
    print("     └─ Creates: data/houston_forecast_report.pdf")
    print()
    
    print("  Scenario B: Modal Webhook (Production/Cloud)")
    print("  └─ Deploy: modal deploy modal_app.py")
    print("  └─ Call via SDK:")
    print("     import modal")
    print("     app = modal.App.lookup('daily-weather-report')")
    print("     webhook = app.function('weather_webhook')")
    print("     result = webhook.remote()  # Runs on Modal servers")
    print()
    
    print("  Scenario C: Browser/HTTP (Via Modal Dashboard)")
    print("  └─ https://modal.com/apps/amankonahbright/main/deployed/daily-weather-report")
    print("  └─ Click 'weather_webhook' → 'Run' → See JSON output")
    print()


if __name__ == "__main__":
    demo_modal_webhook()
    demo_integration()
