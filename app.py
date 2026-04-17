import os
import json
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
# Using gemini-1.5-flash as it's the standard for general text tasks now
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/shopping-list', methods=['POST'])
def generate_shopping_list():
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
        
    query = data['query']
    
    prompt = f"""
    You are an expert in-store shopping assistant for a supermarket/grocery store.
    The user wants: "{query}"
    
    Return a JSON object with two keys:
    1. "items": A list of required grocery items to fulfill this request. Each item should be an object with a "name" and a simulated "aisle" (e.g., "Aisle 4", "Produce", "Dairy").
    2. "cross_sell": One highly relevant complementary cross-sell item that goes well with the user's request. It should be an object with "name", "aisle", and a short "reason" why it's a good pairing.
    
    Respond ONLY with valid JSON. Do not include any markdown formatting like ```json or ```.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up potential markdown formatting from Gemini
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        result = json.loads(response_text)
        return jsonify(result)
        
    except json.JSONDecodeError:
        print(f"JSON Parsing Error. Raw response: {response_text}")
        return jsonify({'error': 'Failed to parse AI response. Please try again.'}), 500
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
