import requests
import rich
from bs4 import BeautifulSoup

url = "https://dash.sonicbit.net/login"

response = requests.get(url)

html_content = response.text

soup = BeautifulSoup(html_content, "html.parser")

csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]

rich.print(csrf_token)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
}

login_data = {
    "_token": csrf_token,
    "_method": "POST",
    "email": "add your email",
    "password": "add your password",
}

login_endpoint = "https://dash.sonicbit.net/login_user"

response = requests.post(
    login_endpoint, headers=headers, data=login_data, cookies=response.cookies
)

rich.print(response.json())

cc = response.cookies


rich.print(cc)
