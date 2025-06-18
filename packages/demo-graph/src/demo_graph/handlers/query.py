import click
from demo_graph.models import Thing

from kai_graphora.db import DB
from kai_graphora.llm import LLM


def query_handler(db: DB, llm: LLM, query: str) -> None:
    click.echo(f"Querying {click.style(query, fg='yellow')}...")

    click.echo("\nThings:")
    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="document"
    )
    for x in res:
        click.echo(f"• {x['dist']:.0%}: ", nl=False)
        click.secho(x.get("name"), fg="green", nl=False)
        things_with_containers = db.recursive_graph_query(
            Thing, x["id"], "stored_in"
        )
        click.echo(". Find it in: ", nl=False)
        for x in things_with_containers:
            click.echo(" > ".join([b.id for b in reversed(x.buckets)]))

    click.echo("\nTags:")
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

    click.echo("\nCategories:")
    res = db.vector_search(
        query, llm.gen_embedding_from_desc(query), table="category", k=3
    )
    for x in res:
        click.echo(f"• {x['dist']:.0%}: {x.get('name')}")
