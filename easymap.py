from typing import Optional

import aiohttp
import re
import os

from towninfo.town_code_repository import TownCodeRepository

DEFAULT_TIMEOUT = 30  # 30 seconds

EASYMAP_BASE_URL = "https://easymap.land.moi.gov.tw"
PROXIES = {"https": "proxy:5566"}

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
EASYMAP_CACHE_DIR = os.path.join(ROOT_DIR, "cache")

TownCodeRepo = TownCodeRepository(EASYMAP_CACHE_DIR)


class LandNumber:
    def __init__(self, name, code):
        self.name = name
        self.code = code

    def __str__(self):
        return f"{self.name}({self.code})"


class WebRequestError(RuntimeError):
    def __init__(self, message, status_code, response_body):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class EasyMapSession:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, proxy: Optional[str] = None):
        self._proxy = proxy
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout))
        self._headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"
        }

    async def __aenter__(self):
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._session.close()

    async def _init_session(self):
        easymap_url = EASYMAP_BASE_URL + "/Index"

        resp = await self._session.get(easymap_url)
        if "JSESSIONID" not in self._session.cookie_jar.filter_cookies(easymap_url):
            raise WebRequestError(
                "Failed getting session from easymap",
                resp.status,
                await resp.text())

    async def _get_point_city(self, x: float, y: float):
        point_city_url = EASYMAP_BASE_URL + "/Query_json_getPointCity"
        data = {"wgs84x": x, "wgs84y": y}

        async with self._session.post(
            point_city_url,
            data=data,
            proxy=self._proxy,
            raise_for_status=True
        ) as resp:
            json = await resp.json()
            if "cityCode" not in json:
                text = await resp.text()
                raise WebRequestError(
                    f"Failed parsing city code text:{text}",
                    resp.status,
                    text
                )

            return json["cityCode"]

    async def _get_token(self):
        set_token_url = EASYMAP_BASE_URL + "/pages/setToken.jsp"
        token_re = re.compile(
            '<input type="hidden" name="(.*?)" value="(.*?)" />')

        resp = await self._session.post(
            set_token_url,
            proxy=self._proxy,
            raise_for_status=True
        )

        data = await resp.text()
        token = dict([(m.group(1), m.group(2))
                      for m in token_re.finditer(data)])

        if "token" not in token:
            raise WebRequestError("Failed parsing token",
                                  resp.status, data)
        return token

    async def _get_door_info(self, x, y, city_code, token):
        get_door_info_url = EASYMAP_BASE_URL + "/Door_json_getDoorInfoByXY"
        data = {"city": city_code, "coordX": x, "coordY": y, **token}

        resp = await self._session.post(
            get_door_info_url,
            data=data,
            proxy=self._proxy,
            raise_for_status=True
        )
        try:
            return await resp.json()
        except Exception:
            raise WebRequestError("Failed parsing door info",
                                  resp.staus, await resp.text())

    async def get_land_number(self, x, y) -> LandNumber:
        """
        Get land number by WGS84 coordinates.

        since the easymap API doesn't provide townname, we then insert a townname field by looking up in xml files in ./towncode downloaded from https://api.nlsc.gov.tw/other/ListTown1/{A-Z}
        """
        city_code = await self._get_point_city(x, y)
        town_code = await TownCodeRepo.load(city_code)
        if not town_code:
            raise RuntimeError(f"Failed to find town code for {city_code}")

        token = await self._get_token()
        result = await self._get_door_info(
            x, y,
            city_code,
            token
        )

        land_number = LandNumber(
            name=town_code.code2name(result["towncode"]),
            code=result["towncode"]
        )

        return land_number


async def main(x: float, y: float):
    async with EasyMapSession() as session:
        land_number = await session.get_land_number(x, y)
        print(land_number)

if __name__ == "__main__":
    import sys
    import asyncio

    if len(sys.argv) != 3:
        print("Usage: easymap.py <wgs84x> <wgs84y>")
        sys.exit(-1)
    x, y = sys.argv[1:3]

    asyncio.run(main(float(x), float(y)))
