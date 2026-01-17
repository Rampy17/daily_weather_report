# Deploy to Railway

## Steps:

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Connect your GitHub account
4. Select this repository (daily_weather_report)
5. Railway will auto-detect the Procfile and deploy

**Or deploy via Railway CLI:**

```bash
npm install -g @railway/cli
railway login
railway init
railway deploy
```

Your public URL will be: `https://your-project-name.up.railway.app/weather`

Railway provides:
- ✅ Free tier with public URL
- ✅ Automatic HTTPS
- ✅ No authentication needed
- ✅ Custom domain support
