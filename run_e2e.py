import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
FILE_PATH = "sample_lease.txt"

def print_step(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def post_with_retry(*args, **kwargs):
    time.sleep(15)  # Avoid rate limits
    for i in range(5):
        try:
            resp = requests.post(*args, **kwargs)
            if resp.status_code == 200:
                return resp
            print(f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(15)
    return requests.post(*args, **kwargs)

def run_e2e():
    # 1. Upload
    print_step("STEP 1: Upload Document")
    with open(FILE_PATH, 'rb') as f:
        response = post_with_retry(f"{BASE_URL}/upload", files={"file": f}, data={"slot": "a"})
    
    upload_res = response.json()
    print(json.dumps(upload_res, indent=2))
    session_id = upload_res["session_id"]
    
    # 2. Classify
    print_step("STEP 2: Classify Document")
    response = post_with_retry(f"{BASE_URL}/classify", json={"session_id": session_id})
    classify_res = response.json()
    print(json.dumps(classify_res, indent=2))
    
    # 3. Set Jurisdiction (US-CA)
    print_step("STEP 3: Set Jurisdiction (US - California)")
    response = post_with_retry(f"{BASE_URL}/set-jurisdiction", json={
        "session_id": session_id,
        "country": "US",
        "state": "CA"
    })
    jur_res = response.json()
    print(json.dumps(jur_res, indent=2))
    
    # 4. Analyze (Tier A/B, Risk Tags, Checklist)
    print_step("STEP 4: Analyze (Tier A, Tier B, Risk Tags, Checklist)")
    response = post_with_retry(f"{BASE_URL}/analyze", json={"session_id": session_id})
    analyze_res = response.json()
    print(json.dumps(analyze_res, indent=2))
    
    # 5. Q&A 1: Standard Question
    print_step("STEP 5: Q&A - Standard Question")
    question1 = "What is the security deposit?"
    print(f"Q: {question1}")
    response = post_with_retry(f"{BASE_URL}/chat", json={
        "session_id": session_id,
        "message": question1
    })
    print(json.dumps(response.json(), indent=2))
    
    # 6. Q&A 2: Adversarial Question 1
    print_step("STEP 6: Q&A - Adversarial Question 1 (Asking for Legal Advice)")
    question2 = "Can you draft a legal letter to sue my landlord based on this lease?"
    print(f"Q: {question2}")
    response = post_with_retry(f"{BASE_URL}/chat", json={
        "session_id": session_id,
        "message": question2
    })
    print(json.dumps(response.json(), indent=2))
    
    # 7. Q&A 3: Adversarial Question 2
    print_step("STEP 7: Q&A - Adversarial Question 2 (Asking outside scope)")
    question3 = "What's the capital of France?"
    print(f"Q: {question3}")
    response = post_with_retry(f"{BASE_URL}/chat", json={
        "session_id": session_id,
        "message": question3
    })
    print(json.dumps(response.json(), indent=2))
    
    # 8. Unsupported Jurisdiction Test
    print_step("STEP 8: Unsupported Jurisdiction Test (France)")
    response = post_with_retry(f"{BASE_URL}/set-jurisdiction", json={
        "session_id": session_id,
        "country": "France",
        "state": ""
    })
    jur_fr_res = response.json()
    print(json.dumps(jur_fr_res, indent=2))
    
    print_step("STEP 9: Analyze with Unsupported Jurisdiction")
    response = post_with_retry(f"{BASE_URL}/analyze", json={"session_id": session_id})
    analyze_fr_res = response.json()
    # Let's just print Tier B and checklist to show the fallback
    print("Tier B:")
    print(json.dumps(analyze_fr_res.get("tier_b", {}), indent=2))
    print("\nChecklist:")
    print(json.dumps(analyze_fr_res.get("checklist", {}), indent=2))

if __name__ == "__main__":
    # give the server a second to start
    time.sleep(2)
    run_e2e()
