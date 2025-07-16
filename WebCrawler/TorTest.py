import httpx
import asyncio

async def test_tor_proxy():
    proxy = "socks5h://127.0.0.1:9050"
    async with httpx.AsyncClient(proxies=proxy, timeout=10) as client:
        r = await client.get("https://httpbin.org/ip")
        print("Tor IP:", r.json()["origin"])

asyncio.run(test_tor_proxy())