
import requests
import json
import os

# Configuration
url = 'http://127.0.0.1:5000/distribute'
file_path = os.path.join('data', 'input data.xlsx')
output_path = 'output_from_upload.xlsx'

# Optional: Manual Settings (matches what Frontend would send)
# If you want AUTO mode, set capacities to None or remove it.
capacities = {
    "الامن السيبراني": 45,
    "تكنولوجيا المعلومات": 45,
    "علوم الحاسوب": 45
}
quotas = {
    "عام": 0.60,
    "ذوي الشهداء": 0.10,
    "موازي": 0.30
}

# Prepare Payload
payload = {
    'capacities': json.dumps(capacities),
    'quotas': json.dumps(quotas)
}

print(f"Testing API: {url}")
print(f"Uploading file: {file_path}")
print("Mode: MANUAL (Simulated)" if capacities else "Mode: AUTO")

try:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, data=payload, files=files)
        
    if response.status_code == 200:
        print("\nSuccess!")
        print("-" * 30)
        print(f"Distributed: {response.headers.get('X-Distributed-Count')}")
        print(f"Unassigned:  {response.headers.get('X-Unassigned-Count')}")
        
        # Save Result
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print("-" * 30)
        print(f"Result saved to: {os.path.abspath(output_path)}")
    else:
        print(f"\nFailed: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\nError: {e}")
    print("Is the backend server running? (python backend/app.py)")
