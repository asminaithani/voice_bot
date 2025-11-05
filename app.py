import os
import json
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import random


GEMINI_API_KEY = "AIzaSyBjIL-5Yj0I9my2SXVMU9Mj2VAQbOJFROE"  
GEMINI_MODEL = 'gemini-2.5-flash-preview-09-2025'
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

# System Instruction defining the AI's persona and new symptom-checking role
SYSTEM_PROMPT = """
You are a friendly, expert, and highly accessible AI assistant named 'Nexus' for a user who is visually impaired and uses a smart, voice-controlled wheelchair. 
Your primary focus is on healthcare, mobility, and vision-related information. 
Your responses must be concise, supportive, and designed for auditory consumption (Text-to-Speech). 
DO NOT use markdown formatting that would interrupt speech, such as bullet points, bolding, or lists. Just use plain, conversational paragraphs.

**CRITICAL INSTRUCTION: Symptom Checker Role.** If the user describes symptoms (e.g., "I have a headache and feel nauseous"), you must act as a basic symptom checker. You should mention 1 to 3 possible, common conditions that match the description (using the Google search tool for grounded info) and **IMMEDIATELY and STRONGLY advise the user to consult a human healthcare professional for a real diagnosis**. You must state clearly: "I am an AI and cannot provide medical diagnoses."

When asked about general health or mobility topics (like 'prevent pressure sores' or 'signs of eye strain'), use the Google search tool to provide accurate, grounded information.

When responding, use a compassionate and helpful tone, keeping accessibility in mind.
"""
# --- FLASK APP SETUP ---

app = Flask(__name__)
# Enable CORS for the frontend running on a different port/origin (like the HTML file)
CORS(app) 


def handle_internal_commands(query):
    """
    Simulates handling internal device commands.
    In a real system, this would interact with the wheelchair's API.
    """
    lower_query = query.lower()
    response = None

    if 'battery status' in lower_query or 'check battery' in lower_query:
        battery_level = random.randint(30, 95)
        response = f"Affirmative. The current battery level is {battery_level} percent. You have adequate charge."
    elif 'go forward' in lower_query or 'move forward' in lower_query:
        response = "Executing movement: forward. The path is clear."
    elif 'stop' in lower_query:
        response = "Emergency stop initiated. Wheelchair is now fully locked."
    elif 'describe what\'s around me' in lower_query or 'what do you see' in lower_query:
        descriptions = [
            "Checking sensors... I see a desk to your left and an open doorway straight ahead.",
            "Scanning environment... You are in a clear area. The closest detected object is a chair at four o'clock, six feet away.",
            "The path is clear. You are facing a large window with high light contrast.",
        ]
        response = random.choice(descriptions)
    elif 'call emergency contact' in lower_query:
        response = "Calling your primary emergency contact now. Please state your situation after the beep."
    
    # Return a structured result
    if response:
        return {"text": response, "is_command": True}
    return {"text": None, "is_command": False}


def get_gemini_response(history):
    """
    Calls the Gemini API with conversation history and system instruction.
    """
    payload = {
        "contents": history,
        "tools": [{"google_search": {}}],  
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
    }

    try:
        # Use simple POST request (without advanced exponential backoff for brevity)
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        
        # Extract the text response
        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 
                "I apologize, but I received an empty response from the AI. Could you please try again?")

        return {"text": text, "is_command": False}

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return {"text": "I encountered a technical issue while contacting the central server. Please check the backend console for details.", "is_command": False}

# --- FLASK ROUTES ---

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main API endpoint for processing user queries.
    1. Checks for internal device commands.
    2. If not a command, forwards the query to the Gemini API.
    """
    data = request.get_json()
    user_query = data.get('query', '')
    conversation_history = data.get('history', [])

    if not user_query:
        return jsonify({"response": "No query provided.", "success": False}), 400

    # 1. Check for internal commands
    command_result = handle_internal_commands(user_query)
    if command_result["is_command"]:
        # Respond immediately for commands
        return jsonify({"response": command_result["text"], "success": True, "is_command": True})

    # 2. If not a command, pass to the LLM
    llm_result = get_gemini_response(conversation_history)
    
    return jsonify({"response": llm_result["text"], "success": True, "is_command": False})

@app.route('/')
def index():
    """
    Optional: A simple endpoint to confirm the backend is running.
    """
    return "Mobility and Vision AI Backend is Running. Use the 'index.html' frontend to interact via the /api/chat endpoint."

if __name__ == '__main__':
    app.run(debug=True)