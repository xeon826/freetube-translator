import requests
import json

url = "http://localhost:5000/translate"
payload = {
    "q": "hello, how are you?",
    "source": "auto",
    "target": "uk",
    "format": "text",
    "alternatives": 3,
    "api_key": ""
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

# Print the JSON response
print(response.json())

