import datetime
import hashlib
import itertools
import logging
import os
import uuid
from typing import Any

import tqdm
from rdflib import DCAT, DCTERMS, PROV, RDF, RDFS, XSD, Graph
from rdflib import Literal as RDFLiteral
from rdflib import URIRef
from stardog import Admin, Connection, content, content_types

from stardog_union import more_stardog as stardog_utils
from stardog_union import vocabs
from stardog_union.kits import exceptions, queries
from stardog_union.kits import utils as kit_utils
from stardog_union.kits.base import DataLoad, Kit
from stardog_union.more_stardog import (
    ConnectionFactory,
    DatabaseOptions,
    dict_to_options_str,
    import_file,
    options_string_to_dict,
)

LOG = logging.getLogger(__name__)


def get_file_prov(dir_name: str, user: str, data_file: DataLoad) -> Graph:
    """Generate PROV-O metadata for a file import"""

    file_to_load = (
        data_file.file
        if os.path.isabs(data_file.file)
        else dir_name + os.sep + data_file.file
    )
    _csv = URIRef("http://www.iana.org/assignments/media-types/text/csv")
    import_activity = URIRef("urn:uuid:" + str(uuid.uuid4()))
    now = datetime.datetime.now().replace(microsecond=0).isoformat()
    input_iri = URIRef("urn:file:" + kit_utils.hash_file(file_to_load))

    user_iri = URIRef(user)

    graph_ref = URIRef(data_file.graph) if data_file.graph else None

    prov_data = [
        (input_iri, RDF.type, PROV.Entity),
        (input_iri, RDF.type, DCAT.Distribution),
        (input_iri, DCTERMS.format, _csv),
        (
            input_iri,
            DCAT.byteSize,
            RDFLiteral(os.path.getsize(file_to_load), datatype=XSD.decimal),
        ),
        (
            input_iri,
            RDFS.label,
            RDFLiteral(os.path.basename(file_to_load)),
        ),
        (user_iri, RDF.type, PROV.Agent),
        (
            import_activity,
            RDF.type,
            PROV.Activity,
        ),
        (
            import_activity,
            PROV.wasAssociatedWith,
            user_iri,
        ),
        (
            import_activity,
            PROV.endedAtTime,
            RDFLiteral(now, datatype=XSD.dateTime),
        ),
        (import_activity, PROV.used, input_iri),
    ]
    if graph_ref:
        prov_data.extend(
            [
                (graph_ref, RDF.type, PROV.Entity),
                (graph_ref, RDF.type, DCAT.Dataset),
                (graph_ref, DCAT.distribution, input_iri),
                (
                    graph_ref,
                    PROV.wasGeneratedBy,
                    import_activity,
                ),
                (
                    graph_ref,
                    PROV.generatedAtTime,
                    RDFLiteral(now, datatype=XSD.dateTime),
                ),
                (graph_ref, PROV.wasAttributedTo, user_iri),
                (
                    import_activity,
                    PROV.generated,
                    graph_ref,
                ),
            ]
        )

    if data_file.mappings:
        mapping_activity = URIRef("urn:uuid:" + str(uuid.uuid4()))
        mappings_file = (
            data_file.mappings
            if os.path.isabs(data_file.mappings)
            else dir_name + os.sep + data_file.mappings
        )
        mappings_iri = URIRef("urn:file:" + kit_utils.hash_file(mappings_file))

        prov_data.extend(
            [
                (
                    mapping_activity,
                    RDF.type,
                    PROV.Activity,
                ),
                (
                    mapping_activity,
                    PROV.endedAtTime,
                    RDFLiteral(now, datatype=XSD.dateTime),
                ),
                (
                    mapping_activity,
                    PROV.wasAssociatedWith,
                    user_iri,
                ),
                (
                    mapping_activity,
                    PROV.used,
                    mappings_iri,
                ),
                (
                    mappings_iri,
                    RDF.type,
                    PROV.Entity,
                ),
            ]
        )
        if graph_ref:
            prov_data.extend(
                [
                    (
                        graph_ref,
                        PROV.wasGeneratedBy,
                        mapping_activity,
                    )
                ]
            )
    meta = Graph(bind_namespaces="none")
    for t in prov_data:
        meta.add(t)
    return meta


def get_kit_meta(kit: Kit, base_iri: str = "tag:stardog:marketplace:") -> Graph:
    """Turn a Kit definition into RDF.

    This does not install the kit or include any of the data in the kit, this
    only includes the metadata _about_ the kit, which can later be used for
    kit management."""

    g = Graph(bind_namespaces="none")
    for prefix in kit.namespaces:
        g.namespace_manager.bind(prefix, kit.namespaces[prefix])

    iri = base_iri + kit.id
    kit_iri = URIRef(iri)

    g.add((kit_iri, RDF.type, vocabs.Kits.KnowledgeKit))
    g.add((kit_iri, RDF.type, vocabs.Kits.Module))

    g.add((kit_iri, vocabs.Kits.id, RDFLiteral(kit.id)))

    g.add((kit_iri, RDFS.label, RDFLiteral(kit.label if kit.label else kit.id)))

    if kit.description:
        g.add((kit_iri, RDFS.comment, RDFLiteral(kit.description)))

    g.add(
        (
            kit_iri,
            DCTERMS.modified,
            RDFLiteral(
                datetime.datetime.now().replace(microsecond=0).isoformat(),
                datatype=XSD.dateTime,
            ),
        )
    )

    schema_graphs = [y for x in kit.schemas for y in x.graphs]
    data_graphs = [
        x.graph
        for x in filter(
            lambda data: data.graph and data.graph not in schema_graphs, kit.data
        )
    ]

    if kit.sources:
        for source in kit.sources:
            source_node = URIRef("urn:uuid:" + str(uuid.uuid4()))
            g.add((kit_iri, vocabs.Kits.hasSource, source_node))
            g.add((source_node, RDFS.label, RDFLiteral(source.name)))

    for schema in kit.schemas:
        schema_node = URIRef("urn:uuid:" + str(uuid.uuid4()))
        g.add((kit_iri, vocabs.Kits.hasSchema, schema_node))
        g.add((schema_node, RDF.type, vocabs.Kits.DataModel))
        for gr in schema.graphs:
            g.add((schema_node, vocabs.Kits.model, URIRef(gr)))
        if schema.name:
            g.add((schema_node, RDFS.label, RDFLiteral(schema.name)))

    for graph in data_graphs:
        g.add((kit_iri, vocabs.Kits.data, URIRef(graph)))

    return g


def install_namespaces(admin: Admin, database: str, namespaces: dict[str, Any]):
    """Install namespaces into a database on a Stardog endpoint"""
    the_db = admin.database(database)
    curr_ns = {}
    for elem in the_db.namespaces():
        curr_ns[elem["prefix"]] = elem["name"]

    for pre in namespaces:
        if pre not in curr_ns:
            the_db.add_namespace(pre, namespaces[pre])


def install_data_virtual_import_static(
    admin: Admin, database: str, load: DataLoad, local_dir: str | None = None
):
    """Install a virtual graph from a kit into the database on a Stardog endpoint"""
    dir_name = local_dir if local_dir else os.getcwd()

    mappings_file = (
        load.mappings
        if os.path.isabs(load.mappings)
        else dir_name + os.sep + load.mappings
    )
    vg_name = load.name if load.name else os.path.basename(mappings_file)

    if load.source not in [ds.name for ds in admin.datasources()]:
        raise exceptions.InvalidDataSource(load.source)

    options = {"mappings.syntax": "SMS2"}
    if load.options:
        options.update(load.options)

    # TODO verify vg doesn't exist before adding
    # TODO error handling
    LOG.info("Adding virtual graph %s", vg_name)

    admin.new_virtual_graph(
        vg_name,
        content.MappingFile(mappings_file, "SMS2"),
        options=options,
        datasource=load.source,
        db=database,
    )


def install_data_local(
    conn: Connection,
    admin: Admin,
    database: str,
    load: DataLoad,
    local_dir: str | None = None,
):
    """Install a static file from a kit into the database on a Stardog endpoint"""
    dir_name = local_dir if local_dir else os.getcwd()

    file_to_load = (
        load.file if os.path.isabs(load.file) else dir_name + os.path.sep + load.file
    )

    if load.mappings:
        # virtual import of csv/json

        options = load.options if load.options else {}
        ng = load.graph if load.graph else "tag:stardog:api:context:default"

        mappings = (
            load.mappings
            if os.path.isabs(load.mappings)
            else dir_name + os.sep + load.mappings
        )
        input_file = (
            load.file
            if os.path.isabs(load.file)
            else dir_name + os.path.sep + load.file
        )

        LOG.info(
            "Importing virtual data from %s using %s into graph %s",
            input_file,
            mappings,
            ng,
        )
        is_json = os.path.splitext(input_file)[1] == ".json"

        sep = options["csv.separator"] if "csv.separator" in options else ","

        import_file(
            admin,
            database,
            content.MappingFile(mappings, "SMS2"),
            content.ImportFile(
                input_file, "JSON" if is_json else "DELIMITED", separator=sep
            ),
            opts=options,
            named_graph=ng,
        )
    else:
        LOG.info("Adding file %s" % file_to_load)
        conn.add(content.File(file_to_load), graph_uri=load.graph)


def install_data(
    conn: Connection,
    admin: Admin,
    database,
    kit: Kit,
    local_dir: str | None = None,
    pbar: tqdm.tqdm | None = None,
):
    # TODO rollback danger alert!! if one of these imports fails the txn will correctly abort
    # but if any succeeded prior to the failure, they will remain. we can hackily execute
    # a second txn to clean those graphs up. if platform would move file import (csv/json)
    # into the core database path, then we get transactions for free?

    for load in kit.data:
        if load.file:
            if pbar:
                pbar.desc = f"Loading data from {load.file}"
            # TODO: better switch for this case
            if load.source:
                install_data_virtual_import_static(
                    conn, database, load, local_dir=local_dir
                )
            elif load.file:
                install_data_local(conn, admin, database, load, local_dir=local_dir)
            else:
                # TODO: error?
                LOG.warning(
                    "Unknown data entry, does not appear to be a valid file or virtual mapping"
                )
        if pbar:
            pbar.update(1)


def install_schemas(admin: Admin, database: str, kit: Kit):
    LOG.info("Installing schema definitions...")

    schemas = options_string_to_dict(
        admin.database(database).get_options(DatabaseOptions.REASONING_SCHEMAS)[
            DatabaseOptions.REASONING_SCHEMAS
        ]
    )

    for schema in kit.schemas:
        graphs = schema.graphs
        if schema.name in schemas:
            graphs = list(itertools.chain(schema.graphs, schemas[schema.name]))

        schemas[schema.name] = graphs

    LOG.info("Saving schema definitions...")

    admin.database(database).set_options(
        {
            DatabaseOptions.REASONING_SCHEMAS: dict_to_options_str(
                schemas, split_token=chr(2)
            )
        }
    )


def load_stored_queries_from_file(admin: Admin, kit: Kit, local_dir: str | None = None):
    dir_name = local_dir if local_dir else os.getcwd()
    file_to_load: str = (
        kit.queries
        if os.path.isabs(kit.queries)
        else dir_name + os.path.sep + kit.queries
    )

    with open(file_to_load, "r") as f:
        sq_data = f.read()

    admin.client.put(
        "/admin/queries/stored",
        data=sq_data,
        headers={"Accept": "application/json", "Content-Type": "text/turtle"},
    )


def install_stored_queries(
    admin: Admin, database: str, kit: Kit, local_dir: str | None = None
):
    def to_str(file: str) -> str:
        with open(file, "r") as f:
            return f.read()

    dir_name = local_dir if local_dir else os.getcwd()

    if isinstance(kit.queries, str):
        load_stored_queries_from_file(admin, kit, local_dir=local_dir)
    else:
        # this is fastest way to get sq's from Stardog
        # TODO: utils from vbx would be great here.
        sqs = [sq.name for sq in admin.stored_queries()]
        for sq in kit.queries:
            if sq.name not in sqs:
                opts = sq.options if sq.options else {}
                query = (
                    sq.query
                    if sq.query
                    else to_str(dir_name + os.sep + sq.file)
                    if sq.file
                    else None
                )

                if not query:
                    # TODO: error?
                    LOG.warning(
                        "Unable to add stored query %s, no query was specified.",
                        sq.name,
                    )

                opts["database"] = database
                opts["shared"] = opts["shared"] if "shared" in opts else True

                LOG.info("Adding stored query %s" % sq["name"])
                admin.new_stored_query(f"{database}_{sq['name']}", query, opts)


def install_provenance(
    conn: Connection, user: str, kit: Kit, local_dir: str | None = None
):
    dir_name = local_dir if local_dir else os.getcwd()
    g = Graph(bind_namespaces="none")
    for data in kit.data:
        prov = get_file_prov(dir_name, user, data)
        for t in prov:
            g.add(t)

    conn.add(content.Raw(g.serialize(), content_types.TURTLE), graph_uri=kit.iri)


def install_metadata(conn: Connection, kit: Kit, local_dir: str | None = None):
    """Install metadata about the kit into the Stardog endpoint"""
    kit_dir = local_dir if local_dir else os.getcwd()
    meta = get_kit_meta(kit)
    if os.path.isfile(kit_dir + os.path.sep + "readme.md"):
        with open(kit_dir + os.path.sep + "readme.md", "r") as f:
            s = f.read()
        meta.add((next(meta.subjects()), vocabs.Kits.readme, RDFLiteral(s)))

    conn.add(content.Raw(meta.serialize(), content_types.TURTLE), graph_uri=kit.iri)


def create_kit_database(admin: Admin, db_name: str, kit: Kit):
    def xform_options(opts):
        new_opts = {}
        for key in opts:
            v = opts[key]
            # todo: this is not a very sophisticated check to see if the option is a list and therefore
            # if it should be encoded correctly before sending over to the server
            if isinstance(v, str) and " " in v:
                v = v.replace(" ", chr(2))
            new_opts[key] = v
        return new_opts

    opts = kit.options if kit.options else {}

    opts["database.namespaces"] = ",".join(
        [f"{k}={v}" for k, v in kit.namespaces.items()]
    )

    admin.new_database(db_name, options=xform_options(opts))


def install_kit(
    conn_factory: ConnectionFactory,
    kit: Kit,
    local_dir: str | None = None,
    show_progress: bool = False,
):
    """Install a kit

    :param local_dir: local directory where kit assets will be found. If not specified, cwd is used.
    """

    with conn_factory.admin() as admin:
        database = conn_factory.database()

        if not database or database not in stardog_utils.get_databases(admin):
            create_kit_database(admin, database, kit)
        else:
            LOG.info("Database %s already exists, skipping creation", database)
            # TODO: verify the database we're installing to has compatible properties

        with conn_factory.connection() as conn:
            user = os.getenv(
                "user",
                "urn:agent:"
                + hashlib.sha1(
                    conn_factory.options.get(
                        "username", os.getenv("USERNAME", "admin")
                    ).encode("utf-8")
                ).hexdigest(),
            )

            conn.begin()
            try:

                def update_status(desc: str | None = None):
                    if pbar:
                        pbar.update(1)
                        if desc:
                            pbar.desc = desc

                pbar = (
                    tqdm.tqdm(
                        desc="Loading Knowledge Kit into Stardog Endpoint",
                        total=6 + len(kit.data),
                    )
                    if show_progress
                    else None
                )

                install_namespaces(admin, database, kit.namespaces)

                update_status("Installing data")
                install_data(conn, admin, database, kit, local_dir=local_dir, pbar=pbar)

                update_status("Installing schemas")
                install_schemas(admin, database, kit)

                update_status("Installing stored queries")
                install_stored_queries(admin, database, kit, local_dir=local_dir)

                update_status("Installing provenance")
                install_provenance(conn, user, kit, local_dir=local_dir)

                update_status("Installing metadata")
                install_metadata(conn, kit, local_dir=local_dir)

                graphs = set(filter(lambda x: x, [data.graph for data in kit.data]))

                if graphs:
                    conn.update(
                        queries.INSERT_ALIAS.format(
                            alias_iri=f"<{kit.alias_iri}>",
                            aliases=",".join(["<%s>" % a for a in graphs]),
                        )
                    )

                update_status("Finalizing installation")

                conn.commit()

                return
            except Exception as e:
                conn.rollback()
                raise e
