
import requests
import json
import os

url = 'http://127.0.0.1:5000/distribute'
headers = {'Content-Type': 'application/json'}
data = {
    'capacities': {
        "الامن السيبراني": 40,
        "تكنولوجيا المعلومات": 40,
        "علوم الحاسوب": 40
    }
}

try:
    print(f"Sending POST request to {url} with capacities...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("Success! Headers received:")
        print(f"Distributed: {response.headers.get('X-Distributed-Count')}")
        print(f"Unassigned: {response.headers.get('X-Unassigned-Count')}")
        
        # Save the file
        output_file = 'output_test.xlsx'
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Excel file saved to: {os.path.abspath(output_file)}")
        print(f"File size: {len(response.content)} bytes")
    else:
        print("Error:", response.status_code, response.text)

except Exception as e:
    print("Request failed:", e)
