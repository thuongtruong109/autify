import asyncio
import aiohttp
from aiohttp import ClientSession, ClientResponse

class CloudflareClient:
    BASE_URL = "https://api.cloudflare.com/client/v4"

    def __init__(self, api_token: str, timeout: int = 15, max_retries: int = 3):
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session: ClientSession | None = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, json=None, params=None):
        if self.session is None:
            raise RuntimeError("Session is not initialized. Use 'async with CloudflareClient(...)'.")

        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(1, self.max_retries + 1):
            try:
                async with self.session.request(
                    method, url, headers=self.headers, json=json, params=params
                ) as resp:

                    if resp.status >= 400:
                        text = await resp.text()
                        print(f"[ERROR] {method} {url} -> {resp.status}")
                        print(f"[DETAIL] {text}")
                        return None

                    try:
                        return await resp.json()
                    except Exception:
                        text = await resp.text()
                        print(f"[ERROR] Invalid JSON response: {text}")
                        return None

            except aiohttp.ClientError as e:
                print(f"[WARN] Network error ({e}). Retry {attempt}/{self.max_retries}...")
                await asyncio.sleep(0.5 * attempt)
            except asyncio.TimeoutError:
                print(f"[WARN] Timeout. Retry {attempt}/{self.max_retries}...")
                await asyncio.sleep(0.5 * attempt)

        print(f"[FATAL] Request failed after {self.max_retries} retries: {method} {url}")
        return None

    async def get_zone_id(self, domain: str):
        resp = await self._request("GET", "/zones", params={"name": domain})
        if resp and resp.get("result"):
            return resp["result"][0]["id"]

        print(f"[ERROR] Zone not found for domain: {domain}")
        return None

    async def add_dns_record(self, zone_id: str, record: dict):
        return await self._request("POST", f"/zones/{zone_id}/dns_records", json=record)

    async def add_multiple_dns_records(self, domain: str, records: list):
        zone_id = await self.get_zone_id(domain)
        if not zone_id:
            return []

        tasks = [
            self.add_dns_record(zone_id, record)
            for record in records
        ]

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def enable_dnssec(self, domain: str):
        zone_id = await self.get_zone_id(domain)
        if not zone_id:
            return None

        return await self._request(
            "PATCH",
            f"/zones/{zone_id}/dnssec",
            json={"status": "active"}
        )