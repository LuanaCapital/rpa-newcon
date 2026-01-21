# utils/human_delay.py

import asyncio
import random

async def human_delay(min_seconds: float = 2.5, max_seconds: float = 4.0):
    """
    Delay humano randômico para evitar comportamento de bot.
    """
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))
