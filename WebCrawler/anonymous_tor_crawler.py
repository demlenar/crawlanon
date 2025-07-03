
import subprocess
import time
import random
import requests
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import numpy as np

# Configuration
TOR_PATH = "C:\\Repos\\Tor\\tor.exe"  # Path to tor.exe 
TORRC_PATH = "C:\\Tor\\torrc"  # Path to torrc file
TOR_CONTROL_PORT = 9051
TOR_PASSWORD = "your_password"  # Set in torrc and hash it #TODO: don't hardcode password
TOR_SOCKS_PROXY = "socks5h://127.0.0.1:9050"

# Launch Tor process
def launch_tor():
    try:
        subprocess.Popen([TOR_PATH, "-f", TORRC_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Launched Tor process...")
        time.sleep(10)  # Wait for Tor 
    except Exception as e:
        print(f"Failed to launch Tor: {e}")

# Renew Tor circuit
def renew_tor_circuit():
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate(password=TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
            print("New Tor circuit requested.")
            time.sleep(controller.get_newnym_wait())
    except Exception as e:
        print(f"Failed to renew Tor circuit: {e}")

# Get a Tor session with proxy
def get_tor_session():
    session = requests.Session()
    session.proxies = {
        'http': TOR_SOCKS_PROXY,
        'https': TOR_SOCKS_PROXY
    }
    return session

# Randomized delay for PET
def randomized_delay(mean=5, jitter=2):
    delay = max(1, random.gauss(mean, jitter))
    print(f"Delaying for {delay:.2f} seconds...")
    time.sleep(delay)

# Get randomized headers
def get_random_headers():
    ua = UserAgent()
    return {
        'User-Agent': ua.random
    }

# Add Laplace noise (differential privacy)
def add_laplace_noise(value, sensitivity=1.0, epsilon=0.5):
    noise = np.random.laplace(0, sensitivity / epsilon)
    return value + noise

# Crawl function
def crawl(urls, circuit_rotation_interval=3):
    session = get_tor_session()
    for i, url in enumerate(urls):
        if i % circuit_rotation_interval == 0 and i != 0:
            renew_tor_circuit()
            session = get_tor_session()

        randomized_delay()

        try:
            headers = get_random_headers()
            response = session.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "No title"
            noisy_length = add_laplace_noise(len(response.text))
            print(f"Fetched: {url[:60]}... Title: {title} (Length + noise: {noisy_length:.1f})")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

# Example usage
if __name__ == "__main__":
    urls_to_crawl = [
        "http://example.com",
        "http://check.torproject.org",
        "http://httpbin.org/ip"
    ]
    launch_tor()
    crawl(urls_to_crawl)
