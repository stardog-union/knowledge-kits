from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from rdflib import Graph

from stardog_union import more_stardog as stardog_utils
from stardog_union.kits import install, uninstall
from stardog_union.kits.base import Kit, StoredQuery

from .test_kits import connection_factory_mock, simple_kit

# NOTE: marking these as used for mypy
connection_factory_mock
simple_kit


def test_uninstall_unknown_db(
    mocker: MockerFixture,
    connection_factory_mock: stardog_utils.ConnectionFactory,
    simple_kit: Kit,
):
    dbs = ["not_a_db"]
    schema_names = ["not_a_schema"]
    mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.get_databases", return_value=dbs
    )

    get_stored_queries_for_db = mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.get_stored_queries_for_db",
        return_value=[],
    )

    options_string_to_dict = mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.options_string_to_dict"
    )

    # set_options = mocker.patch("stardog.admin.Database.set_options")

    mocker.patch("stardog_union.kits.utils.get_schema_names", return_value=schema_names)
    get_schema_graphs = mocker.patch(
        "stardog_union.kits.utils.get_schema_graphs", return_value=schema_names
    )

    uninstall.uninstall_kit(connection_factory_mock, simple_kit.id)

    get_stored_queries_for_db.assert_not_called()

    options_string_to_dict.assert_not_called()
    # set_options.assert_called_once()

    get_schema_graphs.assert_not_called()


def test_uninstall_basic(
    mocker: MockerFixture,
    connection_factory_mock: stardog_utils.ConnectionFactory,
    simple_kit: Kit,
):
    dbs = [connection_factory_mock.database()]
    schema_names = ["schema_name"]
    mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.get_databases", return_value=dbs
    )

    get_stored_queries_for_db = mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.get_stored_queries_for_db",
        return_value=[],
    )

    options_string_to_dict = mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.options_string_to_dict"
    )

    # set_options = mocker.patch("stardog.admin.Database.set_options")

    mocker.patch("stardog_union.kits.utils.get_schema_names", return_value=schema_names)
    get_schema_graphs = mocker.patch(
        "stardog_union.kits.utils.get_schema_graphs", return_value=schema_names
    )

    uninstall.uninstall_kit(connection_factory_mock, simple_kit.id)

    get_stored_queries_for_db.assert_called_once()

    options_string_to_dict.assert_called_once()
    # set_options.assert_called_once()

    get_schema_graphs.assert_called_once()


def test_install_stored_queries_from_file(
    mocker: MockerFixture,
    connection_factory_mock: stardog_utils.ConnectionFactory,
):
    queries_file = Path(__file__).parent / "resources" / "queries" / "test_queries.ttl"
    kit = Kit(
        name="queries-file-kit",
        group="test",
        version="1.0.0",
        data=[],
        schemas=[],
        namespaces={},
        queries=str(queries_file),
    )

    store_queries_in_db = mocker.patch(
        "stardog_union.kits.install.stardog_utils.store_queries_in_db"
    )

    install.install_stored_queries(connection_factory_mock.admin(), "testdb", kit)

    store_queries_in_db.assert_called_once()

    content_arg = store_queries_in_db.call_args[0][1]
    assert "Test Query" in content_arg
    Graph().parse(data=content_arg, format="turtle")


def test_install_stored_queries_individual(
    mocker: MockerFixture,
    connection_factory_mock: stardog_utils.ConnectionFactory,
):
    query_file = Path("tests/resources/queries/single_query.rq")

    kit = Kit(
        name="test-kit",
        group="test",
        version="1.0.0",
        data=[],
        schemas=[],
        namespaces={},
        queries=[
            StoredQuery(name="query1", query="SELECT * WHERE { ?s ?p ?o }"),
            StoredQuery(name="query2", file=str(query_file)),
        ],
    )

    install.install_stored_queries(connection_factory_mock.admin(), "testdb", kit)

    assert connection_factory_mock.admin().new_stored_query.call_count == 2

    for call in connection_factory_mock.admin().new_stored_query.mock_calls:
        first_arg = call[1][0]
        assert first_arg in ["testdb_query1", "testdb_query2"]


def test_install_stored_queries_missing_query(
    mocker: MockerFixture,
    connection_factory_mock: stardog_utils.ConnectionFactory,
    simple_kit: Kit,
):
    kit = Kit(
        name=simple_kit.name,
        group=simple_kit.group,
        version=simple_kit.version,
        data=simple_kit.data,
        schemas=simple_kit.schemas,
        namespaces=simple_kit.namespaces,
        queries=[StoredQuery(name="query1")],
    )

    install.install_stored_queries(connection_factory_mock.admin(), "testdb", kit)

    connection_factory_mock.admin().new_stored_query.assert_not_called()


def test_install_stored_queries_file_not_found(
    mocker: MockerFixture,
    connection_factory_mock: stardog_utils.ConnectionFactory,
    simple_kit: Kit,
):
    kit = Kit(
        name=simple_kit.name,
        group=simple_kit.group,
        version=simple_kit.version,
        data=simple_kit.data,
        schemas=simple_kit.schemas,
        namespaces=simple_kit.namespaces,
        queries=[StoredQuery(name="query1", file="nonexistent.ttl")],
    )

    with pytest.raises(FileNotFoundError):
        install.install_stored_queries(connection_factory_mock.admin(), "testdb", kit)


@pytest.fixture
def queries_kit(simple_kit: Kit) -> Kit:
    """A kit with stored queries, based on simple_kit"""
    return Kit(
        name=simple_kit.name,
        group=simple_kit.group,
        version=simple_kit.version,
        data=simple_kit.data,
        schemas=simple_kit.schemas,
        namespaces=simple_kit.namespaces,
        queries=[
            StoredQuery(name="query1", query="SELECT * WHERE { ?s ?p ?o }"),
            StoredQuery(name="query2", query="SELECT * WHERE { ?s a ?type }"),
        ],
    )


def test_uninstall_kit_with_stored_queries(
    mocker: MockerFixture,
    connection_factory_mock: stardog_utils.ConnectionFactory,
    queries_kit: Kit,
):
    # Mock stored queries that would have been installed
    db_name = connection_factory_mock.database()
    mock_queries = [
        mocker.Mock(name=f"{db_name}_query1"),
        mocker.Mock(name=f"{db_name}_query2"),
        mocker.Mock(name="other_query"),  # Should not be deleted
    ]

    mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.get_databases",
        return_value=[connection_factory_mock.database()],
    )

    mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.get_stored_queries_for_db",
        return_value=mock_queries[:2],  # Only return queries for our db
    )

    mock_delete = mocker.patch(
        "stardog_union.kits.uninstall.stardog_utils.StoredQuery.delete"
    )

    uninstall.uninstall_kit(connection_factory_mock, queries_kit.id)

    # Verify delete was called on the right queries

    mock_delete.assert_has_calls(
        [
            mocker.call(connection_factory_mock.admin().__enter__(), mock_queries[0]),
            mocker.call(connection_factory_mock.admin().__enter__(), mock_queries[1]),
        ]
    )
    assert mock_delete.call_count == 2
