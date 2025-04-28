import asyncio

from .pipeline import pipeline


def main():
    asyncio.run(pipeline())
