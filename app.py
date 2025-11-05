import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import random

# --- GEMINI CONFIG ---
GEMINI_API_KEY = "AIzaSyBjIL-5Yj0I9my2SXVMU9Mj2VAQbOJFROE"  
GEMINI_MODEL = 'gemini-2.5-flash-preview-09-2025'
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are a friendly, expert AI assistant named 'Nexus' for a visually impaired user using a smart wheelchair. 
You focus on healthcare, mobility, and vision-related help. 
Your responses must be clear, natural, and suitable for speech output. 
Avoid bullet points or markdown formatting.

If the user describes symptoms, act as a basic symptom checker — mention 1–3 common possible causes and always say:
"I am an AI and cannot provide medical diagnoses. Please consult a doctor."
"""

# --- FLASK APP ---
app = Flask(__name__)
CORS(app)

# --- INTERNAL COMMAND HANDLER ---
def handle_internal_commands(query):
    lower_query = query.lower()
    response = None

    if 'battery status' in lower_query or 'check battery' in lower_query:
        battery_level = random.randint(30, 95)
        response = f"The current battery level is {battery_level} percent."
    elif 'go forward' in lower_query or 'move forward' in lower_query:
        response = "Moving forward now."
    elif 'stop' in lower_query:
        response = "Stopping immediately."
    elif 'describe what' in lower_query or 'what do you see' in lower_query:
        response = random.choice([
            "I see a desk on your left and an open doorway ahead.",
            "You’re facing a window with sunlight coming through."
        ])
    elif 'call emergency contact' in lower_query:
        response = "Calling your emergency contact. Please explain your situation."

    if response:
        return {"text": response, "is_command": True}
    return {"text": None, "is_command": False}

# --- GEMINI RESPONSE HANDLER ---
def get_gemini_response(history, language="en"):
    # 🌍 MULTILINGUAL UPDATE
    # Add a message to force Gemini to respond in the chosen language
    language_instruction = {
        "role": "user",
        "parts": [{"text": f"Please respond in {language} language for all future replies."}]
    }
    history.insert(0, language_instruction)

    payload = {
        "contents": history,
        "tools": [{"google_search": {}}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        result = response.json()

        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get(
            'text', "Sorry, I didn’t get that. Can you repeat?"
        )
        return {"text": text, "is_command": False}

    except requests.exceptions.RequestException as e:
        print(f"API error: {e}")
        return {"text": "Server error while connecting to AI service.", "is_command": False}

# --- ROUTES ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_query = data.get('query', '')
    conversation_history = data.get('history', [])
    language = data.get('language', 'en')  # 🌍 MULTILINGUAL UPDATE (default: English)

    if not user_query:
        return jsonify({"response": "No query provided.", "success": False}), 400

    command_result = handle_internal_commands(user_query)
    if command_result["is_command"]:
        return jsonify({"response": command_result["text"], "success": True, "is_command": True})

    llm_result = get_gemini_response(conversation_history, language)
    return jsonify({"response": llm_result["text"], "success": True, "is_command": False})

@app.route('/')
def index():
    return "Nexus Multilingual Chatbot Backend is Running."

if __name__ == '__main__':
    app.run(debug=True)
