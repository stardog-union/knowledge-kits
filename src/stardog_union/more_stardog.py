import dataclasses
import datetime
import os
import re
from collections import defaultdict
from enum import Enum
from typing import Any
from urllib.parse import urlparse

import rdflib.namespace as NS
import requests
import stardog
import typing_extensions
import uuid
from rdflib import RDF, BNode, Graph
from rdflib import Literal
from rdflib import Literal as RDFLiteral
from rdflib import URIRef
from rdflib.term import IdentifiedNode
from requests import PreparedRequest

from stardog_union import vocabs

SD_DEFAULT_CONTEXT = "tag:stardog:api:context:default"
SD_ALL_CONTEXT = "tag:stardog:api:context:all"
SD_LOCAL_CONTEXT = "tag:stardog:api:context:local"
SD_VIRTUAL_CONTEXT = "tag:stardog:api:context:virtual"

STARDOG_KG_VIRTUAL = URIRef(SD_VIRTUAL_CONTEXT)
STARDOG_KG_ALL = URIRef(SD_ALL_CONTEXT)
STARDOG_KG_LOCAL = URIRef(SD_LOCAL_CONTEXT)

EMPTY_SELECT_RESULT: dict = {"head": {"vars": []}, "results": {"bindings": []}}

SCHEMA_TRIPLE_LIMIT = 10000


class DatabaseOptions(str, Enum):
    """Valid database options for Stardog.
    [Documentation](https://docs.stardog.com/operating-stardog/database-administration/database-configuration#database-options)
    """

    SEARCH_SEMANTIC_INDEX_CONTEXTS_FILTER = "search.semantic.index.contexts.filter"
    SEARCH_SEMANTIC_ENABLED = "search.semantic.enabled"
    """Whether or not semantic (vector similarity) search is enabled for the database
    type:bool"""
    SEARCH_ENABLED = "search.enabled"
    """Whether or not search is enabled for the database
    type: bool"""

    SEARCH_INDEX_CONTEXTS_EXCLUDED = "search.index.contexts.excluded"
    SEARCH_INDEX_CONTEXTS_FILTER = "search.index.contexts.filter"
    REASONING_SCHEMAS = "reasoning.schemas"
    REASONING_SCHEMA_GRAPHS = "reasoning.schema.graphs"
    REASONING_SCHEMA_VERSIONING_ENABLED = "reasoning.schema.versioning.enabled"
    REASONING_PRECOMPUTE_NON_EMPTY_PREDICATES = (
        "reasoning.precompute.non_empty.predicates"
    )

    SECURITY_PROPERTIES_SENSITIVE = "security.properties.sensitive"
    SECURITY_PROPERTIES_SENSITIVE_GROUPS = "security.properties.sensitive.groups"
    SECURITY_MASKING_FUNCTION = "security.masking.function"

    VOICEBOX_ENABLED = "voicebox.enabled"
    VOICEBOX_PREPROCESSORS = "voicebox.preprocessors"

    DATABASE_NAME = "database.name"
    DATABASE_TIME_MODIFICATION = "database.time.modification"


class ConnectionDetails(typing_extensions.TypedDict):  # parent class is per pydantic
    # TODO: probably merge w/ connection factory
    endpoint: str
    """URL to the Stardog endpoint"""

    username: typing_extensions.NotRequired[str]
    """Username to use for authenticating to the endpoint"""

    password: typing_extensions.NotRequired[str]
    """Password to use for authenticating to the endpoint.

    Other string based credentials, ie tokens could be used here."""

    database: str
    """Name of the database to connect to"""

    schema_name: typing_extensions.NotRequired[str]
    """Name of the schema to use"""


class ConnectionFactory(object):  # pragma: no cover
    """A simple factory for creating connections to a Stardog endpoint."""

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def __init__(
        self,
        options: ConnectionDetails,
    ):
        self.options = options

    def __admin_options(self) -> dict:
        admin_options = dict(self.options.copy())
        admin_options.pop("database", "")
        admin_options.pop("schema", "")
        admin_options.pop("schema_name", "")
        return admin_options

    def __connection_options(self) -> dict:
        admin_options = dict(self.options.copy())
        admin_options.pop("schema", "")
        admin_options.pop("schema_name", "")
        return admin_options

    @property
    def schema_name(self) -> str | None:
        return self.options.get("schema_name", None)

    def database(self) -> str | None:
        """Return the database this connection factory will connect to by default for client connections"""
        return self.options.get("database", None)

    def endpoint(self) -> str:
        return self.options["endpoint"]

    def connection(self) -> stardog.Connection:
        """Return a new client connection to the stardog endpoint"""
        return stardog.Connection(**self.__connection_options())

    def admin(self) -> stardog.Admin:
        """Return a new admin connection to the stardog endpoint"""
        return stardog.Admin(**self.__admin_options())

    def new_connection_factory(
        self, database: str, schema: str = "default"
    ) -> "ConnectionFactory":
        """Create a new ConnectionFactory for the same endpoint, but a different database"""
        cd: ConnectionDetails = self.options.copy()
        cd["database"] = database
        cd["schema_name"] = schema
        return ConnectionFactory(options=cd)


def compute_stats(admin: stardog.Admin, db: str):
    admin.client.put(
        f"/admin/databases/{db}/optimize",
        data='{"optimize.statistics": true, "optimize.compact": false, "optimize.vacuum.data"=false}',
        headers={"Content-Type": "application/json"},
    )


def load_graph_from_stardog(
    conn: stardog.Connection, ng: str
) -> Graph:  # pragma: no cover
    g = Graph(bind_namespaces="none")
    g.parse(
        data=conn.graph(
            f"construct {{ ?s ?p ?o }} where {{ graph <{ng}> {{ ?s ?p ?o }}  }}",
            content_type="text/turtle",
        ).decode("UTF-8")
    )
    return g


def load_schema_graph_from_stardog(
    conn: stardog.Connection, ng: str, limit: int = SCHEMA_TRIPLE_LIMIT
) -> Graph:  # pragma: no cover
    g = Graph(bind_namespaces="none")
    g.parse(
        data=conn.graph(
            f"""construct {{ ?s ?p ?o }} from <{ng}> where {{
                {{ values ?type {{ owl:Class rdfs:Class rdf:Property owl:DatatypeProperty owl:ObjectProperty }} 
                ?s ?p ?o . ?s a ?type . filter (!isBLANK(?s) && !isBLANK(?o)) }}
                UNION {{ ?s ?p ?o FILTER (?s = <{ng}>) FILTER(?p = rdfs:comment) }}  
                }}""",
            content_type="text/turtle",
            limit=limit,
        ).decode("UTF-8")
    )
    return g


def get_database_options(admin: stardog.Admin, db: str, *options: str):
    meta = dict([(x, None) for x in options])
    r = admin.client.get(f"/admin/databases/{db}/options").json()
    for k in meta:
        meta[k] = r.get(k, None)
    return meta


def get_default_schema_graphs(
    admin: stardog.Admin, db: str
) -> list[str]:  # pragma: no cover
    """Return the list of graphs that contain the default schema"""
    opts = get_database_options(admin, db, DatabaseOptions.REASONING_SCHEMA_GRAPHS)
    return opts.get(DatabaseOptions.REASONING_SCHEMA_GRAPHS, [SD_LOCAL_CONTEXT])


def get_schema_graphs(
    admin: stardog.Admin, db: str
) -> dict[str, list[str]]:  # pragma: no cover
    """Get all of the schemas and the graphs where they are stored.

    The keys of the dict are the names of the schemas and the values are lists of strs representing
    the IRIs of the named graphs where the schema is stored."""
    opts = get_database_options(admin, db, DatabaseOptions.REASONING_SCHEMAS)
    schema_list: list[str] = opts.get(DatabaseOptions.REASONING_SCHEMAS, [])
    schemas: dict[str, list[str]] = {}
    for pair in schema_list:
        sp = pair.split("=")
        schema_name = sp[0]
        schema_graph = sp[1]
        graphs: list[str] = schemas.get(schema_name, [])
        graphs.append(schema_graph)
        schemas[schema_name] = graphs
    return schemas


def options_string_to_dict(
    pairs: str, split_token=" ", pair_token="="
):  # pragma: no cover
    """Some server properties values are actually collections, but are string encoded for transport. This
    method takes the db property value as a string and returns a standard dict"""

    def __options_string_to_pairs(
        options_as_string: str, split_token=" ", pair_token="="
    ) -> list:  # pragma: no cover
        options = []
        for pair in options_as_string.split(split_token):
            elems = pair.split(pair_token)
            if len(elems) == 2:
                options.append({elems[0]: elems[1]})
        return options

    opts: dict[str, set[str]] = {}
    for e in pairs:
        for pair in __options_string_to_pairs(e, split_token, pair_token):
            for k, v in pair.items():
                if k not in opts:
                    opts[k] = set()
                opts[k].add(v)
    return opts


def dict_to_options_str(
    d: dict, pair_token="=", split_token=chr(2)
):  # pragma: no cover
    """Serializes a standard dict into the string representation expected for the server. Note that the split_token
    in many cases is a non-printable ascii character, `split_token=chr(2)`. This was chosen because it isn't part
    of the value space for the elements stored for the property and is a good char to split on. Change the split
    token if you want something more human readable."""
    newopt = ""
    for k in d.keys():
        for v in d[k]:
            if len(newopt) > 0:
                newopt += split_token
            newopt += "%s%s%s" % (k, pair_token, v)
    return newopt


@dataclasses.dataclass(frozen=True)
class BearerAuth(requests.auth.AuthBase):
    token: str

    def __call__(self, r: PreparedRequest):
        r.headers["Authorization"] = f"bearer {self.token}"
        return r


def json_safe_value(node: IdentifiedNode):
    """Converts an RDF node to a JSON-safe value which is a string except for numerical and boolean literals."""

    value = node.toPython()
    return value if isinstance(value, (str, int, float, bool)) else str(value)


def result_value_to_rdf(
    result_value: dict,
) -> URIRef | Literal | BNode:  # pragma: no cover
    if result_value["type"] == "uri":
        return URIRef(result_value["value"])
    elif result_value["type"] == "literal":
        # todo, lang
        if "datatype" in result_value:
            return Literal(
                result_value["value"], datatype=URIRef(result_value["datatype"])
            )
        else:
            return Literal(result_value["value"], None)
    else:
        return BNode(result_value["value"])


class BindingSet(object):  # pragma: no cover
    """A single row in a set of query results"""

    def vars(self):
        return self.bindings.keys()

    def keys(self):
        return self.bindings.keys()

    def __init__(self, bindings: dict):
        self.bindings = bindings

    def __getattr__(self, item: str):
        if item not in self.vars():
            return None

        return result_value_to_rdf(self.bindings[item])

    def __getitem__(self, key: str):
        if key not in self.vars():
            return None

        return result_value_to_rdf(self.bindings[key])

    def get(self, key: str, default_value=None):
        return (
            default_value
            if key not in self.vars()
            else result_value_to_rdf(self.bindings[key])
        )

    def __iter__(self):
        return self.bindings.keys().__iter__()

    def __str__(self):
        return "{ %s }" % ", ".join(
            [
                "?%s = %s" % (var, str(result_value_to_rdf(self.bindings[var])))
                for var in self.bindings.keys()
            ]
        )

    def to_simple_dict(self):
        return {k: json_safe_value(self[k]) for k in self.vars()}

    def to_list(self):
        return [self[k] for k in self.vars()]


class SelectQueryResult(object):  # pragma: no cover
    """A set of query results"""

    def __init__(self, results: dict):
        self.results = results

    def vars(self) -> list[str]:
        return self.results["head"]["vars"]

    def is_empty(self) -> bool:
        return len(self.results["results"]["bindings"]) == 0

    def __len__(self) -> int:
        return len(self.results["results"]["bindings"])

    def __iter__(self):
        return self.to_list().__iter__()

    def to_list(self):
        return [BindingSet(x) for x in self.results["results"]["bindings"]]


def is_graph_empty(g: Graph) -> bool:
    # The point of this function is to make mocking easier in tests
    return not g


def get_namespaces(admin: stardog.Admin, db: str):
    # getting the DB object is very expensive. making the namespaces call ourselves
    # e.g. db_ns = admin.database(cf.database()).namespaces()
    r = admin.client.get(f"/{db}/namespaces")
    return r.json()["namespaces"]


def get_databases(admin: stardog.Admin) -> list[str]:
    """Retrieves names of all databases."""
    r = admin.client.get("/admin/databases")
    return r.json()["databases"]


def new_graph(cf: ConnectionFactory) -> Graph:
    """Create a new RDF Graph which has the same namespaces as the database"""
    g = Graph(bind_namespaces="none")
    with cf.admin() as admin:
        db_ns = get_namespaces(admin, cf.database() or "catalog")
        for binding in db_ns:
            g.bind(binding["prefix"], binding["name"])
    return g


class StoredQuery(object):  # pragma: no cover
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.description = kwargs.get("description")
        self.query = kwargs.get("query")
        self.database = kwargs.get("database")
        self.creator = kwargs.get("creator")
        self.shared = kwargs.get("shared")
        self.reasoning = kwargs.get("reasoning")
        self.question = kwargs.get("question")

    @staticmethod
    def get_label(sq: "StoredQuery") -> str:
        if sq.question:
            return sq.question[0]

        if sq.description:
            return sq.description

        if sq.query:
            query = str(sq.query)
            if query.startswith("#"):
                return query[1 : query.index("\n")].strip()

        return sq.name

    @staticmethod
    def delete(admin: stardog.Admin, sq: "StoredQuery"):
        admin.client.delete(f"/admin/queries/stored/{sq.name}")


def get_stored_queries(admin: stardog.Admin) -> list[StoredQuery]:  # pragma: no cover
    """Retrieves the stored queries from the Stardog endpoint.

    .. note:: This replicates the functionality of admin.stored_queries() from pystardog
    but with an important code optimization. The pystardog implementation creates an
    extra network call for every stored query to get the query info. This code can be
    removed once pystardog implements a fix for this issue.
    """
    r = admin.client.get("/admin/queries/stored", headers={"Accept": "text/turtle"})
    graph = Graph(bind_namespaces="none")
    rdf = r.content.decode("utf-8")
    graph.parse(data=rdf, format="text/turtle")
    return load_stored_queries(graph)


def get_stored_queries_for_db(
    admin: stardog.Admin, db: str
) -> list[StoredQuery]:  # pragma: no cover
    """Get all of the stored queries for the given database"""
    return list(filter(lambda sq: sq.database == db, get_stored_queries(admin)))


def load_stored_queries(graph: Graph) -> list[StoredQuery]:  # pragma: no cover
    """Create stored queries from their RDF serialization"""
    field_mappings: dict[Any, str] = {
        vocabs.StardogSystem.queryName: "name",
        vocabs.StardogSystem.queryDescription: "description",
        vocabs.StardogSystem.queryString: "query",
        vocabs.StardogSystem.queryDatabase: "database",
        vocabs.StardogSystem.queryCreator: "creator",
        vocabs.StardogSystem.queryCreationDate: "date",
        vocabs.StardogSystem.voiceboxQuestion: "question",
    }
    type_mappings: dict[Any, str] = {
        vocabs.StardogSystem.SharedQuery: "shared",
        vocabs.StardogSystem.ReasoningQuery: "reasoning",
    }

    metadata: dict[Any, dict[str, Any]] = defaultdict(dict)
    for s, p, o in graph:
        if p == RDF.type:
            type_field = type_mappings.get(o)
            if type_field:
                metadata[s][type_field] = True
        else:
            field = field_mappings.get(p)
            if field:
                if p == vocabs.StardogSystem.voiceboxQuestion:
                    metadata[s].setdefault(field, []).append(str(o))
                else:
                    metadata[s][field] = str(o)

    return [StoredQuery(**q) for q in metadata.values()]


def get_label(
    conn: stardog.Connection,
    subj: URIRef,
    label_property: URIRef = vocabs.SD_LABEL,
    lang: str | None = None,
    ng: URIRef = URIRef(SD_LOCAL_CONTEXT),
) -> str | None:  # pragma: no cover
    q = f"""select ?label from {ng.n3()} where {{
        {subj.n3()} {label_property.n3()} ?label .
        {f"filter (lang(?label) = {lang})" if lang else ""}
}}"""

    results = SelectQueryResult(conn.select(q))
    for b in results:
        return str(b["label"])

    return None


def get_types(
    conn: stardog.Connection,
    subj: URIRef,
    ng: URIRef = URIRef(SD_LOCAL_CONTEXT),
) -> list[URIRef]:  # pragma: no cover
    """Return a list of the types of the individual"""

    q = f"""select ?type from {ng.n3()} where {{
        {subj.n3()} a ?type .
}}"""

    results = SelectQueryResult(conn.select(q))
    return [b["type"] for b in results]


def get_comment(
    conn: stardog.Connection,
    subj: URIRef,
    ng: URIRef = URIRef(SD_LOCAL_CONTEXT),
) -> str | None:  # pragma: no cover
    """Return the rdfs:comment for the given entity"""

    q = f"""select ?comment from {ng.n3()} where {{
        {subj.n3()} rdfs:comment ?comment .
}}"""

    results = SelectQueryResult(conn.select(q))
    for b in results:
        return str(b["comment"])

    return None


def sniff_features_from_plan(plan: str) -> set[str]:  # pragma: no cover
    """Given a query plan, return the features used."""
    features = set()
    for m in re.finditer(
        r"^[\s`\-│─+]*([a-zA-Z-]*)\s?[(\[]",
        plan,
        flags=re.IGNORECASE | re.MULTILINE,
    ):
        if m.group(1):
            f = m.group(1)
            if f.find("Join") != -1:
                f = "Join"

            if f not in ["Scan", "Sort", "Restriction"]:
                if "Full-Text" == f:
                    features.add("SEARCH")
                else:
                    features.add(f.upper())
    return features


def sniff_features(
    cf: ConnectionFactory, generated_query: str
) -> set[str]:  # pragma: no cover
    features = set()
    with cf.connection() as c:
        try:
            plan = c.explain(generated_query)
            features.update(sniff_features_from_plan(plan))
        except Exception as e:
            print(repr(e))
            pass
    return features


def store_queries_in_db(
    cf_or_conn: ConnectionFactory | stardog.Admin, generated_queries: str
):
    """Stores the stored queries in the database. Overwrites the queries if already present

    The `generated_queries` should be a Turtle-serialized representation of the stored queries.

    See Also
    --------
    StoredQuerySerializer : Utility for creating the RDF graph of stored queries to be used for serialization
    """

    if isinstance(cf_or_conn, ConnectionFactory):
        with cf_or_conn.admin() as admin:
            admin.client.put(
                "/admin/queries/stored",
                data=generated_queries,
                headers={"Accept": "application/json", "Content-Type": "text/turtle"},
            )
    else:
        cf_or_conn.client.put(
            "/admin/queries/stored",
            data=generated_queries,
            headers={"Accept": "application/json", "Content-Type": "text/turtle"},
        )


class StoredQuerySerializer:
    """Utility class for serializing a set of queries as RDF using the Stardog Stored Query vocabulary

    See Also
    --------
    stardog.union.vocabs.StardogSystem : Stardog System Vocabulary
    store_queries_in_db : Utility method for storing the RDF created by this class
    """

    prefix: str
    """Default prefix used for creating IRIs for stored queries"""

    database: str
    """The default database stored queries are owned by"""

    username: str | None
    """The user to consider as the creator of the stored queries.

    When not set, the creator of the query will not be specified."""

    graph: Graph
    """The serialized graph of stored queries"""

    def __init__(self, database: str, username: str | None = None):
        self.database = database
        self.username = username
        self.prefix = vocabs.StardogSystem._NS
        self.graph = Graph(bind_namespaces="none")

        nsm = NS.NamespaceManager(Graph())
        nsm.bind("rdf", NS.RDF)
        nsm.bind("rdfs", NS.RDFS)
        nsm.bind("stardog", "tag:stardog:api:")
        nsm.bind("system", self.prefix)

        self.graph.namespace_manager = nsm

    def update_graph(
        self, query: str, name: str, questions: list[str], database: str | None = None
    ):
        """Add a new stored query to the graph

        :param query: the SPARQL query to store
        :param name: the display label for the query
        :param questions: a set of natural language labels for this query. These are indexed by Voicebox.
        :param database: the database that will own this stored query. When specified, this overrides the default
        """

        iri = URIRef(self.prefix + name.replace(" ", "_"))

        self.graph.add((iri, RDF.type, vocabs.StardogSystem.StoredQuery))
        self.graph.add((iri, RDF.type, vocabs.StardogSystem.SharedQuery))
        self.graph.add((iri, vocabs.StardogSystem.queryName, RDFLiteral(name)))
        self.graph.add((iri, vocabs.StardogSystem.queryString, RDFLiteral(query)))

        self.graph.add(
            (
                iri,
                vocabs.StardogSystem.queryDatabase,
                RDFLiteral(database if database else self.database),
            )
        )
        self.graph.add(
            (
                iri,
                vocabs.StardogSystem.queryCreationDate,
                RDFLiteral(datetime.datetime.now()),
            )
        )
        self.graph.add(
            (
                iri,
                vocabs.StardogSystem.queryDescription,
                RDFLiteral(questions[0]) if questions else RDFLiteral(name),
            )
        )

        if self.username:
            self.graph.add(
                (
                    iri,
                    vocabs.StardogSystem.queryCreator,
                    RDFLiteral(self.username),
                )
            )

        for question in questions:
            self.graph.add(
                (
                    iri,
                    vocabs.StardogSystem.voiceboxQuestion,
                    RDFLiteral(question),
                )
            )


def import_file(
    admin: stardog.Admin,
    db: str,
    mappings,
    input_file,
    opts: dict | None = None,
    named_graph: str | None = None,
):
    """Import a JSON or CSV file.

    Args:
        db (str): Name of the database to import the data
        mappings (MappingRaw or MappingFile): New mapping contents.
        input_file(ImportFile or ImportRaw):
        options (dict, Optional): Options for the new csv import.
        named_graph (str, Optional): The namegraph to associate it too

    Returns:
        r.ok

    Examples:
        >>> admin.import_file(
                'mydb', File('mappings.ttl'),
                'test.csv'
            )
    """

    # TODO why copied from pystardog?

    options = dict(opts) if opts else {}

    if mappings is not None:
        if mappings.syntax:
            options["mappings.syntax"] = mappings.syntax

        with mappings.data() as data:
            if hasattr(data, "read"):
                r = data.read()
                mappings = r.decode() if hasattr(r, "decode") else r
            else:
                mappings = data

    if input_file is not None:
        if input_file.separator:
            options["csv.separator"] = input_file.separator

    payload = {"database": db, "mappings": mappings}

    if options is not None:
        payload["options"] = "\n".join(["%s=%s" % (k, v) for (k, v) in options.items()])
    else:
        payload["options"] = ""

    if named_graph is not None:
        payload["named_graph"] = named_graph

    payload["input_file_type"] = input_file.input_type
    payload["input_file_iri"] = f"uuid:{uuid.uuid4()}"

    with input_file.data() as data:
        r = admin.client.post(
            "/admin/virtual_graphs/import",
            data=payload,
            files={
                "input_file": (
                    input_file.name,
                    data,
                    input_file.content_type,
                    input_file.content_encoding,
                )
            },
        )

    return r.ok


class PasswordEntry:
    """
    Entry in a Stardog password file. Details at
    https://docs.stardog.com/operating-stardog/security/managing-users-and-roles#password-file-format
    """

    def __init__(self, line: str):
        args = line.strip().split(":")
        if len(args) != 5:
            raise ValueError(f"Password file contains invalid entry: {line}")
        self.host = args[0]
        self.port = -1 if args[1] == "*" else int(args[1])
        self.db = args[2]
        self.user = args[3]
        self.passwd = args[4]

    def get_credentials(self, host, port, db, user) -> tuple[str, str] | None:
        matches = (
            (self.host == "*" or self.host == host)
            and (self.port == -1 or self.port == port)
            and (self.db == "*" or self.db == db or db is None)
            and (self.user == "*" or self.user == user or user is None)
        )
        return (user if user else self.user, self.passwd) if matches else None


def get_password_file_credentials(endpoint, db=None, username=None) -> tuple[str, str]:
    parsed_url = urlparse(endpoint)
    entries = get_all_credentials()
    try:
        return next(
            filter(
                None,
                (
                    e.get_credentials(
                        parsed_url.hostname, parsed_url.port, db, username
                    )
                    for e in entries
                ),
            )
        )
    except StopIteration:
        return None


def get_all_credentials() -> list[PasswordEntry]:
    try:
        with open(os.path.expanduser("~/.sdpass")) as passwd_file:
            return [
                PasswordEntry(line)
                for line in passwd_file.readlines()
                if not line.startswith("#")
            ]
    except FileNotFoundError:
        return []
