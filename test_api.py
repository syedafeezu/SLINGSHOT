import os, json, re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.environ.get('GEMINI_API_KEY', ''))
model = genai.GenerativeModel('gemini-2.5-flash')

prompt = (
    'You are an expert in-store shopping assistant. '
    'The user wants: "i wanna make pasta". '
    'Return a JSON object with exactly two keys: '
    '"items" (list of objects with "name" and "aisle") and '
    '"cross_sell" (object with "name", "aisle", "reason"). '
    'Respond ONLY with valid JSON. No markdown code fences.'
)

try:
    response = model.generate_content(prompt)
    text = response.text.strip()
    print('RAW:', text[:300])
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    result = json.loads(text)
    print('PARSED OK:', list(result.keys()))
    print('Items:', result.get('items', [])[:2])
except Exception as e:
    print('ERROR:', type(e).__name__, e)
