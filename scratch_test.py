import json
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:8000/chat",
    data=json.dumps({"message": "how do we scale this product to 10k users?"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        print(json.dumps(res, indent=2))
except Exception as e:
    print(f"Failed: {e}")
