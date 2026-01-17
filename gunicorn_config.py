"""Gunicorn config for Railway deployment."""
import os

bind = f"0.0.0.0:{os.getenv('PORT', 3000)}"
workers = 1
worker_class = "sync"
timeout = 120
