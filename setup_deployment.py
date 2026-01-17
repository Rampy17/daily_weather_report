#!/usr/bin/env python
"""
Deploy Weather Webhook to Replit for public access.

This script creates the files needed to deploy on Replit:
https://replit.com (free account, instant public URLs)

Steps:
1. Go to https://replit.com
2. Create new Python project
3. Upload these files
4. Run main.py

Your public URL will be: https://<project-name>.<username>.repl.co/weather
"""

import os

REPLIT_DEPLOY_GUIDE = """
# Deploy to Replit (Free, Instant Public URL)

## Quick Setup:
1. Visit https://replit.com
2. Click "Create" → Python
3. Upload these files:
   - webhook_server.py
   - modal_app.py
   - requirements.txt

4. Run: python webhook_server.py

Your Public URL: https://your-project-name.your-username.repl.co/weather

## Alternative: Deploy to Railway (Also Free)

1. Visit https://railway.app
2. Connect GitHub or upload files
3. Deploy with one click
4. Get instant public HTTPS URL

## Alternative: ngrok (Temporary, but instant)

1. Install: brew install ngrok
2. Run: ngrok http 5000
3. Copy the HTTPS URL provided
4. Share it with anyone!

Example output:
    Session Status                online
    Account                       user@example.com
    Version                       3.3.0
    Region                        us (United States)
    Latency                       11ms
    Web Interface                 http://127.0.0.1:4040
    Forwarding                    https://1234-56-789-012.ngrok.io -> http://localhost:5000

Your public link: https://1234-56-789-012.ngrok.io/weather
"""

# Create deployment guide
deployment_file = "/Users/rampyfilli/daily_weather_report/DEPLOYMENT_GUIDE.md"
with open(deployment_file, "w") as f:
    f.write(REPLIT_DEPLOY_GUIDE)

print("✅ Deployment guide created!")
print(f"\nRead: {deployment_file}")
print("\nQuickest option: ngrok")
print("Command: ngrok http 5000")
