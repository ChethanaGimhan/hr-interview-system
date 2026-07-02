import requests

response = requests.get("https://api.github.com")
print(response.status_code)
print("git is working")