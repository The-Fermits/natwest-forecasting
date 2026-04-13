import os
import httpx
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

response = httpx.get(url)
models = response.json().get("models", [])

print(f"Total models found: {len(models)}")
for m in models:
    name = m['name'].replace("models/", "")
    # Skip non-generative models
    if "generateContent" not in m.get("supportedGenerationMethods", []):
        continue
    
    # Test this model
    test_url = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent?key={api_key}"
    try:
        r = httpx.post(test_url, json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=10.0)
        print(f"Model: {name} | Status: {r.status_code}")
        if r.status_code == 200:
            print(f"!!! SUCCESS !!! Use: {name}")
            # Try once more to see if it's stable
            r2 = httpx.post(test_url, json={"contents": [{"parts": [{"text": "hello"}]}]}, timeout=10.0)
            print(f"Stability check: {r2.status_code}")
    except Exception as e:
        print(f"Model: {name} | Network Error: {e}")

