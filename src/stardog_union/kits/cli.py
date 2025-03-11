import os
from typing import Optional

import prettytable
import typer
import yaml
from dotenv import find_dotenv, load_dotenv
from typing_extensions import Annotated

from stardog_union.kits import install, uninstall
from stardog_union.kits.base import (
    DataLoad,
    Kit,
    Schema,
    StardogKitRepository,
    load_targets_from_env,
)
from stardog_union.more_stardog import ConnectionFactory

kits = typer.Typer()

HELP_TARGET = "Name of Stardog endpoint to use for operations"
HELP_DATABASE = "Name of the database on the endpoint to use for operations"


@kits.command(name="init")
def init_kit(
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the kit")],
    group: Annotated[str, typer.Option("--group", "-g", help="Group of the kit")],
    version: Annotated[
        str, typer.Option("--version", "-v", help="Version of the kit")
    ] = "1.0",
    location: Annotated[
        Optional[str],
        typer.Option(
            "--location", help="Location to create a new kit. Uses cwd if not specified"
        ),
    ] = None,
):
    kit_loc = location if location else os.getcwd()
    kit_dir = os.path.basename(kit_loc)

    k = Kit(
        name=name if name else kit_dir,
        group=group if group else kit_dir,
        version=version,
        data=[
            DataLoad(file="data.ttl", graph="urn:data"),
            DataLoad(file="schema.ttl", graph="urn:schema"),
        ],
        schemas=[Schema(name="schema_name", graphs=["urn:schema"])],
        namespaces=[],
        queries=[],
    )

    with open(os.path.join(kit_loc, "kit.yaml"), "w") as f:
        yaml.dump(k.to_dict(), f)

    with open(os.path.join(kit_loc, "readme.md"), "w") as f:
        f.write(f"# {k.group}:{k.name}:{k.version}")

    with open(os.path.join(kit_loc, "data.ttl"), "w") as f:
        f.write("# Data goes here")

    with open(os.path.join(kit_loc, "schema.ttl"), "w") as f:
        f.write("# Data goes here")

    print(f"Kit initialized at {location}")


@kits.command(name="ls")
def list_kits(
    database: Annotated[str, typer.Option("--database", "-d", help=HELP_DATABASE)],
    target: Annotated[
        Optional[str], typer.Option("--target", "-t", help=HELP_TARGET)
    ] = None,
):
    cf = get_connction_factory(
        target if target else os.getenv("default_target"), database
    )

    print(
        "Listing kits installed in %s @ %s as %s"
        % (cf.options["database"], cf.options["endpoint"], cf.options["username"])
    )

    t = prettytable.PrettyTable()
    t.field_names = ["ID", "Name", "Description"]
    for m in StardogKitRepository(cf).list():
        t.add_row([m[0], m[1], m[2]])
    print(t)


def get_connction_factory(target, database: str | None = None):
    targets = load_targets_from_env()

    cf = ConnectionFactory(targets[target]) if target in targets else None

    if not cf:
        raise Exception(
            f"Missing target {target}, available targets are: {[k for k in targets]}"
        )

    target_info = targets.get(target)

    if database:
        target_info["database"] = database

    return cf


@kits.command(name="install")
def install_kit(
    kit_path: str,
    target: Annotated[
        Optional[str], typer.Option("--target", "-t", help=HELP_TARGET)
    ] = None,
    database: Annotated[
        Optional[str], typer.Option("--database", "-d", help=HELP_DATABASE)
    ] = None,
):
    kit_location = kit_path
    if os.path.isfile(kit_path):
        kit_location = os.path.dirname(kit_path)

    kit_to_add = Kit.from_file(kit_location)

    cf = get_connction_factory(
        target if target else os.getenv("default_target"),
        database if database else Kit.default_database_name(kit_to_add),
    )

    install.install_kit(cf, kit_to_add, kit_location, show_progress=True)

    print("Kit installed")


@kits.command(name="uninstall")
def uninstall_kit(
    kit_id: str,
    target: Annotated[
        Optional[str], typer.Option("--target", "-t", help=HELP_TARGET)
    ] = None,
    database: Annotated[
        Optional[str], typer.Option("--database", "-d", help=HELP_DATABASE)
    ] = None,
    datasources: Annotated[
        bool,
        typer.Option(
            "--sources",
            "-s",
            is_flag=True,
            flag_value=True,
            help="Drop data sources associated with the kit",
        ),
    ] = False,
    db_drop: Annotated[
        bool,
        typer.Option(
            "--drop",
            is_flag=True,
            flag_value=True,
            help="Drop database associated with the kit",
        ),
    ] = False,
):
    db = database if database else kit_id.replace(":", "_").replace(".", "_")
    cf = get_connction_factory(target if target else os.getenv("default_target"), db)

    if uninstall.uninstall_kit(
        cf,
        kit_id,
        clean_database=db_drop,
        clean_datasources=datasources,
        show_progress=True,
    ):
        print("Kit uninstalled")
    else:
        print(f"Nothing to clean, database '{db}' does not exist")


def cli():
    load_dotenv(find_dotenv(usecwd=True))

    kits()


if __name__ == "__main__":
    cli()
