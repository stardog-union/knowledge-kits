from pytest_mock import MockerFixture

from stardog_union import more_stardog as stardog_utils
from stardog_union.kits import Kit, uninstall

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
