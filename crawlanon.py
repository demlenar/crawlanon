import requests
from bs4 import BeautifulSoup

#  Create rquests session and set SOCKS proxies
session = requests.Session()
session.proxies = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
}

# Collect origin of current request to prove that proxies are in place, print to show the origin
test_response = session.get('http://httpbin.org/ip')
print(test_response.json())

# Set URL and collect requests response
url = 'http://quotes.toscrape.com'
response = requests.get(url)

# Parsing HTML using Beautiful Soup and extracting text
soup = BeautifulSoup(response.text, 'html.parser')
quotes = soup.find_all('span', {'class': 'text'})
authors = soup.find_all('small', {'class':'author'})

# Print the quotes and their authors
for quote, author in zip(quotes, authors):
    print(f"{quote.get_text()} — {author.get_text()}")

print(test_response.json())




