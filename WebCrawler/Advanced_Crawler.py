# Requires Tor running on localhost:9050
# - Async crawling using httpx
# - Rotating user-agents and headers
# - Rotating proxies with health checks
# - Gaussian delay strategy

import asyncio
import httpx
print("[DEBUG] Using httpx version:", httpx.__version__)
print("[DEBUG] httpx module loaded from:", httpx.__file__)
import random
import requests
import socket
import time
from bs4 import BeautifulSoup

#Selenium imports for browser automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import numpy as np

# ==================== CONFIG ====================
SELENIUM_CRAWL = False # Swap between httpx and Selenium. If you want to use Selenium, set this to True, otherwise False for httpx

# List of proxies (SOCKS5)
PROXIES = ["socks5h://127.0.0.1:9050"]#fetch_proxies()
 

# User-Agent and header rotation pool
HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.8",
        "Referer": "https://duckduckgo.com"
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/112.0",
        "Accept-Language": "en-GB,en;q=0.7",
        "Referer": "https://www.bing.com"
    }
]

# Target URLs to crawl
URLS_TO_CRAWL = [
    "https://example.com",
    "https://httpbin.org/ip",
    "https://httpbin.org/headers",
    "http://quotes.toscrape.com"
]

CHROME_DRIVER_PATH = "C:\\Repos\\chromedriver-win64\\chromedriver.exe"  #TODO: You got to Change this path to location of install

# ==================== UTILITIES ====================

# Proxy Source (Pluggable)
def fetch_proxies(limit=100):
    url = "https://free-proxy-list.net/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    proxy_list = []

    for row in soup.select("div.fpl-list table tbody tr"):
        #print(row)
        cols = row.find_all("td")
        ip = cols[0].text.strip()
        port = cols[1].text.strip()
        is_https = cols[6].text.strip().lower() == "yes"
        anonymity = cols[4].text.strip().lower()

        if is_https: #and "elite" in anonymity:
            proxy_list.append(f"{ip}:{port}")
        if len(proxy_list) >= limit:
            break

    return proxy_list

async def gaussian_delay(mean=3.0, stddev=1.0):
    delay = max(0.5, random.gauss(mean, stddev))
    print(f"Delaying for {delay:.2f} seconds")
    await asyncio.sleep(delay)

async def test_proxy(proxy: str) -> bool:
    try:
        response = requests.get("https://httpbin.org/ip", proxies={
            "http": proxy,
            "https": proxy
        }, timeout=10)
        print("Proxy is working!")
        print("Tor IP:", response.json()["origin"])
        return True
    except Exception as e:
        print("Proxy test failed:", e)
        return False

async def get_working_proxies() -> list:
    tasks = [test_proxy(proxy) for proxy in PROXIES]
    results = await asyncio.gather(*tasks)
    return [PROXIES[i] for i, ok in enumerate(results) if ok]

def create_browser(proxy, user_agent):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument(f"--proxy-server=socks5://{proxy}")

    try:
        driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)
        return driver
    except WebDriverException as e:
        print(f"Failed to launch Chrome with proxy {proxy}: {e}")
        return None
    
def selenium_delay(mean=3.0, stddev=1.0):
    delay = max(0.5, np.random.normal(mean, stddev))
    print(f"⏳ Delay: {delay:.2f}s")
    time.sleep(delay)

# ==================== CORE CRAWLER ====================

def selenium_crawl(url, proxy, user_agent):
    driver = create_browser(proxy, user_agent)
    if not driver:
        return

    try:
        driver.get(url)
        time.sleep(2)
        title = driver.title
        print(f"[{proxy}] {url} -> Title: {title}")
    except Exception as e:
        print(f"Error fetching {url} with {proxy}: {e}")
    finally:
        driver.quit()

async def fetch(url: str, theproxy: str, headers: dict):
    try:
        async with httpx.AsyncClient(proxy=theproxy, headers=headers, timeout=10) as client:
            r = await client.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string.strip() if soup.title else "No title found"
            quotes = soup.find_all('span', {'class': 'text'})
            authors = soup.find_all('small', {'class':'author'})
            print(f"{url} | Proxy: {theproxy} | Title: {title} | Authors: {len(authors)}")
    except Exception as e:
        print(f"Failed to fetch {url} via {theproxy}: {e}")

async def crawl(urls: list):
    working_proxies = await get_working_proxies()
    if not working_proxies:
        print("No working proxies found.")
        return

    for url in urls:
        proxy = random.choice(working_proxies)
        headers = random.choice(HEADERS_POOL)
        #SELENIUM_CRAWL = True  # Set to True to use Selenium, False for httpx
        if SELENIUM_CRAWL:
            selenium_crawl(url, proxy, headers["User-Agent"])
            selenium_delay()
        else:
            await fetch(url, proxy, headers)
            await gaussian_delay()



# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Your Local IP Address is: {ip_address}")

    asyncio.run(crawl(URLS_TO_CRAWL))

