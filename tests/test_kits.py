import pytest
import stardog
import yaml
from pytest_mock import MockerFixture
from rdflib import Graph

from stardog_union.kits.base import DataLoad, Kit, Schema
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

        assert kit.queries
