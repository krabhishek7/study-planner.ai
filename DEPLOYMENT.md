# Study Planner.AI - Deployment Guide

## 🚀 Quick Fix for Current Error

The `ModuleNotFoundError: No module named 'ics'` error has been resolved by:

1. ✅ Added `ics==0.7` to `requirements.txt`
2. ✅ Added `gunicorn==21.2.0` for production server
3. ✅ Created `Procfile` for deployment platforms
4. ✅ Updated `run.py` to export app correctly

## 📋 Prerequisites

Make sure you have these environment variables set in your deployment platform:

```bash
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
DATABASE_URL=your-database-url-here (for production)
```

## 🌐 Deployment Platforms

### Render.com
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn --bind 0.0.0.0:$PORT run:app`
4. Add environment variables in dashboard
5. Deploy!

### Heroku
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set config vars:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set OPENAI_API_KEY=your-openai-key
   ```
5. Deploy: `git push heroku main`

### Railway
1. Connect GitHub repository
2. Add environment variables
3. Railway will automatically detect and deploy

### Digital Ocean App Platform
1. Connect repository
2. Set environment variables
3. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn --bind 0.0.0.0:$PORT run:app`

## 🔧 Local Development

```bash
# Clone repository
git clone <your-repo-url>
cd smart-calculator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run development server
python run.py
```

## 📦 Required Files

- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Deployment configuration
- ✅ `run.py` - Application entry point
- ✅ `.env.example` - Environment variables template

## 🗄️ Database

- **Development**: SQLite (automatic)
- **Production**: PostgreSQL (recommended)
- **Database URL**: Set `DATABASE_URL` for production

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] Database URL set (if using external DB)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] App properly exported (`run:app`)
- [ ] Debug mode disabled in production

## 🔍 Troubleshooting

### Common Issues:

1. **ModuleNotFoundError**: Check `requirements.txt` has all dependencies
2. **App not found**: Ensure `run.py` exports `app` variable
3. **Database errors**: Check database URL and permissions
4. **Environment variables**: Verify all required vars are set

### Debug Commands:

```bash
# Check installed packages
pip list

# Test app import
python -c "from run import app; print('App imported successfully')"

# Check environment variables
python -c "import os; print(os.getenv('SECRET_KEY', 'Not set'))"
```

## 🎨 Features Included

- ✨ Modern UI with gradient design
- 🤖 AI-powered task decomposition
- 📅 Calendar integration
- 👤 User authentication
- 📚 Subject management
- ✅ Task tracking
- 💡 Motivational coaching

## 📞 Support

If you encounter deployment issues, check:
1. All environment variables are set
2. Requirements.txt includes all dependencies
3. Procfile uses correct command
4. App is properly exported in run.py

Happy deploying! 🚀 