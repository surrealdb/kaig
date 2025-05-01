import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import click
import requests

from demo_graph_rag_gaming.db import DB
from demo_graph_rag_gaming.handlers.utils import ensure_db_open
from demo_graph_rag_gaming.models import AppData, AppsListRoot, SteamAppDetails


@dataclass
class Log:
    appid: int
    msg: str


@ensure_db_open
async def load_json(
    file: str,
    skip: int = -1,
    limit: int = -1,
    error_limit: int = -1,
    retry_errors: bool = False,
    throttle: int = 0,
    *,
    db: DB,
) -> None:
    # -- Load json with appids
    file_path = Path(file)
    with open(file_path) as f:
        applist_json = json.load(f)
    apps_list = AppsListRoot.model_validate(applist_json)
    games = apps_list.applist.apps
    if skip != -1:
        games = games[skip:]
    if limit == -1:
        limit = len(games)

    # -- Query API for each game and store details in database
    errored: list[Log] = []
    skipped: list[Log] = []
    soft_errors: list[Log] = []
    inserted = 0
    index = -1
    stop = False
    click.echo(f"Starting ingestion of {len(games)} games...")
    with click.progressbar(range(limit)) as bar:
        for bar_step in bar:
            if stop:
                break
            while True:
                index += 1
                game = games[index]
                appid = game.appid

                # -- Check limit
                if _should_stop(limit, inserted, error_limit, len(errored)):
                    stop = True
                    break

                # -- Skip if name is empty
                if not game.name:
                    skipped.append(Log(appid, "Name is empty"))
                    continue

                # -- Check if we already have details for this appid, or if this
                #    appid has errored before (unless we want to retry errors)
                try:
                    if await db.get_appdata(appid):
                        skipped.append(Log(appid, "Already exists"))
                        continue
                    elif not retry_errors and await db.error_exists(appid):
                        skipped.append(Log(appid, "Errored before"))
                        continue
                except Exception as e:
                    soft_errors.append(
                        Log(
                            appid,
                            f"Failed to check if {appid} exists. Will try to insert. Error: {e}",
                        )
                    )

                # -- Get details for each game
                try:
                    detail = _get_details(appid)
                except Exception as e:
                    errored.append(Log(appid, str(e)))
                    await db.safe_insert_error(appid, str(e))
                    continue

                # -- Insert details in database
                try:
                    await db.insert_appdata(appid, detail)
                    inserted += 1
                except Exception as e:
                    errored.append(
                        Log(appid, f"Failed to insert data for {appid}: {e}")
                    )
                    await db.safe_insert_error(appid, str(e))

                # -- Step progress
                break

            # -- Throttle
            await asyncio.sleep(throttle)

    # -- Details
    if errored:
        click.secho("Errored:", fg="red")
        for x in errored:
            click.echo(f"{x.msg} ({x.appid})")
    if soft_errors:
        click.secho("Soft errors:", fg="yellow")
        for x in soft_errors:
            click.echo(f"{x.msg} ({x.appid})")

    # -- Summary
    click.echo()
    click.secho(f"Inserted {inserted}", fg="green")
    click.secho(f"Skipped {len(skipped)}", fg="yellow")
    click.secho(f"Soft errors {len(soft_errors)}", fg="yellow")
    click.secho(f"Errored {len(errored)}", fg="red")


def _should_stop(
    limit: int, inserted: int, error_limit: int, errored_count: int
) -> bool:
    return (limit != -1 and inserted >= limit) or (
        error_limit != -1 and errored_count >= error_limit
    )


def _get_details(appid: int) -> AppData:
    q = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    res = requests.get(q)
    app_details = SteamAppDetails.model_validate(res.json())
    app = app_details.get_app_details(appid)
    if app and app.data:
        return app.data
    else:
        raise ValueError(f"Failed to get details for appid {appid}")
