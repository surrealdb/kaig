from dataclasses import dataclass

from openai import AsyncOpenAI

from kaig.db import DB


@dataclass
class Deps:
    db: DB
    openai: AsyncOpenAI
