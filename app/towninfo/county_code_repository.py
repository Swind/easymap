import os
import logging
import json
import aiohttp
import aiofiles
import xml.etree.ElementTree as ET

from typing import Dict, Optional, Tuple

ROOT_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(ROOT_DIR, "..", "..", "cache")

COUNTY_CODE_API = "https://api.nlsc.gov.tw/other/ListCounty"
COUNTY_FILE_NAME = "county.json"

logger = logging.getLogger(__name__)


class CountyCode:
    def __init__(self,
                 code_name_map: Dict[str, str],
                 name_code_map: Dict[str, str]):
        self.code_name_map = code_name_map
        self.name_code_map = name_code_map

    def code2name(self, code: str) -> Optional[str]:
        return self.code_name_map.get(code)

    def name2code(self, name: str) -> Optional[str]:
        return self.name_code_map.get(name)


class CountyCodeRepository:
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.root_path = cache_dir
        else:
            cache_dir = ROOT_DIR

    async def load(self) -> Optional[CountyCode]:
        result = await self.load_county_cache()
        if result:
            return result

        code_name_map, name_code_map = await self.download_county()
        if not code_name_map or not name_code_map:
            return None

        county_code = CountyCode(code_name_map, name_code_map)
        await self.save_county_cache(county_code)
        return county_code

    def clean_cache(self) -> None:
        cache_path = self.get_cache_path()
        if os.path.exists(cache_path):
            os.remove(cache_path)

    def get_cache_path(self) -> str:
        return os.path.join(self.root_path, COUNTY_FILE_NAME)

    async def load_county_cache(self) -> Optional[CountyCode]:
        cache_path = self.get_cache_path()
        if not os.path.exists(cache_path):
            return None

        async with aiofiles.open(cache_path, "r") as fp:
            cache = json.loads(await fp.read())
            if cache["code_name_map"] and cache["name_code_map"]:
                return CountyCode(cache["code_name_map"], cache["name_code_map"])

        return None

    async def save_county_cache(self, county_code: CountyCode) -> None:
        os.makedirs(self.root_path, exist_ok=True)

        async with aiofiles.open(self.get_cache_path(), "w") as fp:
            return await fp.write(json.dumps({
                "code_name_map": county_code.code_name_map,
                "name_code_map": county_code.name_code_map
            }))

    async def download_county(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        async with aiohttp.request("GET", COUNTY_CODE_API) as resp:
            root = ET.fromstring(await resp.text())

        code_name_map: Dict[str, str] = {}
        name_code_map: Dict[str, str] = {}

        for countyItem in root:
            countyJson = {}
            for item in countyItem:
                countyJson[item.tag] = item.text

            if not countyJson["countycode"] or not countyJson["countyname"]:
                continue

            code_name_map[countyJson["countycode"]] = countyJson["countyname"]
            name_code_map[countyJson["countyname"]] = countyJson["countycode"]

        return code_name_map, name_code_map
