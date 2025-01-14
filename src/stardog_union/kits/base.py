import abc
import logging
import os
from typing import Any

import stardog
import yaml
from rdflib import Literal as RDFLiteral
from rdflib import URIRef
from rdflib.term import Node

from stardog_union import more_stardog as stardog_utils
from stardog_union import vocabs
from stardog_union.kits import queries

LOG = logging.getLogger(__name__)


def default_namespaces() -> dict[str, str]:
    return {
        "catalog": "tag:stardog:api:catalog:",
        "m": "urn:stardog:modules:",
        "sqs": "tag:stardog:api:sqs:",
        "rule": "tag:stardog:api:rule:",
        "sd": "urn:stardog:",
        "sql": "tag:stardog:api:sql:",
        "spa": "tag:stardog:api:analytics:",
    }


def load_targets_from_env() -> dict[str, dict[str, str]]:
    """Looks for environment variables fitting the kits format and assembles them into login credentials
    for named endpoints. The result is a dictionary where the keys are endpoint names (targets) and the values
    are a dictionary of its configuration options."""

    targets = {}

    for env_var in os.environ:
        if env_var.endswith("_server"):
            target_name = env_var[: env_var.find("_server")]
            target_server = os.environ[env_var]
            creds = stardog_utils.get_password_file_credentials(endpoint=target_server)
            target_user = os.environ.get(
                f"{target_name}_username", creds[0] if creds else "admin"
            )
            target_passwd = os.environ.get(
                f"{target_name}_password", creds[1] if creds else "admin"
            )

            conn_details = {
                "endpoint": target_server,
                "username": target_user,
                "password": target_passwd,
            }
            targets[target_name] = conn_details

    return targets


class DataLoad:
    graph: str | None = None
    """Graph to load data into.

    If none, the default graph is used, however if the file serialization supports
    named graphs, those can be specified within the file.

    Best practice would be to explicitly declare graphs."""

    # file and source are mutually exclusive
    file: str | None = None
    """Path to a file on disk containing the data to be loaded"""
    source: str | None = None
    """Name of the Stardog DataSource where the data is located"""

    name: str | None = None
    """Name for this asset"""

    mappings: str | None = None
    """Stardog Mappings to use for loading the data."""

    options: dict | None = None
    """VG options"""

    def __init__(
        self,
        graph: str | None = None,
        file: str | None = None,
        source: str | None = None,
        name: str | None = None,
        mappings: str | None = None,
        options: dict | None = None,
    ):
        self.graph = graph
        self.file = file
        self.source = source
        self.name = name
        self.mappings = mappings
        self.options = options

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DataLoad):
            return False
        return (
            self.graph == other.graph
            and self.file == other.file
            and self.source == other.source
            and self.name == other.name
            and self.mappings == other.mappings
            and self.options == other.options
        )

    def __hash__(self) -> int:
        return hash(
            (self.graph, self.file, self.source, self.name, self.mappings, self.options)
        )


class Schema:
    name: str
    graphs: list[str]

    def __init__(self, name: str, graphs: list[str]):
        self.name = name
        self.graphs = graphs

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Schema):
            return False
        return self.name == other.name and self.graphs == other.graphs

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.graphs)))


class StoredQuery:
    name: str

    # these are mutually exclusive
    query: str | None
    file: str | None

    options: dict | None = None

    def __init__(
        self,
        name: str,
        query: str | None = None,
        file: str | None = None,
        options: dict | None = None,
    ):
        self.name = name
        self.query = query
        self.file = file
        self.options = options

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, StoredQuery):
            return False
        return (
            self.name == other.name
            and self.query == other.query
            and self.file == other.file
            and self.options == other.options
        )

    def __hash__(self) -> int:
        return hash((self.name, self.query, self.file, self.options))


class DataSource:
    name: str

    options: dict | None = None

    def __init__(self, name: str, options: dict | None = None):
        self.name = name
        self.options = options

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DataSource):
            return False
        return self.name == other.name and self.options == other.options

    def __hash__(self) -> int:
        return hash((self.name, self.options))


class Kit:
    name: str
    group: str
    version: str

    options: dict[str, bool | str | list[str]] | None = None
    sources: list[DataSource] | None = None

    alias: str | None = None

    label: str | None = None
    description: str | None = None

    data: list[DataLoad]
    schemas: list[Schema]
    namespaces: dict[str, str]
    queries: str | list[StoredQuery]

    metadata: dict | None = None
    """User-defined metadata"""

    @property
    def iri(self) -> str:
        return f"tag:stardog:kit:{self.id}"

    @property
    def alias_iri(self) -> str:
        """Return the IRI for the alias of this kit.

        The alias IRI is a named graph alias that contains all of the kit's data"""
        return f"tag:stardog:kit:alias:{(self.alias if self.alias else self.id).replace('.', '_')}"

    @property
    def id(self) -> str:
        return f"{self.group}:{self.name}:{self.version}"

    @staticmethod
    def default_database_name(kit: "Kit") -> str:
        """Return the default database name for a kit.

        This name is used when a kit is installed in a database and
        a database name is not explicitly provided."""
        return f"{kit.group}_{kit.name}_{kit.version.replace('.', '_')}"

    @staticmethod
    def from_file(location: str) -> "Kit":
        """Load a kit from a file or directory."""
        kit_loc = location
        if os.path.isdir(kit_loc):
            kit_loc = os.path.join(kit_loc, "kit.yaml")

        with open(kit_loc, "r") as f:
            return Kit.from_dict(yaml.safe_load(f))

    @staticmethod
    def from_dict(kit_data: dict) -> "Kit":
        name = kit_data["name"]
        group = kit_data.get("group", "stardog")
        version = str(kit_data.get("version", "1.0"))
        label = kit_data.get("label", None)
        description = kit_data.get("description", None)
        data = (
            [
                DataLoad(
                    file=x["file"],
                    graph=x.get("graph", None),
                    mappings=x.get("mappings"),
                )
                for x in kit_data["data"]
            ]
            if "data" in kit_data
            else []
        )
        schemas = (
            [Schema(name=x["name"], graphs=x["graphs"]) for x in kit_data["schemas"]]
            if "schemas" in kit_data
            else []
        )
        namespaces = kit_data.get("namespaces", default_namespaces())
        meta = kit_data.get("metadata", {})
        queries = kit_data.get("queries", [])
        alias = kit_data.get("alias", None)

        options = kit_data.get("options", {})

        sources = kit_data.get("sources", [])

        return Kit(
            name=name,
            group=group,
            version=version,
            label=label,
            description=description,
            data=data,
            schemas=schemas,
            namespaces=namespaces,
            metadata=meta,
            alias=alias,
            queries=queries,
            options=options,
            sources=sources,
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "group": self.group,
            "version": self.version,
            "label": self.label,
            "description": self.description,
            "data": [
                {"file": x.file, "graph": x.graph, "mappings": x.mappings}
                for x in self.data
            ],
            "schemas": [{"name": x.name, "graphs": x.graphs} for x in self.schemas],
            "namespaces": self.namespaces,
            "metadata": self.metadata,
            "queries": self.queries,
            "alias": self.alias,
            "options": self.options,
            "sources": self.sources,
        }

    def __init__(
        self,
        name: str,
        group: str,
        version: str,
        data: list[DataLoad],
        schemas: list[Schema],
        namespaces: dict[str, str],
        queries: str | list[StoredQuery],
        metadata: dict | None = None,
        alias: str | None = None,
        options: dict[str, bool | str | list[str]] | None = None,
        sources: list[DataSource] | None = None,
        label: str | None = None,
        description: str | None = None,
    ):
        self.name = name
        self.group = group
        self.version = version
        self.data = data
        self.schemas = schemas
        self.namespaces = namespaces
        self.queries = queries
        self.metadata = metadata
        self.alias = alias
        self.options = options
        self.sources = sources
        self.label = label
        self.description = description

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Kit):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class KitRepository(abc.ABC):
    """Something that contains kits"""

    @abc.abstractmethod
    def list(self) -> list[tuple[str, str | None, str | None]]:
        pass


class LocalKitRepository(KitRepository):
    def __init__(self, location: str):
        self.location = location

    def list(self) -> list[tuple[str, str | None, str | None]]:
        kits = []
        for root, _, files in os.walk(self.location):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    with open(os.path.join(root, file), "r") as f:
                        kit = Kit.from_dict(yaml.safe_load(f))
                        kits.append((kit.id, kit.label, kit.description))
        return kits


class StardogKitRepository(KitRepository):
    conn_factory: stardog_utils.ConnectionFactory

    def __init__(self, conn_factory: stardog_utils.ConnectionFactory):
        self.conn_factory = conn_factory

    def list(self) -> list[tuple[str, str | None, str | None]]:
        with self.conn_factory.connection() as conn:
            t = []

            results = stardog_utils.SelectQueryResult(conn.select(queries.LIST_KITS))
            for binding in results:
                label = binding.get("ml", None)
                description = binding.get("description", None)
                t.append(
                    (
                        str(binding.id),
                        str(label) if label else None,
                        str(description) if description else None,
                    )
                )
        return t


def get_kit_property(conn: stardog.Connection, kit_id: str, prop: URIRef) -> list[Node]:
    results = stardog_utils.SelectQueryResult(
        conn.select(
            f"SELECT ?v WHERE {{ ?kit {vocabs.Kits.id.n3()} {RDFLiteral(kit_id).n3()} ; {prop.n3()} ?v }}"
        )
    )

    return [b.v for b in results]
