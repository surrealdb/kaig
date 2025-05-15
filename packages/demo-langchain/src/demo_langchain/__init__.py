import asyncio

from demo_langchain.main import main


def cli():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
