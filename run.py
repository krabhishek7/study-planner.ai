#!/usr/bin/env python3
"""
Study Planner.AI - Run Script
This script initializes and runs the Flask application
"""

import os
from app import app, db

def create_app():
    """Initialize the application and database"""
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")
    
    return app

if __name__ == '__main__':
    # Check if required environment variables are set
    required_vars = ['SECRET_KEY', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with the required variables.")
        print("See .env.example for reference.")
        exit(1)
    
    # Initialize and run the app
    application = create_app()
    
    print("🚀 Starting Study Planner.AI...")
    print("📋 Phase 1 MVP Features Available:")
    print("   - User Registration & Login")
    print("   - Subject Management") 
    print("   - Task Creation & Management")
    print("   - AI-Powered Task Decomposition")
    print("   - Calendar View")
    print("\n🌐 Open http://localhost:5001 in your browser")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Run the Flask development server
    application.run(
        debug=True,
        host='0.0.0.0',
        port=5001
    ) 