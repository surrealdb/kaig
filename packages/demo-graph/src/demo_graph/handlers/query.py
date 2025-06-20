import random

import click
from demo_graph.models import Thing

from kai_graphora.db import DB
from kai_graphora.llm import LLM

PERSONALITIES = [
    """
You are a very close friend of mine, and always funny, roasting me like only
really close friends can.""",
#     """
# Your are a very close friend, who has always been secretely in love
# with me, but you are starting to feel empowered and want to let me know
# your true feelings""",
    # "You are Llarimar, from the book Warbreaker.",
    # "You are Sazed, from the Mistborn saga.",
]


def query_handler(db: DB, llm: LLM, query: str) -> None:
    click.echo(f"Querying {click.style(query, fg='yellow')}...")

    answer_data = {}
    click.echo(
        "\nThings ("
        + click.style("vector search", fg="green")
        + " and "
        + click.style("recursive graph query", fg="blue")
        + "):"
    )
    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="document"
    )
    answer_data["item_name"] = res[0].get("name")
    answer_data["item_description"] = res[0].get("desc")
    for i, x in enumerate(res):
        if x["dist"] < 0.4 and answer_data["item_location"]:
            break
        click.echo(f"• {x['dist']:.0%}: ", nl=False)
        click.secho(x.get("name"), fg="green", nl=False)
        things_with_containers = db.recursive_graph_query(
            Thing, x["id"], "stored_in"
        )
        click.echo(". Find it in: ", nl=False)
        for x in things_with_containers:
            temp = " > ".join([b.id for b in reversed(x.buckets)])
            if i == 0:
                # we only want the top one for giving the answer
                answer_data["item_location"] = temp
            click.secho(temp, fg="blue")

    click.echo(
        "\nTags ("
        + click.style("vector search", fg="green")
        + " and "
        + click.style("recursive graph query", fg="blue")
        + "):"
    )
    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="tag"
    )
    for x in res:
        click.echo(f"• {x['dist']:.0%}: ", nl=False)
        click.secho(x.get("name"), fg="green", nl=False)
        things = db.graph_query_inward(Thing, x["id"], "has_tag", "document")
        roots = set()
        for thing in things:
            for related in thing["related"]:
                things_with_containers = db.recursive_graph_query(
                    Thing, related, "stored_in"
                )
                for x in things_with_containers:
                    roots.add(x.buckets[0].id)
        click.echo(". Usually stored in: ", nl=False)
        click.secho(", ".join(roots), fg="blue")

    click.echo(
        "\nCategories (" + click.style("vector search", fg="green") + "):"
    )
    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="category", k=3
    )
    for x in res:
        click.echo(f"• {x['dist']:.0%}: {x.get('name')}")

    # -- Generated response
    click.echo("\nGenerating answer...\n")
    answer = llm.gen_answer(
        f"Where did i put my {query}", answer_data, random.choice(PERSONALITIES)
    )
    click.secho(answer, fg="cyan")
