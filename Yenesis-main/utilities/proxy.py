#!/usr/bin/env python
# utilities/proxy.py
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
import time

# Step 1: Scrape Free Proxies
def get_free_proxies():
    url = "https://free-proxy-list.net/"
    proxies = []

    try:
        headers = {
            "User-Agent": UserAgent().random
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        with open("proxy_page_debug.html", "w") as f:
            f.write(soup.prettify())
        print("🔍 Saved response HTML to proxy_page_debug.html")

        table = soup.find("table", class_="table")
        if not table:
            print("❌ Proxy list table not found on the page!")
            return proxies

        rows = table.find_all("tr")
        if rows and "IP Address" in rows[0].text:
            rows = rows[1:]  # Skip header row

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 7 and cols[6].text.strip().lower() == "yes":  # HTTPS
                proxy = f"{cols[0].text.strip()}:{cols[1].text.strip()}"
                proxies.append(proxy)

    except Exception as e:
        print(f"❌ Error fetching proxies: {e}")

    return proxies


# Step 2: Validate Proxies
def test_proxy(proxy):
    try:
        response = requests.get("https://httpbin.org/ip", proxies={
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }, timeout=5)
        return response.status_code == 200
    except:
        return False

def build_proxy_pool():
    raw_proxies = get_free_proxies()
    print(f"🔧 Testing {len(raw_proxies)} proxies...")
    working = []
    for p in raw_proxies:
        if test_proxy(p):
            print(f"✅ Working proxy: {p}")
            working.append(p)
        time.sleep(0.5)  # avoid IP ban while testing
    print(f"🎯 Final proxy pool size: {len(working)}")
    return working

if __name__ == "__main__":
    proxies = get_free_proxies()
    print(f"Fetched {len(proxies)} proxies:")
    for p in proxies:
        print(p)
