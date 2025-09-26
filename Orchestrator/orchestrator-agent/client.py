import requests

prompt = input("Enter your prompt: ")
resp = requests.post("http://127.0.0.1:8000/run", json={"prompt": prompt})
print("Response:", resp.json())
