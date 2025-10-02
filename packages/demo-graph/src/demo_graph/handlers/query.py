import random
from typing import Any

import click
from surrealdb import RecordID
from demo_graph.models import Document, Thing

from kaig.db import DB
from kaig.llm import LLM

PERSONALITIES = [
    """You are a usefull assistant"""
    #     """
    # You are a very close friend of mine, and always funny, roasting me like only
    # really close friends can.""",
    #     """
    # Your are a very close friend, who has always been secretely in love
    # with me, but you are starting to feel empowered and want to let me know
    # your true feelings""",
    #     "You are Llarimar, from the book Warbreaker.",
    # "You are Sazed, from the Mistborn saga.",
]

# THRESHOLD = 0.35
THRESHOLD = 0.5


def query_handler(
    db: DB, llm: LLM, query: str, additional_instructions: str = ""
) -> None:
    click.echo(f"Querying {click.style(query, fg='yellow')}...")

    answer_data: list[dict[str, RecordID | str | None]] = []
    click.echo(
        "\nThings ("
        + click.style("vector search", fg="green")
        + " and "
        + click.style("recursive graph query", fg="blue")
        + "):"
    )
    res, _time = db.vector_search_from_text(
        Thing, query, table="document", k=10
    )
    if res:
        for i, (x, score) in enumerate(res):
            assert x.id
            if score < THRESHOLD:
                break
            click.echo(f"• {score:.0%}: ", nl=False)
            click.secho(x.name, fg="green", nl=False)
            things_with_containers = db.recursive_graph_query(
                Thing, x.id, "stored_in"
            )
            click.echo(". Find it in: ", nl=False)
            for y in things_with_containers:
                temp = " > ".join([b.id for b in reversed(y.buckets)])
                answer_data_temp = {
                    "item_id": x.id,
                    "item_name": x.name,
                    "item_description": x.content,
                    "item_url": x.url,
                    "item_location": temp,
                }
                answer_data.append(answer_data_temp)
                click.secho(temp, fg="blue")

    click.echo(
        "\nTags ("
        + click.style("vector search", fg="green")
        + " and "
        + click.style("recursive graph query", fg="blue")
        + "):"
    )
    res, _time = db.vector_search_from_text(Document, query, table="tag", k=10)
    top_tag_embedding = []
    for i, (x, score) in enumerate(res):
        assert x.id
        if score < THRESHOLD:
            break
        if i == 0:
            top_tag_embedding = x.embedding
        click.echo(f"• {score:.0%}: ", nl=False)
        click.secho(x.content, fg="green", nl=False)
        things, _time = db.graph_query_inward(
            Thing,
            x.id,
            "has_tag",
            "document",
            top_tag_embedding,
        )
        roots: set[str] = set()
        for thing in things:
            assert thing.id is not None
            things_with_containers = db.recursive_graph_query(
                Thing, thing.id, "stored_in"
            )
            for x in things_with_containers:
                if x.buckets:
                    roots.add(" > ".join([b.id for b in reversed(x.buckets)]))
        click.echo(". Usually stored in: ", nl=False)
        click.secho("; ".join(roots), fg="blue")

    click.echo(
        "\nCategories (" + click.style("vector search", fg="green") + "):"
    )
    res, _time = db.vector_search_from_text(
        Document, query, table="category", k=3
    )
    for x, score in res:
        if score < THRESHOLD:
            break
        click.echo(f"• {score:.0%}: {x.content}")

    # -- Graph query: tag siblings
    click.echo("\nTag siblings:")

    def similarity_filter(x: Thing[Any]) -> float:
        return x.similarity if x.similarity else 0

    if answer_data:
        id = answer_data[0].get("item_id")
        if isinstance(id, RecordID):
            res, _time = db.graph_siblings(
                Thing,
                id,
                "has_tag",
                "document",
                "tag",
            )
            for augmented_thing in sorted(
                res,
                key=similarity_filter,
                reverse=True,
            ):
                click.echo(
                    f"- {augmented_thing.similarity:.0%} {augmented_thing.content} (url: {augmented_thing.url})"
                )
        else:
            click.echo(f"Expected a RecordID, but got {type(id)}")

    # -- Graph query: container siblings
    click.echo("\nContainer siblings:")
    if answer_data:
        id = answer_data[0].get("item_id")
        if isinstance(id, RecordID):
            res, _time = db.graph_siblings(
                Thing,
                id,
                "stored_in",
                "document",
                "container",
            )
            for augmented_thing in sorted(
                res,
                key=lambda x: x.similarity if x.similarity else 0,
                reverse=True,
            ):
                click.echo(
                    f"- {augmented_thing.similarity:.0%} {augmented_thing.content} (url: {augmented_thing.url})"
                )
        else:
            click.echo(f"Expected a RecordID, but got {type(id)}")

    # -- Generated response
    if answer_data:
        click.echo("\nGenerating answer...\n")
        click.secho(answer_data, fg="black")
        answer = llm.gen_answer(
            query,
            answer_data,
            random.choice(PERSONALITIES) + additional_instructions,
        )
        click.secho(answer, fg="cyan")
