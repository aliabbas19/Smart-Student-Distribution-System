
import requests
import json
import os

BASE_URL = 'http://127.0.0.1:5000'
FILE_PATH = os.path.join('data', 'input data.xlsx')

def test_scan():
    print("\n[Testing /scan]...")
    url = f"{BASE_URL}/scan"
    try:
        with open(FILE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("Success!")
            print(f"Student Count: {data.get('student_count')}")
            print(f"Departments Found: {data.get('departments')}")
            return data.get('departments')
        else:
            print(f"Failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_distribute_equal(total_cap=150):
    print(f"\n[Testing /distribute - EQUAL Mode (Total: {total_cap})]...")
    url = f"{BASE_URL}/distribute"
    
    payload = {
        'mode': 'EQUAL',
        'total_capacity': str(total_cap)
    }
    
    try:
        with open(FILE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, data=payload, files=files)
            
        if response.status_code == 200:
            print("Success!")
            print(f"Distributed: {response.headers.get('X-Distributed-Count')}")
            print(f"Unassigned:  {response.headers.get('X-Unassigned-Count')}")
            with open('output_equal.xlsx', 'wb') as f:
                f.write(response.content)
            print("Saved 'output_equal.xlsx'")
        else:
            print(f"Failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error: {e}")

def test_distribute_manual(depts):
    print(f"\n[Testing /distribute - MANUAL Mode]...")
    url = f"{BASE_URL}/distribute"
    
    # Create specific caps
    caps = {d: 50 for d in depts}
    caps[depts[0]] = 10 # Restriction test
    
    payload = {
        'mode': 'MANUAL',
        'capacities': json.dumps(caps)
    }
    
    try:
        with open(FILE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, data=payload, files=files)
            
        if response.status_code == 200:
            print("Success!")
            print(f"Distributed: {response.headers.get('X-Distributed-Count')}")
            print(f"Unassigned:  {response.headers.get('X-Unassigned-Count')}")
            with open('output_manual.xlsx', 'wb') as f:
                f.write(response.content)
            print("Saved 'output_manual.xlsx'")
        else:
            print(f"Failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    depts = test_scan()
    if depts:
        test_distribute_equal()
        test_distribute_manual(depts)
