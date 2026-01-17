#!/usr/bin/env python
"""
Quick deploy guide to get a public URL.

RUN THIS and follow instructions.
"""

print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                    🌤️  GET YOUR PUBLIC WEATHER WEBHOOK URL                    ║
╚════════════════════════════════════════════════════════════════════════════════╝

OPTION 1: REPLIT (Easiest, Instant URL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: https://replit.com
2. Click "Create" → Select "Import from GitHub"
3. Paste: https://github.com/yourusername/daily_weather_report
   (Or upload files manually)
4. Click "Run"
5. You get instant public URL like:
   https://daily-weather-report.username.repl.co/weather

OPTION 2: RAILWAY (Free, Permanent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: https://railway.app
2. Click "New Project"
3. Connect GitHub or upload this folder
4. Railway auto-deploys from Procfile
5. You get public URL like:
   https://daily-weather-report-prod.up.railway.app/weather

OPTION 3: RENDER (Free, Permanent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub or upload files
4. Render deploys automatically
5. You get public URL like:
   https://daily-weather-report.onrender.com/weather

OPTION 4: LOCAL ONLY (No Deploy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your webhook is already running at:
✅ http://localhost:3000/weather

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDED: Use REPLIT (takes 2 minutes)

Files needed for deployment:
  ✓ webhook_server.py (already created)
  ✓ modal_app.py (already created)
  ✓ requirements.txt (already created)
  ✓ Procfile (already created)
  ✓ gunicorn_config.py (already created)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
