import asyncio
from itertools import islice

from fastapi import APIRouter

router = APIRouter()


@router.get("/multi_async_task")
async def download_image():
    task_list = [asyncio.create_task(asyncio.sleep(1)) for _ in range(23)]

    def batch_iter(iterable, batch_size):
        it = iter(iterable)
        while batch := list(islice(it, batch_size)):
            yield batch

    for batch in batch_iter(task_list, 5):
        await asyncio.gather(*batch)
