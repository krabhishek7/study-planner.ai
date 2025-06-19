# Study Planner.AI - Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your configuration
# - Set a secure SECRET_KEY
# - Add your OpenAI API key from https://platform.openai.com/api-keys
```

### 3. Run the Application
```bash
python run.py
```

The application will be available at: http://localhost:5001

## 📋 Phase 1 MVP Features

✅ **Foundation Features**
- User Registration & Authentication
- Subject Management with Color Coding
- Task Creation & Management
- Calendar View for Due Dates

✅ **AI-Powered Features**
- **Intelligent Task Decomposition**: Break down complex study goals into manageable subtasks
- Uses OpenAI GPT-3.5-turbo for smart academic planning

## 🔧 Configuration Options

### Environment Variables (.env file)
```
SECRET_KEY=your-secure-secret-key
OPENAI_API_KEY=sk-your-openai-api-key
DATABASE_URL=sqlite:///study_planner.db
FLASK_ENV=development
FLASK_DEBUG=True
```

### Database Options
- **Development**: SQLite (default, no setup required)
- **Production**: PostgreSQL (recommended)

## 🎯 How to Use

### 1. Create Account
- Register with username, email, and password
- Login to access your personal dashboard

### 2. Add Subjects
- Create subjects for your courses (e.g., "Biology 101", "Calculus")
- Choose colors to visually organize your subjects
- Add descriptions for context

### 3. Create Tasks
- Add study tasks linked to your subjects
- Set due dates and difficulty levels
- Provide detailed descriptions for better AI decomposition

### 4. AI Task Decomposition
- Click "AI Decompose" on any task
- AI automatically breaks down complex tasks into 30-60 minute study sessions
- View generated subtasks with time estimates

### 5. Track Progress
- Use the calendar view to see upcoming deadlines
- Monitor your subjects and tasks from the dashboard
- Track AI decomposition progress

## 🔮 Coming in Phase 2

- **Adaptive Scheduling**: Smart calendar placement based on priorities
- **Spaced Repetition**: Automatic review session scheduling
- **Performance Tracking**: Learn from your study habits

## 🛠️ Development

### Project Structure
```
smart-study-planner/
├── app.py              # Main Flask application
├── run.py              # Application runner
├── requirements.txt    # Python dependencies
├── .env               # Environment configuration
├── templates/         # HTML templates
├── static/           # CSS, JS, images
└── study_planner.db  # SQLite database (auto-created)
```

### Adding New Features
1. Update database models in `app.py`
2. Create new routes and templates
3. Update the frontend with new functionality
4. Test thoroughly before deployment

## ⚡ Performance Tips

- **AI API Calls**: Task decomposition requires OpenAI API calls
- **Database**: SQLite works fine for development, use PostgreSQL for production
- **Caching**: Consider caching AI responses for similar tasks

## 🔐 Security Notes

- Change the default SECRET_KEY in production
- Use environment variables for sensitive data
- Consider implementing rate limiting for AI endpoints
- Use HTTPS in production

## 📊 Monitoring

The application includes:
- Error handling for AI API failures
- User feedback for all operations
- Loading states for async operations
- Responsive design for mobile devices

---

**Need Help?** Check the application logs or review the Phase 1 roadmap for guidance. 