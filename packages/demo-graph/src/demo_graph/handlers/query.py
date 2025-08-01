import random

import click
from demo_graph.models import Thing

from kai_graphora.db import DB
from kai_graphora.llm import LLM

PERSONALITIES = [
    """
You are a very close friend of mine, and always funny, roasting me like only
really close friends can.""",
    """
Your are a very close friend, who has always been secretely in love
with me, but you are starting to feel empowered and want to let me know
your true feelings""",
    "You are Llarimar, from the book Warbreaker.",
    # "You are Sazed, from the Mistborn saga.",
]

# THRESHOLD = 0.35
THRESHOLD = 0.5


def query_handler(
    db: DB, llm: LLM, query: str, additional_instructions: str = ""
) -> None:
    click.echo(f"Querying {click.style(query, fg='yellow')}...")

    answer_data = []
    click.echo(
        "\nThings ("
        + click.style("vector search", fg="green")
        + " and "
        + click.style("recursive graph query", fg="blue")
        + "):"
    )
    res = db.vector_search(llm.gen_embedding_from_desc(query), table="document")
    if res:
        for i, x in enumerate(res):
            if x["dist"] > THRESHOLD:
                break
            click.echo(f"• {1 - x['dist']:.0%}: ", nl=False)
            click.secho(x.get("name"), fg="green", nl=False)
            things_with_containers = db.recursive_graph_query(
                Thing, x["id"], "stored_in"
            )
            click.echo(". Find it in: ", nl=False)
            for x in things_with_containers:
                temp = " > ".join([b.id for b in reversed(x.buckets)])
                answer_data_temp = {
                    "item_id": res[0].get("id"),
                    "item_name": res[0].get("name"),
                    "item_description": res[0].get("desc"),
                    "item_url": res[0].get("url"),
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
    res = db.vector_search(llm.gen_embedding_from_desc(query), table="tag")
    top_tag_embedding = []
    for i, x in enumerate(res):
        if x["dist"] > THRESHOLD:
            break
        if i == 0:
            top_tag_embedding = x.get("embedding")
        click.echo(f"• {1 - x['dist']:.0%}: ", nl=False)
        click.secho(x.get("name"), fg="green", nl=False)
        things = db.graph_query_inward(
            Thing,
            # TODO: we can send a list here
            x["id"],
            "has_tag",
            "document",
            top_tag_embedding,
        )
        roots = set()
        for thing in things:
            assert thing.id is not None
            things_with_containers = db.recursive_graph_query(
                Thing, thing.id, "stored_in"
            )
            for x in things_with_containers:
                if x.buckets:
                    roots.add(x.buckets[0].id)
        click.echo(". Usually stored in: ", nl=False)
        click.secho(", ".join(roots), fg="blue")

    click.echo(
        "\nCategories (" + click.style("vector search", fg="green") + "):"
    )
    res = db.vector_search(
        llm.gen_embedding_from_desc(query), table="category", k=3
    )
    for x in res:
        if x["dist"] > THRESHOLD:
            break
        click.echo(f"• {1 - x['dist']:.0%}: {x.get('name')}")

    # -- Graph query: tag siblings
    click.echo("\nTag siblings:")
    if answer_data:
        res = db.graph_siblings(
            Thing,
            answer_data[0].get("item_id", ""),
            "has_tag",
            "document",
            "tag",
        )
        for augmented_thing in sorted(
            res, key=lambda x: x.similarity if x.similarity else 0, reverse=True
        ):
            click.echo(
                f"- {augmented_thing.similarity:.0%} {augmented_thing.desc} (url: {augmented_thing.url})"
            )

    # -- Graph query: container siblings
    click.echo("\nContainer siblings:")
    if answer_data:
        res = db.graph_siblings(
            Thing,
            answer_data[0].get("item_id", ""),
            "stored_in",
            "document",
            "container",
        )
        for augmented_thing in sorted(
            res, key=lambda x: x.similarity if x.similarity else 0, reverse=True
        ):
            click.echo(
                f"- {augmented_thing.similarity:.0%} {augmented_thing.desc} (url: {augmented_thing.url})"
            )

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
