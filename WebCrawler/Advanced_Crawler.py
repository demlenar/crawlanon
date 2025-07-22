# Requires Tor running on localhost:9050
# - Async crawling using httpx
# - Rotating user-agents and headers
# - Rotating proxies with health checks
# - Gaussian delay strategy
# - Selenium integration for dynamic content and real browser behavior


import asyncio
import httpx
import random
import requests
import socket
import time
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse
#print("[DEBUG] Using httpx version:", httpx.__version__)
#print("[DEBUG] httpx module loaded from:", httpx.__file__)

#Circuit rotation
from stem import Signal
from stem.control import Controller

#Selenium imports for browser automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import numpy as np

# ==================== CONFIG ====================
# Swap between httpx and Selenium. If you want to use Selenium, set this to True, otherwise False for httpx
SELENIUM_CRAWL = False 

# Maximum number of retries for failed requests
MAX_RETRIES = 3

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
    "https://httpbin.org",
    "https://www.bbc.com",
    "http://quotes.toscrape.com",
    "https://www.wikipedia.org"
]

CHROME_DRIVER_PATH = "C:\\Repos\\chromedriver-win64\\chromedriver.exe"  #This is machine dependent!! Change this path to location of install

# ==================== UTILITIES ====================
 
def fetch_proxies(limit=100):
    """
    Scrapes free HTTPS proxies from a public proxy listing website.
    Filters only HTTPS proxies and returns a list of IP:Port strings.

    Note: This is not currently used in the main logic but can be
    swapped in as an alternative to Tor or SOCKS proxies.
    """
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
    """
    Introduces a random delay between requests based on a Gaussian (normal) distribution.
    Helps simulate human-like browsing behavior and avoid detection.
    Args:
        mean (float): Mean time delay in seconds.
        stddev (float): Standard deviation of the delay.
    """
    delay = max(0.5, random.gauss(mean, stddev))
    print(f"Delaying for {delay:.2f} seconds")
    await asyncio.sleep(delay)

async def test_proxy(proxy: str) -> bool:
    """
    Tests whether a single proxy is functional by sending a request to httpbin.org/ip.
    Args:
        proxy (str): Proxy string in format "http://ip:port" or "socks5://ip:port".
    Returns:
        bool: True if proxy works, False otherwise.
    """
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
    """
    Filters the list of configured proxies and returns only those that are operational.
    Returns:
        list: List of proxy strings that successfully passed the connectivity test.
    """
    tasks = [test_proxy(proxy) for proxy in PROXIES]
    results = await asyncio.gather(*tasks)
    return [PROXIES[i] for i, ok in enumerate(results) if ok]

def create_browser(proxy, user_agent):
    """
    Configures and launches a headless Chrome browser through a SOCKS5 proxy and custom User-Agent.
    Used for dynamic web content scraping via Selenium.
    Args:
        proxy (str): SOCKS5 proxy in format "ip:port".
        user_agent (str): User-Agent string to override browser fingerprinting.
    Returns:
        WebDriver or None: A Selenium WebDriver instance or None on failure.
    """
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
    """
    Similar to gaussian_delay but blocking. Used for spacing out Selenium browser sessions.
    Args:
        mean (float): Mean time delay in seconds.
        stddev (float): Standard deviation of the delay.
    """
    delay = max(0.5, np.random.normal(mean, stddev))
    print(f"Delay: {delay:.2f}s")
    time.sleep(delay)

def rotate_tor_circuit(self) -> bool:
    """
    Rotate the Tor circuit by sending a NEWNYM signal to the Tor control port.
        
    Returns:
        bool: True if rotation was successful, False otherwise.
    """
    try:
        with Controller.from_port(port=self.config.tor_control_port) as controller:
            if self.config.tor_control_password:
                controller.authenticate(password=self.config.tor_control_password)
            else:
                controller.authenticate()
            controller.signal(Signal.NEWNYM)
            time.sleep(10)  # Wait for new circuit to stabilize (Tor's minimum)
            print("Successfully rotated Tor circuit")
            return True
    except Exception as e:
        print(f"Failed to rotate Tor circuit: {str(e)}")
        return False

# ==================== CORE CRAWLER ====================

def selenium_crawl(url, proxy, user_agent)-> Optional[Dict]:
    """
    Uses Selenium to load a full webpage through a SOCKS5 proxy and scrape its title.
    Can be extended to extract dynamic JavaScript-rendered content.
    Args:
        url (str): Target URL to crawl.
        proxy (str): SOCKS5 proxy in format "ip:port".
        user_agent (str): Browser user-agent string.
    """
    driver = create_browser(proxy, user_agent)
    if not driver:
        return

    try:
        driver.get(url)
        time.sleep(2)# Wait for page load
        title = driver.title
        soup = BeautifulSoup(driver.page_source, "html.parser")
        quotes = soup.find_all('span', {'class': 'text'})
        authors = soup.find_all('small', {'class': 'author'})
            
        # New fields
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
                
        # Meta tags
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_description['content'] if meta_description and 'content' in meta_description.attrs else None
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        meta_keywords = meta_keywords['content'] if meta_keywords and 'content' in meta_keywords.attrs else None
                
        # Links
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if urlparse(link['href']).netloc == domain]
        external_links = [link['href'] for link in links if urlparse(link['href']).netloc and urlparse(link['href']).netloc != domain]
                
        # Images
        images = [{'src': img.get('src'), 'alt': img.get('alt')} for img in soup.find_all('img') if img.get('src')]
                
        # Headings
        headings = []
        for tag in ['h1', 'h2', 'h3']:
            headings.extend([h.get_text(strip=True) for h in soup.find_all(tag)])
                
        # Paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
                
        # Social media metadata
        og_data = {meta['property']: meta['content'] for meta in soup.find_all('meta', property=True) if 'content' in meta.attrs}
        twitter_data = {meta['name']: meta['content'] for meta in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}) if 'content' in meta.attrs}
                
        # Page stats
        html_size = len(str(soup).encode('utf-8'))
        visible_text = soup.get_text(strip=True)
        word_count = len(visible_text.split())
                
        # Scripts
        scripts = [script.get('src') or script.get_text(strip=True) for script in soup.find_all('script')]
                
        result = {
                    'url': url,
                    'title': title,
                    'quotes_count': len(quotes),
                    'authors_count': len(authors),
                    'meta_description': meta_description,
                    'meta_keywords': meta_keywords,
                    'internal_links': internal_links,
                    'external_links': external_links,
                    'images': images,
                    'headings': headings,
                    'paragraphs': paragraphs,
                    'og_data': og_data,
                    'twitter_data': twitter_data,
                    'html_size': html_size,
                    'word_count': word_count,
                    'scripts': scripts
        }
        print(f"Successfully fetched {url} | Proxy: {proxy} | Title: {title}")
        return result
    except Exception as e:
        print(f"Error fetching {url} with proxy {proxy}: {str(e)}")
        return None
    finally:
        driver.quit()

async def fetch(url: str, theproxy: str, headers: dict, attempt: int = 0) -> Optional[Dict]:
    """
    Sends an HTTP GET request through a proxy with randomized headers using httpx (async).
    Extracts page title and number of quote/author elements (for demo purposes).
    Args:
        url (str): The target webpage URL.
        theproxy (str): Proxy string (e.g., "socks5h://127.0.0.1:9050").
        headers (dict): Custom headers to use, such as User-Agent and Referer.
    """
    try:
        async with httpx.AsyncClient(proxy=theproxy, headers=headers, timeout=10) as client:
            r = await client.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string.strip() if soup.title else "No title found"
            quotes = soup.find_all('span', {'class': 'text'})
            authors = soup.find_all('small', {'class':'author'})

            # New fields
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
                
            # Meta tags
            meta_description = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_description['content'] if meta_description and 'content' in meta_description.attrs else None
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            meta_keywords = meta_keywords['content'] if meta_keywords and 'content' in meta_keywords.attrs else None
                
            # Links
            links = soup.find_all('a', href=True)
            internal_links = [link['href'] for link in links if urlparse(link['href']).netloc == domain]
            external_links = [link['href'] for link in links if urlparse(link['href']).netloc and urlparse(link['href']).netloc != domain]
                
            # Images
            images = [{'src': img.get('src'), 'alt': img.get('alt')} for img in soup.find_all('img') if img.get('src')]
                
            # Headings
            headings = []
            for tag in ['h1', 'h2', 'h3']:
                headings.extend([h.get_text(strip=True) for h in soup.find_all(tag)])
                
            # Paragraphs
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
                
            # Social media metadata
            og_data = {meta['property']: meta['content'] for meta in soup.find_all('meta', property=True) if 'content' in meta.attrs}
            twitter_data = {meta['name']: meta['content'] for meta in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}) if 'content' in meta.attrs}
                
            # Page stats
            html_size = len(str(soup).encode('utf-8'))
            visible_text = soup.get_text(strip=True)
            word_count = len(visible_text.split())
                
            # Scripts
            scripts = [script.get('src') or script.get_text(strip=True) for script in soup.find_all('script')]
                
            result = {
                    'url': url,
                    'title': title,
                    'quotes_count': len(quotes),
                    'authors_count': len(authors),
                    'status': r.status_code,
                    'meta_description': meta_description,
                    'meta_keywords': meta_keywords,
                    'internal_links': internal_links,
                    'external_links': external_links,
                    'images': images,
                    'headings': headings,
                    'paragraphs': paragraphs,
                    'og_data': og_data,
                    'twitter_data': twitter_data,
                    'html_size': html_size,
                    'word_count': word_count,
                    'scripts': scripts
            }

            print(f"Successfully fetched {url} | Proxy: {theproxy} | Title: {title}")
            return result
    except Exception as e:
        if attempt < MAX_RETRIES:
            print(f"Retrying {url} with proxy {theproxy} due to error: {e}")
            await gaussian_delay()
            return await fetch(url, theproxy, headers, attempt + 1)
        print(f"Failed to fetch {url} after {MAX_RETRIES} via {theproxy}: {e}")
        return None

async def crawl(urls: list):
    """
    Main crawl controller. Selects working proxies, rotates headers and either:
    - uses httpx for fast async scraping
    - or Selenium for dynamic content
    Args:
        urls (list): List of target URLs to process.
    """
    results = []
    working_proxies = await get_working_proxies()
    if not working_proxies:
        print("No working proxies found.")
        return

    for url in urls:
        # Rotate Tor circuit for each URL
        #rotate_tor_circuit()  

        proxy = random.choice(working_proxies)
        headers = random.choice(HEADERS_POOL)
        #SELENIUM_CRAWL = True  # Set to True to use Selenium, False for httpx
        if SELENIUM_CRAWL:
            result = selenium_crawl(url, proxy, headers["User-Agent"])
            selenium_delay()
        else:
            result = await fetch(url, proxy, headers)
            await gaussian_delay()
        if result:
            results.append(result)

    with open('crawl_results.json', 'w') as f:
            json.dump(results, f, indent=2)
    print(f"Saved {len(results)} results to crawl_results.json")



# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Your Local IP Address is: {ip_address}")
    asyncio.run(crawl(URLS_TO_CRAWL))

