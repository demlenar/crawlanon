import requests
from bs4 import BeautifulSoup
import random
import time

# SOCKS5 proxies list (Tor or your own proxy server)
PROXIES = [
    "socks5h://127.0.0.1:9050",  # Example: Tor local SOCKS5 proxy
    # Add more proxies here if needed
]

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def get_html(url, proxy):
    try:
        response = requests.get(url, proxies={"http": proxy, "https": proxy}, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[!] Error using proxy {proxy}: {e}")
        return None

def crawl(urls):
    for url in urls:
        proxy = random.choice(PROXIES)
        print(f"[+] Crawling: {url} via {proxy}")
        html = get_html(url, proxy)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else "No title"
            print(f"    - Page Title: {title}")
        else:
            print("    - Failed to fetch content.")

        # Random delay for privacy protection (basic PET)
        time.sleep(random.uniform(2, 6))

if __name__ == "__main__":
    urls_to_crawl = [
        "https://example.com",
        "https://httpbin.org/ip",
        # Add more URLs here
    ]
    crawl(urls_to_crawl)
