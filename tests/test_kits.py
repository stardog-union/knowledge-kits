import pytest
import stardog
import yaml
from pytest_mock import MockerFixture
from rdflib import Graph

from stardog_union.kits.base import DataLoad, Kit, Schema, StoredQuery
from stardog_union.more_stardog import ConnectionFactory

fake_endpoint = "https://some-endpoint:5820"
fake_database = "fake_database"
fake_schema_name = "fake_schema_name"
fake_schema_graphs = ["urn:schema:graph"]


@pytest.fixture
def simple_kit() -> Kit:
    with open("tests/resources/test_kit.yaml", "r") as f:
        data = yaml.safe_load(f)

        return Kit.from_dict(data)


@pytest.fixture
def connection_factory_mock(mocker: MockerFixture, databases=[fake_database]):
    cf = mocker.Mock(
        spec=ConnectionFactory,
        connection=mocker.Mock(
            return_value=mocker.MagicMock(spec=stardog.Connection),
        ),
        admin=mocker.Mock(
            return_value=mocker.MagicMock(
                spec=stardog.Admin, databases=mocker.Mock(return_value=databases)
            ),
        ),
        new_connection_factory=mocker.Mock(),
        endpoint=mocker.Mock(return_value=fake_endpoint),
        database=mocker.Mock(return_value=fake_database),
        schema_name=fake_schema_name,
        options={
            "endpoint": fake_endpoint,
            "username": "mhgrove",
            "database": fake_database,
            "schema_name": fake_schema_name,
            "password": "passwd",
        },
    )
    cf.new_connection_factory.return_value = cf

    return cf


def assert_contains(g: Graph, triple: tuple):
    assert list(g.triples(triple))


def test_kit_load():
    with open("tests/resources/test_kit.yaml", "r") as f:
        data = yaml.safe_load(f)

        kit = Kit.from_dict(data)

        assert kit.id == "stardog:testing:1.0"
        assert kit.name == "testing"
        assert kit.group == "stardog"
        assert kit.version == "1.0"

        assert kit.label == "Stardog Testing Kit"
        assert kit.description == "This is used for testing"

        assert kit.data == [
            DataLoad(file="model.ttl", graph="tag:stardog:api:context:schema"),
            DataLoad(file="data.ttl", graph="urn:stardog:test:data"),
            DataLoad(
                file="data.csv",
                graph="urn:stardog:test:other_data",
                mappings="mappings.sms",
            ),
        ]

        assert kit.schemas == [
            Schema(name="default", graphs=["tag:stardog:api:context:schema"])
        ]

        assert len(kit.namespaces) == 8
        assert kit.namespaces["sd"] == "urn:stardog:"

        assert kit.metadata

        assert kit.queries


def test_kit_load_queries_as_string():
    """Test that queries can be loaded as a single file path (string)."""
    kit_data = {
        "name": "test",
        "group": "test",
        "version": "1.0",
        "queries": "stored_queries.ttl",
    }

    kit = Kit.from_dict(kit_data)

    assert isinstance(kit.queries, str)
    assert kit.queries == "stored_queries.ttl"


def test_kit_load_queries_as_list_with_inline_query():
    """Test that queries can be loaded as a list with inline query strings."""
    kit_data = {
        "name": "test",
        "group": "test",
        "version": "1.0",
        "queries": [
            {
                "name": "query1",
                "query": "SELECT * WHERE { ?s ?p ?o }",
                "options": {"reasoning": True},
            },
            {
                "name": "query2",
                "query": "SELECT * WHERE { ?s a ?type }",
            },
        ],
    }

    kit = Kit.from_dict(kit_data)

    # Queries should be a list
    assert isinstance(kit.queries, list)
    assert len(kit.queries) == 2

    # Each query should be a StoredQuery object
    assert isinstance(kit.queries[0], StoredQuery)
    assert isinstance(kit.queries[1], StoredQuery)

    # Check first query
    assert kit.queries[0].name == "query1"
    assert kit.queries[0].query == "SELECT * WHERE { ?s ?p ?o }"
    assert kit.queries[0].file is None
    assert kit.queries[0].options == {"reasoning": True}

    # Check second query
    assert kit.queries[1].name == "query2"
    assert kit.queries[1].query == "SELECT * WHERE { ?s a ?type }"
    assert kit.queries[1].file is None
    assert kit.queries[1].options is None


def test_kit_load_queries_as_list_with_file_reference():
    """Test that queries can be loaded as a list with file references.

    This test demonstrates the bug: when queries are defined as a list with
    individual StoredQuery objects that reference files, the parsing logic
    should create StoredQuery objects, but currently it doesn't.
    """
    kit_data = {
        "name": "test",
        "group": "test",
        "version": "1.0",
        "queries": [
            {
                "name": "query_from_file",
                "file": "queries/my_query.sparql",
                "options": {"reasoning": True},
            },
            {
                "name": "inline_query",
                "query": "SELECT * WHERE { ?s ?p ?o }",
            },
        ],
    }

    kit = Kit.from_dict(kit_data)

    # Queries should be a list
    assert isinstance(kit.queries, list)
    assert len(kit.queries) == 2

    # Each query should be a StoredQuery object
    assert isinstance(kit.queries[0], StoredQuery)
    assert isinstance(kit.queries[1], StoredQuery)

    # Check first query (file-based)
    assert kit.queries[0].name == "query_from_file"
    assert kit.queries[0].file == "queries/my_query.sparql"
    assert kit.queries[0].query is None
    assert kit.queries[0].options == {"reasoning": True}

    # Check second query (inline)
    assert kit.queries[1].name == "inline_query"
    assert kit.queries[1].query == "SELECT * WHERE { ?s ?p ?o }"
    assert kit.queries[1].file is None
