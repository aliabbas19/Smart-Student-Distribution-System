
import requests
import json

try:
    response = requests.get('http://127.0.0.1:5000/distribute')
    if response.status_code == 200:
        data = response.json()
        print("Status:", data['status'])
        print("Stats:", json.dumps(data['stats'], indent=4, ensure_ascii=False))
        print("Assigned Sample:", len(data['assigned']))
        print("Unassigned Sample:", len(data['unassigned']))
    else:
        print("Error:", response.status_code, response.text)
except Exception as e:
    print("Request failed:", e)
