from stardog_union import vocabs
from stardog_union.vocabs import Kits

_ALIAS_GRAPH = "tag:stardog:api:graph:aliases"

_PREFIXES = f"""prefix : <{Kits._NS}>
prefix m: <{Kits._NS}>
prefix kits: <{Kits._NS}>
"""

INSERT_ALIAS = """INSERT DATA {{
    graph <tag:stardog:api:graph:aliases> {{
        {alias_iri} <tag:stardog:api:graph:alias> {aliases} .
    }}
}}
"""

GET_KIT_GRAPHS = (
    """%s
select ?g ?model ?constraints ?data where {{
    graph ?g {{
        {{ ?module a :Module }} union {{ ?module a :KnowledgeKit }}
        ?module :id {kit_id} .
        optional {{ {{ ?module :model ?model }} union {{ ?module :hasSchema [ :model ?model ] }} }}
        optional {{ ?module :constraints ?constraints }}
        optional {{ ?module :data ?data }}
    }}
}}"""
    % _PREFIXES
)

DELETE_ALIAS = """%s
DELETE {{
    graph <%s> {{
        {alias_iri} <tag:stardog:api:graph:alias> ?x .
    }}
}}
WHERE {{
    graph <%s> {{
        {alias_iri} <tag:stardog:api:graph:alias> ?x .
    }}
}}
""" % (
    _PREFIXES,
    _ALIAS_GRAPH,
    _ALIAS_GRAPH,
)

GET_KIT_SCHEMA_NAMES = (
    """%s
select distinct ?name where {{
    graph ?g {{
        {{ ?module a :Module }} union {{ ?module a :KnowledgeKit }} .

        ?module :id {kit_id} .

        {{  ?module :schemaName ?name }}
        union
        {{ ?module :hasSchema [ rdfs:label ?name ] }}
    }}
}}
"""
    % _PREFIXES
)

GET_KIT_SCHEMA_GRAPHS = (
    """%s
select distinct ?model where {{
    graph ?g {{
        {{ ?module a :Module }} union {{ ?module a :KnowledgeKit }} .

        ?module :id {kit_id} .

        {{ {{ ?module :model ?model }} union {{ ?module :hasSchema [ :model ?model ] }} }}
    }}
}}
"""
    % _PREFIXES
)

SEC_PROPERTY_GROUPS = (
    """%s
select ?property ?groupid ?r {{
    graph {schema_graph} {{
        ?property m:group [ a m:SensitivePropertyGroup ; m:id ?groupid ; m:requiresRole ?r ]
    }}
}}"""
    % _PREFIXES
)


LIST_KITS = f"""
select distinct ?kit ?id ?ml ?description {{
    graph ?g {{
        {{ ?kit a {vocabs.Kits.KnowledgeKit.n3()} }} union {{ ?kit a {vocabs.Kits.Module.n3()} }}
        ?kit {vocabs.Kits.id.n3()} ?id ;
            rdfs:label ?ml .
        optional {{ ?module rdfs:comment ?description }}
    }}
}}
"""
