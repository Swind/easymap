from app.easymap import EasyMapSession


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
