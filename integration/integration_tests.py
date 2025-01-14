import os

import pytest

from stardog_union import more_stardog as stardog_utils
from stardog_union.kits import install, uninstall
from stardog_union.kits.base import DataLoad, Kit, StardogKitRepository, StoredQuery


@pytest.fixture
def connection_factory() -> stardog_utils.ConnectionFactory:
    return stardog_utils.ConnectionFactory(
        stardog_utils.ConnectionDetails(
            endpoint=os.getenv("STARDOG_INTERNAL_ENDPOINT", "http://localhost:5820"),
            database=os.getenv("STARDOG_INTERNAL_DATABASE", "testDb"),
            username=os.getenv("STARDOG_INTERNAL_USERNAME", "admin"),
            password=os.getenv("STARDOG_INTERNAL_PASSWORD", "admin"),
        )
    )


@pytest.fixture
def simple_kit() -> Kit:
    return Kit.from_file("examples/starwars")


@pytest.fixture
def installed_kit(connection_factory: stardog_utils.ConnectionFactory, simple_kit: Kit):
    install.install_kit(connection_factory, simple_kit, local_dir="examples/starwars")
    try:
        yield simple_kit
    finally:
        uninstall.uninstall_kit(connection_factory, simple_kit.id, clean_database=True)


@pytest.fixture
def queries_file_kit() -> Kit:
    return Kit(
        name="queries-file-kit",
        group="test",
        version="1.0.0",
        data=[],  # No data needed for this test
        schemas=[],  # No schemas needed for this test
        namespaces={},  # Using empty namespaces for this test
        queries="queries.ttl",  # File-based queries
    )


@pytest.fixture
def queries_direct_kit() -> Kit:
    return Kit(
        name="queries-direct-kit",
        group="test",
        version="1.0.0",
        data=[],
        schemas=[],
        namespaces={},
        queries=[
            StoredQuery(
                name="direct_query1", query="SELECT ?s WHERE { ?s a <urn:test:Class> }"
            ),
            StoredQuery(name="direct_query2", file="query2.rq"),
        ],
    )


def test_install_kit_integration(
    connection_factory: stardog_utils.ConnectionFactory, simple_kit: Kit
):
    repo = StardogKitRepository(connection_factory)

    install.install_kit(
        conn_factory=connection_factory, kit=simple_kit, local_dir="examples/starwars"
    )

    graphs = [g for g in filter(lambda x: x, [data.graph for data in simple_kit.data])]

    assert simple_kit.id in [id for id, _, _ in repo.list()]
    for graph in graphs:
        with connection_factory.connection() as conn:
            query = f"ASK {{ GRAPH <{graph}> {{ }} }}"
            assert conn.ask(query)

    uninstall.uninstall_kit(connection_factory, simple_kit.id, clean_database=True)

    with connection_factory.admin() as admin:
        assert Kit.default_database_name(simple_kit) not in stardog_utils.get_databases(
            admin
        )


def test_install_kit_with_file_queries(
    connection_factory: stardog_utils.ConnectionFactory, queries_file_kit: Kit
):
    try:
        install.install_kit(
            conn_factory=connection_factory,
            kit=queries_file_kit,
            local_dir="tests/resources/kits/queries-file-kit",
        )

        # Verify queries were installed
        with connection_factory.admin() as admin:
            stored_queries = stardog_utils.get_stored_queries(admin)
            query_names = {sq.name for sq in stored_queries}
            print(query_names)
            assert "file_query_1" in query_names
            assert "file_query_2" in query_names

    finally:
        uninstall.uninstall_kit(
            connection_factory, queries_file_kit.id, clean_database=True
        )


def test_uninstall_kit_with_file_queries(
    connection_factory: stardog_utils.ConnectionFactory, queries_file_kit: Kit
):
    try:
        install.install_kit(
            conn_factory=connection_factory,
            kit=queries_file_kit,
            local_dir="tests/resources/kits/queries-file-kit",
        )

        # Verify queries were installed
        with connection_factory.admin() as admin:
            stored_queries = stardog_utils.get_stored_queries(admin)
            query_names = {sq.name for sq in stored_queries}
            assert "file_query_1" in query_names
            assert "file_query_2" in query_names

        # Now uninstall
        uninstall.uninstall_kit(connection_factory, queries_file_kit.id)

        # Verify queries were removed
        with connection_factory.admin() as admin:
            stored_queries = stardog_utils.get_stored_queries(admin)
            query_names = {sq.name for sq in stored_queries}
            assert "file_query_1" not in query_names
            assert "file_query_2" not in query_names

    finally:
        # Cleanup in case test fails
        uninstall.uninstall_kit(
            connection_factory, queries_file_kit.id, clean_database=True
        )


def test_uninstall_kit_with_direct_queries(
    connection_factory: stardog_utils.ConnectionFactory, queries_direct_kit: Kit
):
    try:
        install.install_kit(
            conn_factory=connection_factory,
            kit=queries_direct_kit,
            local_dir="tests/resources/kits/queries-direct-kit",
        )

        db_name = connection_factory.database()
        expected_queries = {f"{db_name}_direct_query1", f"{db_name}_direct_query2"}

        # Verify queries were installed
        with connection_factory.admin() as admin:
            stored_queries = stardog_utils.get_stored_queries(admin)
            query_names = {sq.name for sq in stored_queries}
            assert expected_queries.issubset(query_names)

        # Now uninstall
        uninstall.uninstall_kit(connection_factory, queries_direct_kit.id)

        # Verify queries were removed
        with connection_factory.admin() as admin:
            stored_queries = stardog_utils.get_stored_queries(admin)
            query_names = {sq.name for sq in stored_queries}
            assert not expected_queries.intersection(query_names)

    finally:
        # Cleanup in case test fails
        uninstall.uninstall_kit(
            connection_factory, queries_direct_kit.id, clean_database=True
        )


def test_install_kit_with_url_data(connection_factory: stardog_utils.ConnectionFactory):
    # Mock the HTTP request

    kit = Kit(
        name="url-data-kit",
        group="test",
        version="1.0.0",
        data=[
            DataLoad(
                file="https://raw.githubusercontent.com/stardog-union/stardog-examples/refs/heads/develop/examples/python-client/sdclient/resources/GettingStarted_Music_Data.ttl",  # noqa: E501
                graph="http://example.com/music",
            )
        ],
        schemas=[],
        namespaces={},
        queries=[],
    )

    try:
        install.install_kit(conn_factory=connection_factory, kit=kit)

        with connection_factory.connection() as conn:
            query = """
            ASK { 
                GRAPH <http://example.com/music> { 
                    ?s ?p ?o 
                }
            }
            """
            assert conn.ask(query), "Graph should contain data after installation"

    finally:
        uninstall.uninstall_kit(connection_factory, kit.id, clean_database=True)


def test_install_kit_with_invalid_url(
    connection_factory: stardog_utils.ConnectionFactory,
):
    kit = Kit(
        name="invalid-url-kit",
        group="test",
        version="1.0.0",
        data=[
            DataLoad(
                file="https://raw.githubusercontent.com/nonexistent/invalid.ttl",
                graph="http://example.com/nonexistent",
            )
        ],
        schemas=[],
        namespaces={},
        queries=[],
    )

    with pytest.raises(Exception):
        install.install_kit(conn_factory=connection_factory, kit=kit)

    # Verify the graph wasn't created
    with connection_factory.connection() as conn:
        query = """
        ASK { 
            GRAPH <http://example.com/nonexistent> { 
                ?s ?p ?o 
            }
        }
        """
        assert not conn.ask(query), "Graph should not exist after failed installation"
