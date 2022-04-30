import os
import logging
import json
import aiohttp
import aiofiles
import xml.etree.ElementTree as ET


from typing import Dict, Optional, Tuple

ROOT_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(ROOT_DIR, 'cache')

TOWN_CODE_API = "https://api.nlsc.gov.tw/other/ListTown/{county_code}"
TOWN_FILE_NAME = "{county_code}_town.json"

logger = logging.getLogger(__name__)


class TownCode:
    def __init__(self, county_code: str,
                 code_name_map: Dict[str, str],
                 name_code_map: Dict[str, str]):

        self.county_code = county_code
        self.code_name_map = code_name_map
        self.name_code_map = name_code_map

    def code2name(self, code: str) -> Optional[str]:
        return self.code_name_map.get(code)

    def name2code(self, name: str) -> Optional[str]:
        return self.name_code_map.get(name)


class TownCodeRepository:
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.root_path = cache_dir
        else:
            cache_dir = CACHE_DIR

    async def load(self, county_code: str) -> Optional[TownCode]:
        result = await self.load_cache(county_code)
        if result:
            return result

        code_name_map, name_code_map = await self.download_town_code(county_code)
        if not code_name_map or not name_code_map:
            return None

        town_code = TownCode(county_code, code_name_map, name_code_map)
        await self.save_cache(county_code, town_code)
        return town_code

    async def load_cache(self, county_code) -> Optional[TownCode]:
        cache_path = self.get_cache_path(county_code)
        if not os.path.exists(cache_path):
            return None

        async with aiofiles.open(cache_path, "r") as fp:
            cache = json.loads(await fp.read())
            if cache["code_name_map"] and cache["name_code_map"]:
                return TownCode(county_code,
                                cache["code_name_map"],
                                cache["name_code_map"])

        return None

    def clean_cache(self, county_code: str) -> None:
        town_cache_path = self.get_cache_path(county_code)
        if os.path.exists(town_cache_path):
            os.remove(town_cache_path)

    def get_cache_path(self, county_code: str) -> str:
        return os.path.join(self.root_path,
                            TOWN_FILE_NAME.format(county_code=county_code))

    async def save_cache(self, county_code: str, town_code: TownCode) -> None:
        os.makedirs(self.root_path, exist_ok=True)

        async with aiofiles.open(self.get_cache_path(county_code), "w") as fp:
            return await fp.write(json.dumps({
                "code_name_map": town_code.code_name_map,
                "name_code_map": town_code.name_code_map
            }))

    async def download_town_code(self, county_code: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        async with aiohttp.request("GET", TOWN_CODE_API.format(county_code=county_code)) as resp:
            root = ET.fromstring(await resp.text())

        code_name_map: Dict[str, str] = {}
        name_code_map: Dict[str, str] = {}

        for town_items in root:
            town_json = {}
            for item in town_items:
                town_json[item.tag] = item.text

            if not town_json["towncode"] or not town_json["townname"]:
                continue

            code_name_map[town_json["towncode"]] = town_json["townname"]
            name_code_map[town_json["townname"]] = town_json["towncode"]

        return code_name_map, name_code_map
