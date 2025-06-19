#!/usr/bin/env python3
"""
Test script for OpenAI API setup
Run this to verify your OpenAI API key is working correctly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_setup():
    """Test if OpenAI API is properly configured"""
    
    print("🔍 Testing OpenAI API Setup...")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("\n💡 To fix this:")
        print("1. Create a .env file in your project directory")
        print("2. Add this line: OPENAI_API_KEY=sk-your-actual-api-key-here")
        print("3. Get your API key from: https://platform.openai.com/api-keys")
        return False
    
    if not api_key.startswith('sk-'):
        print("❌ Invalid OpenAI API key format")
        print("API keys should start with 'sk-'")
        return False
    
    print(f"✅ OpenAI API key found: {api_key[:7]}...{api_key[-4:]}")
    
    # Test API call
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        print("🔄 Testing API connection...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this message."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API Response: {result}")
        
        if "successful" in result.lower():
            print("\n🎉 OpenAI API is working correctly!")
            return True
        else:
            print("⚠️ Unexpected API response")
            return False
            
    except ImportError:
        print("❌ OpenAI library not installed")
        print("Run: pip install openai")
        return False
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        print("\n💡 Common issues:")
        print("- Invalid API key")
        print("- Insufficient credits/quota")
        print("- Network connectivity issues")
        return False

def test_task_decomposition():
    """Test the actual task decomposition functionality"""
    
    print("\n🧪 Testing Task Decomposition...")
    print("=" * 50)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Sample task decomposition prompt
        prompt = """You are an expert academic planner. A student needs to work on the following task:

Task: Study for Biology midterm
Subject: Biology 101
Description: Need to review chapters 4-7 covering cell biology and genetics
Due Date: 2024-07-01
Estimated Difficulty: medium

Break this down into a logical, structured list of subtasks that can each be completed in 30-60 minutes. Consider the complexity and create specific, actionable study topics.

Output the list in JSON format with this structure:
{
  "subtasks": [
    {
      "title": "Specific subtask title",
      "description": "Brief description of what to do",
      "estimated_time": 45
    }
  ]
}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert academic planner who helps students break down large tasks into manageable study sessions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        print(f"✅ Task decomposition response received")
        print(f"📝 Sample output (first 200 chars): {content[:200]}...")
        
        # Try to parse JSON
        import json
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            result = json.loads(json_str)
            print(f"✅ JSON parsing successful - found {len(result.get('subtasks', []))} subtasks")
            return True
        else:
            print("⚠️ Could not find valid JSON in response")
            return False
            
    except Exception as e:
        print(f"❌ Task decomposition test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🤖 Study Planner.AI - AI Feature Test")
    print("=" * 50)
    
    # Test basic setup
    setup_ok = test_openai_setup()
    
    if setup_ok:
        # Test task decomposition
        decomp_ok = test_task_decomposition()
        
        if decomp_ok:
            print("\n🎉 All tests passed! Your AI feature should work correctly.")
            print("💡 If you're still having issues in the web app, check:")
            print("   - Make sure the Flask app is restarted after adding the API key")
            print("   - Check the browser console for JavaScript errors")
            print("   - Look at the Flask server logs for error messages")
        else:
            print("\n❌ Task decomposition test failed")
    else:
        print("\n❌ Basic setup test failed")
    
    print("\n" + "=" * 50) 