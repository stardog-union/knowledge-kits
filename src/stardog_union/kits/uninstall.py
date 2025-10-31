import logging

import tqdm

from stardog_union import more_stardog as stardog_utils
from stardog_union import vocabs
from stardog_union.kits import base, queries, utils

LOG = logging.getLogger(__name__)


def uninstall_property_groups(
    conn_factory: stardog_utils.ConnectionFactory, kit_id: str
):
    db = conn_factory.database()
    sec = []

    with conn_factory.connection() as conn:
        for model_graph in utils.get_schema_graphs(conn, kit_id):
            results = stardog_utils.SelectQueryResult(
                conn.select(
                    queries.SEC_PROPERTY_GROUPS.format(
                        schema_graph="<%s>" % model_graph
                    )
                )
            )
            for b in results:
                sec.append({str(b.groupid): str(b.property)})

    if sec:
        with conn_factory.admin() as admin:
            pgroups = stardog_utils.options_string_to_dict(
                admin.database(db).get_options(
                    stardog_utils.DatabaseOptions.SECURITY_PROPERTIES_SENSITIVE_GROUPS
                )[stardog_utils.DatabaseOptions.SECURITY_PROPERTIES_SENSITIVE_GROUPS]
            )
            for pair in sec:
                for k, v in pair.items():
                    if k in pgroups:
                        pgroups[k].remove(v)

            admin.database(db).set_options(
                {
                    stardog_utils.DatabaseOptions.SECURITY_PROPERTIES_SENSITIVE_GROUPS: stardog_utils.dict_to_options_str(
                        pgroups, split_token=chr(2)
                    )
                }
            )


def uninstall_schemas(
    conn_factory: stardog_utils.ConnectionFactory, kit_schemas: list[str]
):
    db = conn_factory.database()
    with conn_factory.admin() as admin:
        stardog_db = admin.database(db)
        opts = stardog_db.get_options(stardog_utils.DatabaseOptions.REASONING_SCHEMAS)[
            stardog_utils.DatabaseOptions.REASONING_SCHEMAS
        ]
        schemas = stardog_utils.options_string_to_dict(opts)
        for sn in kit_schemas:
            if sn in schemas:
                schemas.pop(sn)

        stardog_db.set_options(
            {
                stardog_utils.DatabaseOptions.REASONING_SCHEMAS: stardog_utils.dict_to_options_str(
                    schemas, split_token=chr(2)
                )
            }
        )


def uninstall_kit(
    conn_factory: stardog_utils.ConnectionFactory,
    kit_id: str,
    clean_database: bool = False,
    clean_datasources: bool = False,
    show_progress: bool = False,
):
    if not conn_factory or not kit_id:
        raise ValueError("conn_factory and kit_id are required")

    def update_status(desc: str | None = None, count: int = 0):
        if pbar and count:
            pbar.update(count)
        if pbar and desc:
            pbar.desc = desc

    with conn_factory.admin() as admin:
        db = conn_factory.database()

        db_exists = db in stardog_utils.get_databases(admin)

        if db_exists:
            LOG.info("Deleting db %s", db)

            stored_queries = stardog_utils.get_stored_queries_for_db(admin, db)

            pbar = (
                tqdm.tqdm(
                    desc="Uninstalling Knowledge Kit into Stardog Endpoint",
                    total=4 + len(stored_queries),
                )
                if show_progress
                else None
            )

            update_status("Dropping Stored Queries")
            for sq in stored_queries:
                LOG.info("Deleting stored query %s" % sq.name)
                stardog_utils.StoredQuery.delete(admin, sq)
                update_status(count=1)

            with conn_factory.connection() as conn:
                conn.begin()

                update_status("Uninstalling Schemas", count=1)
                uninstall_schemas(conn_factory, utils.get_schema_names(conn, kit_id))

                update_status(desc="Uninstalling Property Groups", count=1)
                uninstall_property_groups(conn_factory, kit_id)

                update_status("Removing Graphs")
                graphs = utils.get_graphs_list(conn, kit_id)

                if graphs:
                    conn.update(";\n".join(["clear graph <%s>" % g for g in graphs]))

                    alias_iri = base.get_kit_property(conn, kit_id, vocabs.Kits.alias)

                    if alias_iri:
                        conn.update(queries.DELETE_ALIAS.format(alias_iri=alias_iri[0]))

                conn.commit()

                update_status(count=1)

            if clean_datasources:
                pass
            #     for n in [src['name'] for src in self.project_file["sources"]]:
            #         admin.datasource(n).delete()

            if clean_database:
                LOG.info("Dropping database")

                update_status("Dropping Database")

                admin.database(db).drop()

            update_status(count=1)
            return True
        else:
            return False
