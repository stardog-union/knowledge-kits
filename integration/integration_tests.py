import pytest
from stardog_union import more_stardog as stardog_utils
from stardog_union.kits.base import Kit, StardogKitRepository
from stardog_union.kits import install, uninstall

import yaml
import os

@pytest.fixture
def connection_factory() -> stardog_utils.ConnectionFactory:
    return stardog_utils.ConnectionFactory(
        endpoint=os.getenv("STARDOG_INTERNAL_ENDPOINT", "http://localhost:5820"),
        database=os.getenv("STARDOG_INTERNAL_DATABASE", "testDb"),
        username=os.getenv("STARDOG_INTERNAL_USERNAME", "admin"),
        password=os.getenv("STARDOG_INTERNAL_PASSWORD", "admin")
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

def test_install_kit_integration(connection_factory: stardog_utils.ConnectionFactory, simple_kit: Kit):
    repo = StardogKitRepository(connection_factory)

    install.install_kit(conn_factory=connection_factory, kit=simple_kit, local_dir="examples/starwars")

    graphs = [ g for g in filter(lambda x:x, [data.graph for data in simple_kit.data])]

    assert simple_kit.id in [id for id, _, _ in repo.list()]
    for graph in graphs:
        with connection_factory.connection() as conn:
            query = f"ASK {{ GRAPH <{graph}> {{ }} }}"
            assert conn.ask(query)

    uninstall.uninstall_kit(connection_factory, simple_kit.id, clean_database=True)

    for graph in graphs:
        with connection_factory.connection() as conn:
            query = f"ASK {{ GRAPH <{graph}> {{ }} }}"
            assert not conn.ask(query)
