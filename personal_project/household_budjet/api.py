import requests

url = 'https://open.er-api.com/v6/latest/USD'

response = requests.get(url)
print(f"{response.status_code}")
print(response.text)