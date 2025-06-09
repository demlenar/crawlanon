from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

CHROME_DRIVER_PATH = "C:\\Repos\\chromedriver-win64\\chromedriver.exe"

options = Options()
options.headless = True

driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
driver.get("https://example.com")
print(driver.title)
driver.quit()