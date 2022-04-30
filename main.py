from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class WGS84(BaseModel):
    x: float
    y: float


@app.get("/")
async def root():
    return {}


@app.get("/landnumber")
async def landnumber(wgs84: WGS84):
    return {}
