# Create a version of the crawler that rotates through a list of proxies
# ENSURE PACKAGES EXIST!!!
# py -m pip install selenium beautifulsoup4 requests numpy
#===================== LOOK UP =======================

from selenium import webdriver
from selenium.webdriver.chrome.service import Service #Google
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service #Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
import time
import random
import numpy as np

def fetch_proxies_selenium(limit=10):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome(options=options)
    driver.get("https://free-proxy-list.net/")
    time.sleep(3)  # Wait for JS to render the table
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    proxy_list = []
    for row in soup.select("div.fpl-list table tbody tr"):
        cols = row.find_all("td")
        ip = cols[0].text.strip()
        port = cols[1].text.strip()
        is_https = cols[6].text.strip().lower() == "yes"
        anonymity = cols[4].text.strip().lower()

        if is_https: # and "elite" in anonymity:
            proxy_list.append(f"{ip}:{port}")
        if len(proxy_list) >= limit:
            break
    return proxy_list

def fetch_proxies_1():
    url = "https://proxylist.geonode.com/api/proxy-list?limit=10&page=1&sort_by=lastChecked&sort_type=desc"
    res = requests.get(url)
    proxies = []
    if res.status_code == 200:
        data = res.json()
        for proxy in data.get("data", []):
            ip = proxy["ip"]
            port = proxy["port"]
            proxies.append(f"{ip}:{port}")
    return proxies

# Proxy Source (Pluggable)
def fetch_proxies(limit=10):
    url = "https://free-proxy-list.net/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    proxy_list = []

    for row in soup.select("div.fpl-list table tbody tr"):
        print(row)
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

CHROME_DRIVER_PATH = "C:\\Repos\\chromedriver-win64\\chromedriver.exe"  #TODO: You got to Change this path to location of install
GECKO_DRIVER_PATH = "C:\\\\Path\\\\To\\\\geckodriver.exe"
USE_GOOGLE = True #true for google, flase for Firefox

# Setup Chrome with Proxy
#TODO: Better modularity 
def create_browser_with_proxy(proxy):
    if USE_GOOGLE:
        chrome_options = Options()
        #chrome_options.add_argument(f'--proxy-server=http://{proxy}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)
    else:
        firefox_options = Options()
        firefox_options.headless = True
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("network.proxy.type", 1)
        firefox_profile.set_preference("network.proxy.http", proxy.split(":")[0])
        firefox_profile.set_preference("network.proxy.http_port", int(proxy.split(":")[1]))
        firefox_profile.set_preference("network.proxy.ssl", proxy.split(":")[0])
        firefox_profile.set_preference("network.proxy.ssl_port", int(proxy.split(":")[1]))
        firefox_profile.update_preferences()
        return webdriver.Firefox(service=Service(GECKO_DRIVER_PATH), options=firefox_options, firefox_profile=firefox_profile)
    
def is_proxy_working(proxy):
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}",
    }
    try:
        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
        return response.status_code == 200
    except:
        return False


# Privacy Enhancing Techniques
def randomized_delay(mean=5, jitter=2):
    delay = max(1, random.gauss(mean, jitter))
    print(f"Delaying for {delay:.2f} seconds...")
    time.sleep(delay)

def add_laplace_noise(value, sensitivity=1.0, epsilon=0.5):
    noise = np.random.laplace(0, sensitivity / epsilon)
    return value + noise

# Crawler Logic
def crawl(urls, proxies):
    for i, url in enumerate(urls):
        #proxy = "51.158.123.35:8811"
        proxy = proxies[i % len(proxies)]
        print(f"Using proxy: {proxy}")

        if not is_proxy_working(proxy):
            print(f"Skipping bad proxy: {proxy}")
            continue

        driver = create_browser_with_proxy(proxy)
        try:
            randomized_delay()
            print(f"Crawling: {url}")
            driver.get(url)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else "No title"
            noisy_length = add_laplace_noise(len(html))
            print(f"Title: {title}, Length+Noise: {noisy_length:.1f}")
        except Exception as e:
            print(f"Error crawling {url}: {e}")
        finally:
            driver.quit()

# === Main ===
if __name__ == "__main__":
    urls_to_crawl = [
        "http://example.com",
        "http://httpbin.org/ip",
        "http://httpbin.org/user-agent"
    ]
    proxy_list = fetch_proxies_selenium()
    if not proxy_list:
        print("No proxies available. Exiting.")
    else:
        crawl(urls_to_crawl, proxy_list)