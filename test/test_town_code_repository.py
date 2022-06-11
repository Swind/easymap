import os
from easymap.app.towninfo.town_code_repository import TownCodeRepository

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


async def test_load_town_code_without_cache():
    county_code = "F"

    repo = TownCodeRepository(ROOT_DIR)
    assert repo.get_cache_path(county_code) == os.path.join(
        ROOT_DIR, f"{county_code}_town.json")

    repo.clean_cache(county_code)
    assert os.path.exists(repo.get_cache_path("F")) is False

    town_code = await repo.load(county_code)
    assert town_code is not None

    assert town_code.name2code('新莊區') == 'F01'
    assert town_code.code2name('F01') == '新莊區'

    assert os.path.exists(repo.get_cache_path(county_code)) is True

    repo.clean_cache(county_code)
    assert os.path.exists(repo.get_cache_path(county_code)) is False
