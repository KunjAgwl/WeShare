import os
import urllib.request
from dotenv import load_dotenv

load_dotenv()
url = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://") + "/v2/pipeline"
token = os.environ["TURSO_AUTH_TOKEN"]

print(f"Testing URL: {url}")
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
try:
    resp = urllib.request.urlopen(req, timeout=5)
    print("Success:", resp.read())
except Exception as e:
    print("Error:", e)
