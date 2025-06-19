"""
Mock AI functionality for when OpenAI API is not available
This provides sample task decomposition for testing purposes
"""

import json
import random

def mock_task_decomposition(task_title, subject_name, description="", difficulty="medium"):
    """
    Generate mock subtasks for testing when OpenAI API is not available
    """
    
    # Sample subtask templates based on common study patterns
    templates = {
        "biology": [
            {"title": "Review cell structure and organelles", "description": "Study diagrams and functions of cellular components", "estimated_time": 45},
            {"title": "Practice cellular processes", "description": "Work through mitosis, meiosis, and metabolic pathways", "estimated_time": 50},
            {"title": "Memorize key terminology", "description": "Create flashcards for important biological terms", "estimated_time": 30},
            {"title": "Complete practice questions", "description": "Answer chapter review questions and quizzes", "estimated_time": 40}
        ],
        "math": [
            {"title": "Review fundamental concepts", "description": "Go through basic principles and definitions", "estimated_time": 40},
            {"title": "Work through example problems", "description": "Solve step-by-step examples from textbook", "estimated_time": 50},
            {"title": "Practice problem sets", "description": "Complete assigned homework problems", "estimated_time": 60},
            {"title": "Review challenging areas", "description": "Focus on topics that need more attention", "estimated_time": 35}
        ],
        "history": [
            {"title": "Read assigned chapters", "description": "Carefully read and take notes on key events", "estimated_time": 45},
            {"title": "Create timeline of events", "description": "Organize important dates and sequences", "estimated_time": 30},
            {"title": "Analyze primary sources", "description": "Review documents and artifacts from the period", "estimated_time": 40},
            {"title": "Write practice essays", "description": "Practice essay questions and arguments", "estimated_time": 50}
        ],
        "default": [
            {"title": "Review core material", "description": "Go through main concepts and principles", "estimated_time": 45},
            {"title": "Practice key skills", "description": "Work on practical applications and exercises", "estimated_time": 50},
            {"title": "Memorize important information", "description": "Focus on facts, formulas, or terminology", "estimated_time": 35},
            {"title": "Test understanding", "description": "Complete practice questions or self-assessment", "estimated_time": 40}
        ]
    }
    
    # Determine subject category
    subject_lower = subject_name.lower()
    if any(word in subject_lower for word in ["bio", "anatomy", "physiology"]):
        category = "biology"
    elif any(word in subject_lower for word in ["math", "calc", "algebra", "geometry", "statistics"]):
        category = "math"
    elif any(word in subject_lower for word in ["history", "social", "political"]):
        category = "history"
    else:
        category = "default"
    
    # Select appropriate templates
    available_templates = templates[category]
    
    # Adjust number of subtasks based on difficulty
    if difficulty == "easy":
        num_subtasks = random.randint(2, 3)
    elif difficulty == "hard":
        num_subtasks = random.randint(4, 5)
    else:  # medium
        num_subtasks = random.randint(3, 4)
    
    # Select random subtasks
    selected_subtasks = random.sample(available_templates, min(num_subtasks, len(available_templates)))
    
    # Customize subtasks based on the specific task
    for subtask in selected_subtasks:
        if description and len(description) > 10:
            # Incorporate specific description elements
            if "chapter" in description.lower():
                subtask["description"] = f"Focus on {description.split('.')[0].lower()}: {subtask['description']}"
        
        # Add task context to title
        if task_title and "exam" in task_title.lower():
            subtask["title"] = f"{subtask['title']} for exam prep"
        elif task_title and "project" in task_title.lower():
            subtask["title"] = f"{subtask['title']} for project"
    
    return {
        "subtasks": selected_subtasks
    }

def get_mock_response_json(task_title, subject_name, description="", difficulty="medium"):
    """
    Get mock response in the same format as OpenAI API
    """
    result = mock_task_decomposition(task_title, subject_name, description, difficulty)
    return json.dumps(result, indent=2) 