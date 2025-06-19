from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import openai
import json
from sqlalchemy import or_, and_
from ics import Calendar, Event
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///study_planner.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    calendar_token = db.Column(db.String(255), unique=True)  # For calendar feed access
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subjects = db.relationship('Subject', backref='user', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    progress_entries = db.relationship('UserProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    motivational_messages = db.relationship('MotivationalMessage', backref='user', lazy=True, cascade='all, delete-orphan')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3498db')  # Hex color code
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='subject', lazy=True, cascade='all, delete-orphan')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    estimated_time = db.Column(db.Integer)  # in minutes
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    is_decomposed = db.Column(db.Boolean, default=False)  # Whether AI has broken this down

    # Phase 2 fields
    scheduled_time = db.Column(db.DateTime)  # For adaptive scheduling
    completed_at = db.Column(db.DateTime)    # When the task was completed
    difficulty_rating = db.Column(db.Integer)  # User feedback 1-5
    next_review = db.Column(db.DateTime)     # For spaced repetition
    review_interval = db.Column(db.Integer, default=1)  # Days until next review

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    parent_task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)  # For subtasks
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for subtasks
    subtasks = db.relationship('Task', backref=db.backref('parent_task', remote_side=[id]), lazy=True)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    tasks_completed = db.Column(db.Integer, default=0)
    study_time_minutes = db.Column(db.Integer, default=0)
    stress_level = db.Column(db.Integer)  # 1-5 scale, user reported
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MotivationalMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), nullable=False)  # encouragement, warning, achievement
    shown = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful!')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    recent_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', subjects=subjects, recent_tasks=recent_tasks, now=datetime.utcnow())

@app.route('/subjects')
@login_required
def subjects():
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template('subjects.html', subjects=subjects)

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    name = request.form['name']
    description = request.form.get('description', '')
    color = request.form.get('color', '#3498db')
    
    subject = Subject(
        name=name,
        description=description,
        color=color,
        user_id=current_user.id
    )
    
    db.session.add(subject)
    db.session.commit()
    
    flash('Subject added successfully!')
    return redirect(url_for('subjects'))

@app.route('/tasks')
@login_required
def tasks():
    tasks = Task.query.filter_by(user_id=current_user.id, parent_task_id=None).all()  # Only main tasks
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', tasks=tasks, subjects=subjects, now=datetime.utcnow())

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    title = request.form['title']
    description = request.form.get('description', '')
    subject_id = request.form['subject_id']
    due_date_str = request.form.get('due_date')
    difficulty = request.form.get('difficulty', 'medium')
    
    due_date = None
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    
    task = Task(
        title=title,
        description=description,
        subject_id=subject_id,
        due_date=due_date,
        difficulty=difficulty,
        user_id=current_user.id
    )
    
    db.session.add(task)
    db.session.commit()
    
    flash('Task added successfully!')
    return redirect(url_for('tasks'))

# AI-Powered Task Decomposition Route
@app.route('/decompose_task/<int:task_id>', methods=['POST'])
@login_required
def decompose_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Ensure user owns this task
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if task.is_decomposed:
        return jsonify({'error': 'Task already decomposed'}), 400
    
    try:
        subject = Subject.query.get(task.subject_id)
        
        # Check if OpenAI API key is set and working
        use_mock = False
        if not openai.api_key:
            print("No OpenAI API key found, using mock AI")
            use_mock = True
        
        if not use_mock:
            try:
                # Try to use OpenAI API
                prompt = f"""You are an expert academic planner. A student needs to work on the following task:

Task: {task.title}
Subject: {subject.name}
Description: {task.description or 'No additional details provided'}
Due Date: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not specified'}
Estimated Difficulty: {task.difficulty}

Break this down into a logical, structured list of subtasks that can each be completed in 30-60 minutes. Consider the complexity and create specific, actionable study topics.

Output the list in JSON format with this structure:
{{
  "subtasks": [
    {{
      "title": "Specific subtask title",
      "description": "Brief description of what to do",
      "estimated_time": 45
    }}
  ]
}}"""

                # Updated to use the new OpenAI client format
                from openai import OpenAI
                client = OpenAI(api_key=openai.api_key)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert academic planner who helps students break down large tasks into manageable study sessions."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Parse the response
                content = response.choices[0].message.content
                
                # Extract JSON from the response
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                
                result = json.loads(json_str)
                
            except Exception as openai_error:
                print(f"OpenAI API failed: {str(openai_error)}")
                print("Falling back to mock AI")
                use_mock = True
        
        if use_mock:
            # Use mock AI functionality
            from mock_ai import mock_task_decomposition
            result = mock_task_decomposition(
                task.title, 
                subject.name, 
                task.description or '', 
                task.difficulty
            )
        
        # Create subtasks in database
        for subtask_data in result['subtasks']:
            subtask = Task(
                title=subtask_data['title'],
                description=subtask_data['description'],
                estimated_time=subtask_data['estimated_time'],
                subject_id=task.subject_id,
                user_id=current_user.id,
                parent_task_id=task.id,
                difficulty=task.difficulty,
                due_date=task.due_date
            )
            db.session.add(subtask)
        
        # Mark original task as decomposed
        task.is_decomposed = True
        db.session.commit()
        
        return jsonify({'success': True, 'subtasks': result['subtasks']})
        
    except Exception as e:
        print(f"AI Decomposition Error: {str(e)}")  # Debug log
        return jsonify({'error': f'Failed to decompose task: {str(e)}'}), 500

@app.route('/calendar')
@login_required
def calendar():
    tasks = Task.query.filter_by(user_id=current_user.id).filter(Task.due_date.isnot(None)).all()
    return render_template('calendar.html', tasks=tasks, now=datetime.utcnow())

@app.route('/get_subtasks/<int:task_id>')
@login_required
def get_subtasks(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Ensure user owns this task
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    subtasks = Task.query.filter_by(parent_task_id=task_id).all()
    
    subtasks_data = []
    for subtask in subtasks:
        subtasks_data.append({
            'id': subtask.id,
            'title': subtask.title,
            'description': subtask.description,
            'estimated_time': subtask.estimated_time
        })
    
    return jsonify({'success': True, 'subtasks': subtasks_data})

@app.route('/edit_subject/<int:subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    # Ensure user owns this subject
    if subject.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('subjects'))
    
    subject.name = request.form['name']
    subject.description = request.form.get('description', '')
    subject.color = request.form.get('color', '#3498db')
    
    db.session.commit()
    flash('Subject updated successfully!')
    return redirect(url_for('subjects'))

# --- Spaced Repetition Helper ---
def get_next_review_date(last_review, interval):
    """Return the next review date using a simple spaced repetition algorithm."""
    return last_review + timedelta(days=interval)

@app.route('/auto_schedule_task/<int:task_id>', methods=['POST'])
@login_required
def auto_schedule_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    # Find the earliest available slot before the due date
    all_tasks = Task.query.filter_by(user_id=current_user.id).filter(Task.id != task.id).all()
    busy_times = [(t.scheduled_time, t.estimated_time or 60) for t in all_tasks if t.scheduled_time]
    now = datetime.now()
    slot = now
    while True:
        overlap = False
        for st, dur in busy_times:
            if st and abs((st - slot).total_seconds()) < (dur * 60):
                overlap = True
                break
        if not overlap:
            break
        slot += timedelta(minutes=30)
        if task.due_date and slot > task.due_date:
            return jsonify({'success': False, 'error': 'No available slot before due date'})
    task.scheduled_time = slot
    if not task.due_date or task.due_date < slot:
        task.due_date = slot + timedelta(minutes=task.estimated_time or 60)
    db.session.commit()
    return jsonify({'success': True, 'scheduled_time': task.scheduled_time.strftime('%Y-%m-%d %H:%M')})

@app.route('/review_task/<int:task_id>', methods=['POST'])
@login_required
def review_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    now = datetime.now()
    # Simple spaced repetition: double interval each time, max 30 days
    task.next_review = get_next_review_date(now, task.review_interval or 1)
    task.review_interval = min((task.review_interval or 1) * 2, 30)
    db.session.commit()
    return jsonify({'success': True, 'next_review': task.next_review.strftime('%Y-%m-%d')})

@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    rating = request.json.get('difficulty_rating')
    now = datetime.now()
    task.status = 'completed'
    task.completed_at = now
    if rating:
        task.difficulty_rating = int(rating)
    db.session.commit()
    return jsonify({'success': True, 'completed_at': now.strftime('%Y-%m-%d')})

@app.route('/user_stats')
@login_required
def user_stats():
    # Tasks completed
    completed = Task.query.filter_by(user_id=current_user.id, status='completed').all()
    tasks_completed = len(completed)
    # Average difficulty (from difficulty_rating)
    ratings = [t.difficulty_rating for t in completed if t.difficulty_rating]
    avg_difficulty = round(sum(ratings)/len(ratings), 2) if ratings else None
    # Review streak: count consecutive days with at least one review
    today = datetime.utcnow().date()
    review_dates = sorted({(t.completed_at or t.created_at).date() for t in completed if t.completed_at})
    streak = 0
    for days_ago in range(len(review_dates)):
        if today - timedelta(days=days_ago) in review_dates:
            streak += 1
        else:
            break
    return jsonify({
        'success': True,
        'tasks_completed': tasks_completed,
        'avg_difficulty': avg_difficulty,
        'review_streak': streak
    })

# Motivational Coach Functions
def detect_burnout_risk(user_id):
    """Detect if user is at risk of burnout based on recent activity patterns"""
    recent_progress = UserProgress.query.filter_by(user_id=user_id)\
        .filter(UserProgress.date >= datetime.utcnow().date() - timedelta(days=7))\
        .all()
    
    if len(recent_progress) >= 5:
        avg_stress = sum(p.stress_level for p in recent_progress if p.stress_level) / len([p for p in recent_progress if p.stress_level])
        if avg_stress >= 4:
            return True
    return False

def generate_motivational_message(user_id):
    """Generate personalized motivational messages based on user progress"""
    user = User.query.get(user_id)
    completed_tasks = Task.query.filter_by(user_id=user_id, status='completed').count()
    recent_completions = Task.query.filter_by(user_id=user_id, status='completed')\
        .filter(Task.completed_at >= datetime.utcnow() - timedelta(days=7)).count()
    
    messages = []
    
    # Achievement messages
    if completed_tasks >= 10 and completed_tasks % 10 == 0:
        messages.append({
            'message': f'🎉 Amazing! You\'ve completed {completed_tasks} tasks! You\'re building great study habits!',
            'type': 'achievement'
        })
    
    # Encouragement for consistent work
    if recent_completions >= 5:
        messages.append({
            'message': '🔥 You\'re on fire this week! Keep up the fantastic momentum!',
            'type': 'encouragement'
        })
    
    # Gentle nudge for inactive users
    if recent_completions == 0:
        messages.append({
            'message': '📚 Ready to tackle some tasks today? Small steps lead to big achievements!',
            'type': 'encouragement'
        })
    
    # Burnout warning
    if detect_burnout_risk(user_id):
        messages.append({
            'message': '🌱 Remember to take breaks! Your well-being is as important as your studies.',
            'type': 'warning'
        })
    
    return messages

def create_motivational_messages(user_id):
    """Create and store new motivational messages for the user"""
    messages = generate_motivational_message(user_id)
    for msg_data in messages:
        # Check if similar message already exists and hasn't been shown
        existing = MotivationalMessage.query.filter_by(
            user_id=user_id, 
            message_type=msg_data['type'],
            shown=False
        ).first()
        
        if not existing:
            message = MotivationalMessage(
                user_id=user_id,
                message=msg_data['message'],
                message_type=msg_data['type']
            )
            db.session.add(message)
    
    db.session.commit()

@app.route('/motivational_messages')
@login_required
def get_motivational_messages():
    # Create new messages based on current progress
    create_motivational_messages(current_user.id)
    
    # Get unshown messages
    messages = MotivationalMessage.query.filter_by(
        user_id=current_user.id, 
        shown=False
    ).order_by(MotivationalMessage.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'messages': [{
            'id': msg.id,
            'message': msg.message,
            'type': msg.message_type,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M')
        } for msg in messages]
    })

@app.route('/mark_message_shown/<int:message_id>', methods=['POST'])
@login_required
def mark_message_shown(message_id):
    message = MotivationalMessage.query.get_or_404(message_id)
    if message.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    message.shown = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/record_daily_progress', methods=['POST'])
@login_required
def record_daily_progress():
    data = request.json
    today = datetime.utcnow().date()
    
    # Check if progress already recorded for today
    existing = UserProgress.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if existing:
        # Update existing entry
        existing.tasks_completed = data.get('tasks_completed', existing.tasks_completed)
        existing.study_time_minutes = data.get('study_time_minutes', existing.study_time_minutes)
        existing.stress_level = data.get('stress_level', existing.stress_level)
    else:
        # Create new entry
        progress = UserProgress(
            user_id=current_user.id,
            date=today,
            tasks_completed=data.get('tasks_completed', 0),
            study_time_minutes=data.get('study_time_minutes', 0),
            stress_level=data.get('stress_level')
        )
        db.session.add(progress)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/get_progress_chart')
@login_required
def get_progress_chart():
    # Get last 30 days of progress
    start_date = datetime.utcnow().date() - timedelta(days=30)
    progress_data = UserProgress.query.filter_by(user_id=current_user.id)\
        .filter(UserProgress.date >= start_date)\
        .order_by(UserProgress.date).all()
    
    chart_data = {
        'dates': [p.date.strftime('%Y-%m-%d') for p in progress_data],
        'tasks_completed': [p.tasks_completed for p in progress_data],
        'study_time': [p.study_time_minutes for p in progress_data],
        'stress_levels': [p.stress_level for p in progress_data if p.stress_level]
    }
    
    return jsonify({'success': True, 'data': chart_data})

# Resource Recommendation System
def generate_resource_recommendations(task_title, subject_name, description=""):
    """Generate educational resource recommendations for a task"""
    try:
        # Use OpenAI to generate search terms and resource suggestions
        use_mock = False
        if not openai.api_key:
            use_mock = True
        
        if not use_mock:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai.api_key)
                
                prompt = f"""You are an educational resource curator. Based on this study task, suggest 3-5 specific search terms for finding helpful educational content.

Task: {task_title}
Subject: {subject_name}
Description: {description}

Return JSON with this structure:
{{
  "search_terms": ["term1", "term2", "term3"],
  "video_suggestions": ["video title suggestion 1", "video title suggestion 2"],
  "article_topics": ["topic 1", "topic 2"],
  "practice_suggestions": ["practice exercise idea 1", "practice exercise idea 2"]
}}"""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert educational resource curator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                
                content = response.choices[0].message.content
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                
                return json.loads(json_str)
                
            except Exception as e:
                print(f"OpenAI API failed for resources: {str(e)}")
                use_mock = True
        
        if use_mock:
            # Mock resource suggestions
            return {
                "search_terms": [f"{subject_name} basics", f"{task_title} tutorial", f"{subject_name} examples"],
                "video_suggestions": [f"Introduction to {subject_name}", f"{task_title} explained"],
                "article_topics": [f"{subject_name} fundamentals", f"{task_title} guide"],
                "practice_suggestions": [f"{subject_name} practice problems", f"{task_title} exercises"]
            }
    
    except Exception as e:
        print(f"Resource recommendation error: {str(e)}")
        return {
            "search_terms": [subject_name, task_title],
            "video_suggestions": [f"Learn {subject_name}"],
            "article_topics": [f"{subject_name} study guide"],
            "practice_suggestions": [f"{subject_name} practice"]
        }

@app.route('/get_resources/<int:task_id>')
@login_required
def get_task_resources(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    resources = generate_resource_recommendations(
        task.title, 
        task.subject.name, 
        task.description or ""
    )
    
    # Generate YouTube search URLs
    youtube_links = []
    for term in resources.get('search_terms', [])[:3]:
        search_url = f"https://www.youtube.com/results?search_query={term.replace(' ', '+')}"
        youtube_links.append({
            'term': term,
            'url': search_url
        })
    
    # Generate Google Scholar search URLs for articles
    scholar_links = []
    for topic in resources.get('article_topics', [])[:3]:
        scholar_url = f"https://scholar.google.com/scholar?q={topic.replace(' ', '+')}"
        scholar_links.append({
            'topic': topic,
            'url': scholar_url
        })
    
    return jsonify({
        'success': True,
        'resources': {
            'youtube_searches': youtube_links,
            'scholar_searches': scholar_links,
            'video_suggestions': resources.get('video_suggestions', []),
            'practice_suggestions': resources.get('practice_suggestions', [])
        }
    })

@app.route('/study_resources')
@login_required
def study_resources():
    """Dedicated page for study resources and recommendations"""
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    recent_tasks = Task.query.filter_by(user_id=current_user.id)\
        .order_by(Task.created_at.desc()).limit(10).all()
    
    return render_template('resources.html', subjects=subjects, recent_tasks=recent_tasks)

@app.route('/sync_settings')
@login_required
def sync_settings():
    """Display calendar sync settings page"""
    return render_template('sync_settings.html')

# Calendar Integration Functions
@app.route('/export_calendar/<format>')
@login_required
def export_calendar(format):
    """Export user's tasks and schedule to various calendar formats"""
    if format not in ['ical', 'google']:
        return jsonify({'success': False, 'error': 'Invalid format'}), 400
    
    try:
        # Get all tasks with due dates or scheduled times
        tasks = Task.query.filter_by(user_id=current_user.id)\
            .filter(db.or_(Task.due_date.isnot(None), Task.scheduled_time.isnot(None)))\
            .all()
        
        if format == 'ical':
            # Create iCal calendar
            cal = Calendar()
            
            for task in tasks:
                event = Event()
                event.name = f"{task.subject.name}: {task.title}"
                event.description = task.description or ""
                
                # Use due date or scheduled time
                if task.scheduled_time:
                    event.begin = task.scheduled_time
                    event.end = task.scheduled_time + timedelta(hours=1)  # Default 1 hour duration
                elif task.due_date:
                    event.begin = task.due_date
                    event.make_all_day()
                
                event.uid = f"task-{task.id}-{uuid.uuid4()}"
                event.categories = [task.subject.name]
                
                # Add status
                if task.status == 'completed':
                    event.status = 'CONFIRMED'
                    event.description += f"\n✅ Completed"
                elif task.status == 'in_progress':
                    event.description += f"\n🔄 In Progress"
                
                cal.events.add(event)
            
            # Return iCal file
            response = make_response(str(cal))
            response.headers['Content-Type'] = 'text/calendar'
            response.headers['Content-Disposition'] = f'attachment; filename=study_schedule_{current_user.username}.ics'
            return response
        
        elif format == 'google':
            # Generate Google Calendar import URL
            google_urls = []
            for task in tasks:
                if task.due_date or task.scheduled_time:
                    title = f"{task.subject.name}: {task.title}"
                    description = task.description or ""
                    
                    if task.scheduled_time:
                        start_time = task.scheduled_time.strftime('%Y%m%dT%H%M%S')
                        end_time = (task.scheduled_time + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')
                    else:
                        start_time = task.due_date.strftime('%Y%m%d')
                        end_time = task.due_date.strftime('%Y%m%d')
                    
                    google_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={start_time}/{end_time}&details={description}"
                    google_urls.append({
                        'task': task.title,
                        'url': google_url
                    })
            
            return jsonify({'success': True, 'urls': google_urls})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate_calendar_feed')
@login_required
def generate_calendar_feed():
    """Generate a unique URL for calendar feed subscription"""
    # Create or get user's calendar feed token
    if not current_user.calendar_token:
        import secrets
        current_user.calendar_token = secrets.token_urlsafe(32)
        db.session.commit()
    
    feed_url = url_for('calendar_feed', token=current_user.calendar_token, _external=True)
    
    return jsonify({
        'success': True,
        'feed_url': feed_url,
        'instructions': {
            'google': f'In Google Calendar, click "+" next to "Other calendars" → "From URL" → paste: {feed_url}',
            'outlook': f'In Outlook, go to Calendar → "Add calendar" → "Subscribe from web" → paste: {feed_url}',
            'apple': f'In Apple Calendar, go to File → "New Calendar Subscription" → paste: {feed_url}'
        }
    })

@app.route('/calendar_feed/<token>')
def calendar_feed(token):
    """Public calendar feed for external calendar apps"""
    # Find user by calendar token
    user = User.query.filter_by(calendar_token=token).first()
    if not user:
        return "Invalid calendar feed", 404
    
    # Get user's tasks
    tasks = Task.query.filter_by(user_id=user.id)\
        .filter(db.or_(Task.due_date.isnot(None), Task.scheduled_time.isnot(None)))\
        .all()
    
    # Create iCal calendar
    cal = Calendar()
    cal.name = f"{user.username}'s Study Schedule"
    
    for task in tasks:
        event = Event()
        event.name = f"{task.subject.name}: {task.title}"
        event.description = task.description or ""
        
        if task.scheduled_time:
            event.begin = task.scheduled_time
            event.end = task.scheduled_time + timedelta(hours=1)
        elif task.due_date:
            event.begin = task.due_date
            event.make_all_day()
        
        event.uid = f"task-{task.id}-{user.id}"
        event.categories = [task.subject.name]
        
        if task.status == 'completed':
            event.status = 'CONFIRMED'
            event.description += f"\n✅ Completed on {task.completed_at.strftime('%Y-%m-%d') if task.completed_at else 'N/A'}"
        
        cal.events.add(event)
    
    response = make_response(str(cal))
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache'
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 