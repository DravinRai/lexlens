import requests, json

BASE_URL = "http://localhost:8000/api"
def run():
    print("Uploading...")
    with open("sample_lease.txt", "rb") as f:
        res = requests.post(f"{BASE_URL}/upload", files={"file": f}, data={"slot": "a"}).json()
    session_id = res["session_id"]

    print("Q1: Is my landlord allowed to evict me for no reason?")
    q1 = requests.post(f"{BASE_URL}/chat", json={"session_id": session_id, "message": "Is my landlord allowed to evict me for no reason?"}).json()
    print(json.dumps(q1, indent=2))

    print("Q2: Can I sue my landlord for this?")
    q2 = requests.post(f"{BASE_URL}/chat", json={"session_id": session_id, "message": "Can I sue my landlord for this?"}).json()
    print(json.dumps(q2, indent=2))

if __name__ == "__main__":
    run()
