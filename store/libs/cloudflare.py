import asyncio
import aiohttp

class CloudflareAsyncClient:
    def __init__(self, api_token: str = "D0LRG-crTGRTqMn9udddaRCkzfw919PON0e2YpcP"):
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, endpoint: str, json: dict = None, params: dict = None):
        url = f"{self.base_url}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, json=json, params=params) as resp:
                try:
                    resp.raise_for_status()
                    return await resp.json()
                except aiohttp.ClientResponseError as e:
                    print(f"Request failed: {e}")
                    return None

    async def get_zone_id(self, domain: str):
        resp = await self._request("GET", "/zones", params={"name": domain})
        if resp and resp.get("result"):
            return resp["result"][0]["id"]
        print("Zone not found")
        return None

    async def add_dns_record(self, zone_id: str, record: dict):
        return await self._request("POST", f"/zones/{zone_id}/dns_records", json=record)

    async def add_multiple_dns_records(self, domain: str, records: list):
        zone_id = await self.get_zone_id(domain)
        if not zone_id:
            return []

        tasks = [self.add_dns_record(zone_id, record) for record in records]
        return await asyncio.gather(*tasks)

# async def main():
#     domain = "gunova.site"
#     dns_records = [
#         {"type": "A", "name": "www.gunova.site", "content": "198.51.100.4", "ttl": 1, "proxied": False},
#         {"type": "A", "name": "api.gunova.site", "content": "198.51.100.5", "ttl": 1, "proxied": False},
#         {"type": "CNAME", "name": "blog.gunova.site", "content": "gunova.site", "ttl": 1, "proxied": False},
#     ]

#     client = CloudflareAsyncClient()
#     results = await client.add_multiple_dns_records(domain, dns_records)

#     for r in results:
#         print(r)

# asyncio.run(main())