from rdflib import URIRef
from rdflib.namespace import DefinedNamespace, Namespace


class StardogSystem(DefinedNamespace):
    """Namespace for Stardog System database"""

    VoiceboxQuestions: URIRef

    voiceboxQuestion: URIRef
    queryString: URIRef
    queryCreator: URIRef
    queryCreationDate: URIRef

    queryDatabase: URIRef
    queryName: URIRef
    queryDescription: URIRef

    ReasoningQuery: URIRef
    SharedQuery: URIRef
    StoredQuery: URIRef

    _NS = Namespace("http://system.stardog.com/")


class Kits(DefinedNamespace):
    """Namespace for Knowledge Kits"""

    readme: URIRef
    model: URIRef
    data: URIRef
    constraints: URIRef
    alias: URIRef
    id: URIRef

    hasOption: URIRef
    key: URIRef
    value: URIRef

    hasQuery: URIRef
    queryCode: URIRef
    hasSchema: URIRef
    hasSource: URIRef

    DataModel: URIRef
    DataSource: URIRef

    Module: URIRef
    """A Module, aka, a Knowledge Kit.
    
    This is the previous name/schema for a KK. It is being deprecated in favor of KnowledgeKit."""

    KnowledgeKit: URIRef

    _NS = Namespace("urn:stardog:modules:")


class SO(DefinedNamespace):
    """A version of the schema.org model that uses https as the basis, not http."""

    domainIncludes: URIRef
    rangeIncludes: URIRef

    _NS = Namespace("https://schema.org/")


SD_TEXT_MATCH = URIRef("tag:stardog:api:property:textMatch")
SD_LABEL = URIRef("tag:stardog:api:label")

VBX_QUESTION_GRAPH = URIRef("http://system.stardog.com/VoiceboxQuestions")
