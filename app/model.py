
from pydantic import BaseModel, Field


class WGS84(BaseModel):
    x: float = Field(..., ge=120.035141, le=122.035141,
                     description="x must be in Taiwan")
    y: float = Field(..., ge=21.8969, le=25.298401,
                     description="y must be in Taiwan")


class LandNumber(BaseModel):
    name: str
    code: str
