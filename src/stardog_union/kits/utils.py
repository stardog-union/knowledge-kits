import hashlib

import stardog
from rdflib import Literal as RDFLiteral

from stardog_union import more_stardog as stardog_utils
from stardog_union.kits import queries


def hash_file(fn) -> str:
    """Compute the SHA1 hash of a file"""
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

    sha1 = hashlib.sha1()

    with open(fn, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    return "%s" % sha1.hexdigest()


def get_graphs_list(conn: stardog.Connection, kit_id: str) -> list[str]:
    """Get the list of graphs associated with a given kit"""
    graphs = set()
    result = stardog_utils.SelectQueryResult(
        conn.select(queries.GET_KIT_GRAPHS.format(kit_id=RDFLiteral(kit_id).n3()))
    )
    for binding in result:
        if "g" in binding:
            graphs.add(str(binding.g))
        if "data" in binding:
            graphs.add(str(binding.data))
        if "model" in binding:
            graphs.add(str(binding.model))
        if "constraints" in binding:
            graphs.add(str(binding.constraints))
    return [x for x in graphs]


def get_schema_names(conn: stardog.Connection, kit_id: str) -> list[str]:
    result = stardog_utils.SelectQueryResult(
        conn.select(queries.GET_KIT_SCHEMA_NAMES.format(kit_id=RDFLiteral(kit_id).n3()))
    )
    names = []

    for binding in result:
        if "name" in binding:
            names.append(binding.name)

    return names


def get_schema_graphs(conn: stardog.Connection, kit_id: str) -> list[str]:
    result = stardog_utils.SelectQueryResult(
        conn.select(
            queries.GET_KIT_SCHEMA_GRAPHS.format(kit_id=RDFLiteral(kit_id).n3())
        )
    )

    return list(filter(lambda x: x, [binding.get("model") for binding in result]))
