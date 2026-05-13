import asyncio
import os


async def delete_file(file_path: str) -> None:
    await asyncio.sleep(60)
    if os.path.exists(file_path):
        os.remove(file_path)
