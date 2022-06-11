import os
from easymap.app.towninfo.county_code_repository import CountyCodeRepository

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


async def test_load_county_code_without_cache():
    repo = CountyCodeRepository(ROOT_DIR)
    assert repo.get_cache_path() == os.path.join(
        ROOT_DIR, 'county.json')

    repo.clean_cache()
    assert os.path.exists(repo.get_cache_path()) is False

    county_code = await repo.load()
    assert county_code is not None

    assert county_code.name2code('基隆市') == 'C'
    assert county_code.name2code('新北市') == 'F'

    assert os.path.exists(repo.get_cache_path()) is True

    repo.clean_cache()
    assert os.path.exists(repo.get_cache_path()) is False
