import requests

BASE_URL = "http://localhost:8001/api"

def verify():
    print("--- 1. Login ---")
    login_data = {"email": "admin@safeguard.local", "password": "admin1234"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Login success ✓")

    print("\n--- 2. Add Webcam ---")
    cam_data = {"camera_id": "webcam", "source": "0"}
    resp = requests.post(f"{BASE_URL}/cameras", json=cam_data, headers=headers)
    if resp.status_code in [201, 400]: # 400 if already exists
        print(f"Camera add response: {resp.status_code}")
        print(resp.json())
    else:
        print(f"Failed to add camera: {resp.status_code} {resp.text}")
        return

    print("\n--- 3. List Cameras ---")
    resp = requests.get(f"{BASE_URL}/cameras", headers=headers)
    print(resp.json())

if __name__ == "__main__":
    verify()
