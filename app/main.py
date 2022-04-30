import os

from typing import Optional
from fastapi import FastAPI, Query

from .model import LandNumber
from .easymap import EasyMapSession

EASYMAP_PROXY = os.environ.get("EASYMAP_PROXY", "")

app = FastAPI()


@app.get("/")
async def root():
    return {}


@app.get("/landnumber")
async def landnumber(
    longitude: float = Query(..., gt=120.035141, lt=122.035141),
    latitude: float = Query(..., gt=21.8969, lt=25.298401),
) -> Optional[LandNumber]:
    async with EasyMapSession(proxy=EASYMAP_PROXY) as session:
        land_number = await session.get_land_number(longitude, latitude)

    return land_number
