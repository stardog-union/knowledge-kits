import pytest
import stardog
import yaml
from pytest_mock import MockerFixture
from rdflib import RDF, Graph, URIRef
from stardog import content, content_types

from stardog_union import vocabs
from stardog_union.kits import install
from stardog_union.kits.base import Kit
from stardog_union.kits.install import (
    get_kit_meta,
    install_data_local,
    install_kit,
    install_namespaces,
    install_provenance,
    install_schemas,
)
from stardog_union.more_stardog import ConnectionFactory

from .test_kits import assert_contains

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
def connection_factory_mock(mocker: MockerFixture):
    cf = mocker.Mock(
        spec=ConnectionFactory,
        connection=mocker.Mock(
            return_value=mocker.MagicMock(spec=stardog.Connection),
        ),
        admin=mocker.Mock(
            return_value=mocker.MagicMock(spec=stardog.Admin),
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


def test_to_rdf(simple_kit):
    base = "urn:base:"
    g = get_kit_meta(simple_kit, base_iri=base)

    iri = URIRef(f"{base}{simple_kit.id}")

    assert g
    assert_contains(g, (iri, RDF.type, vocabs.Kits.KnowledgeKit))


def test_install_schema(mocker: MockerFixture, connection_factory_mock, simple_kit):
    mocker.patch("stardog_union.more_stardog.options_string_to_dict", return_value={})

    method = mocker.spy(install, "dict_to_options_str")

    install_schemas(
        connection_factory_mock.admin(),
        Kit.default_database_name(simple_kit),
        simple_kit,
    )

    method.assert_called_once()


def test_install_namespaces(
    mocker: MockerFixture, connection_factory_mock, simple_kit: Kit
):
    method = mocker.spy(
        connection_factory_mock.admin().database(fake_database), "add_namespace"
    )
    get_admin = mocker.spy(connection_factory_mock, "admin")
    install_namespaces(
        connection_factory_mock.admin(), "database", simple_kit.namespaces
    )
    get_admin.assert_called_once()

    assert method.call_count == 8


def test_install_provenance(
    mocker: MockerFixture, connection_factory_mock, simple_kit: Kit
):
    # Mock the get_file_prov function
    mock_prov_graph = Graph(bind_namespaces="none")
    mock_prov_graph.add(
        (vocabs.Kits.KnowledgeKit, vocabs.Kits.KnowledgeKit, vocabs.Kits.KnowledgeKit)
    )
    mock_user = "user"

    mocker.patch(
        "stardog_union.kits.install.get_file_prov", return_value=mock_prov_graph
    )

    mock_connection = connection_factory_mock.connection()

    install_provenance(mock_connection, mock_user, simple_kit)

    mock_connection.add.assert_called_once()
    args, _ = mock_connection.add.call_args
    assert isinstance(args[0], content.Raw)

    assert args[0].raw == mock_prov_graph.serialize()
    assert args[0].content_type == content_types.TURTLE


def test_install_kit_with_local_files(
    mocker: MockerFixture, connection_factory_mock, simple_kit: Kit
):
    mocker.patch(
        "stardog_union.kits.install.get_file_prov",
        return_value=Graph(bind_namespaces="none"),
    )

    install_kit(connection_factory_mock, simple_kit, local_dir="tests/resources")

    connection_factory_mock.connection.assert_called_once()
    connection_factory_mock.admin.assert_called_once()


def test_install_data_local_with_mappings(
    mocker: MockerFixture, connection_factory_mock, simple_kit: Kit
):
    mock_admin = connection_factory_mock.admin()
    mock_conn = connection_factory_mock.connection()
    mock_load = mocker.Mock()
    mock_load.file = "data.csv"
    mock_load.mappings = "mappings.sms"
    mock_load.options = {"csv.separator": ";"}
    mock_load.graph = "urn:graph"

    mocker.patch("os.path.isabs", return_value=False)
    mocker.patch("os.getcwd", return_value="tests/resources")
    mocker.patch("os.path.sep", "/")
    mocker.patch("os.path.splitext", return_value=(".csv", ".csv"))

    # NOTE: because of the import in install, we have to use the local path/name rather than its normal location
    import_file_spy = mocker.patch("stardog_union.kits.install.import_file")

    install_data_local(mock_conn, mock_admin, "fake_database", mock_load)

    import_file_spy.assert_called_once()
    args, kwargs = import_file_spy.call_args
    assert args[0] == mock_admin
    assert args[1] == "fake_database"
    assert isinstance(args[2], content.MappingFile)
    assert isinstance(args[3], content.ImportFile)
    assert kwargs["opts"] == {"csv.separator": ";"}
    assert kwargs["named_graph"] == "urn:graph"


def test_install_data_local_without_mappings(
    mocker: MockerFixture, connection_factory_mock, simple_kit: Kit
):
    mock_admin = connection_factory_mock.admin()
    mock_conn = connection_factory_mock.connection()
    mock_load = mocker.Mock()
    mock_load.file = "data.csv"
    mock_load.mappings = None
    mock_load.options = None
    mock_load.graph = "urn:graph"

    mocker.patch("os.path.isabs", return_value=False)
    mocker.patch("os.getcwd", return_value="tests/resources")
    mocker.patch("os.path.sep", "/")

    install_data_local(mock_conn, mock_admin, "fake_database", mock_load)

    mock_conn.add.assert_called_once()
    args, kwargs = mock_conn.add.call_args

    assert isinstance(args[0], content.File)
    assert kwargs["graph_uri"] == "urn:graph"
