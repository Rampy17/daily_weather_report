#!/usr/bin/env python3
"""Test the deployed Modal webhook."""

import requests
import json
import sys

def test_webhook():
    """Test the Modal webhook endpoint."""
    url = "https://amankonahbright--daily-weather-report-weather-webhook.modal.run"
    
    print("=" * 70)
    print("MODAL WEBHOOK TEST")
    print("=" * 70)
    print(f"\nWebhook URL: {url}\n")
    
    try:
        print("Sending request...")
        response = requests.get(url, timeout=30)
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ SUCCESS! Webhook is live and responding.\n")
            print("Response:")
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return 1
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_webhook())
