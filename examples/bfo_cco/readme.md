# BFO / CCO Knowledge Kit

This kit adds the [Basic Formal Ontology 2020](https://github.com/BFO-ontology/BFO-2020) and
the [Common Core Ontologies](https://github.com/CommonCoreOntology/CommonCoreOntologies) (CCO)
v2.2 to a Stardog database, set up so that Stardog's reasoner and Voicebox actually use them.
Both ontologies are loaded at install time from their GitHub releases. The kit also includes:

- **Stardog-specific inference supplements.** These restore inferences that Stardog's SL
  reasoner otherwise drops: part-of and located-in chains at any depth, and automatic
  classification into CCO's defined classes such as Sensor.
- **SHACL shapes** that catch BFO/CCO disjointness errors in your data, for example a record
  typed as both an aircraft and a maintenance event.

```
$ kits install examples/bfo_cco -t my_endpoint
```

**What the kit does not do.** It does not connect *your* ontology to CCO. Until you align
your classes and properties with CCO and BFO (see [Aligning your ontology](#aligning-your-ontology)),
CCO is present but no data belongs to it, and CCO-level queries return nothing. The
alignment is usually a few dozen axioms, and it is the part each team has to write. For a
complete worked example, install [`../bfo_cco_fleet`](../bfo_cco_fleet/readme.md).

## Requirements and tested environments

| | |
|---|---|
| Tested | Stardog **12.1.1** (Docker image `stardog/stardog:12.1.1`), `reasoning.type=SL`, with the `kits` CLI from this repository |
| Other versions | Not yet tested. |
| Network | The machine running `kits install` downloads BFO and CCO from `raw.githubusercontent.com`. For an air-gapped install, download the 12 files listed in `kit.yaml` and change each `file:` to the local path. |
| Server access | Normal database-creation and data-loading rights. No access to the server's file system is needed, so the kit also works on managed deployments. |

## Installing into a new database

```
$ kits install examples/bfo_cco -t my_endpoint                  # creates kit-bfo-cco
$ kits install examples/bfo_cco -t my_endpoint -d my_new_db     # or any name that does not exist yet
```

The kit creates the database with these options: Voicebox and semantic search on,
`query.timeout=60s` (see [Known issues](#known-issues)), and the BFO, CCO and supplement graphs
in both `reasoning.schema.graphs` and `search.semantic.index.contexts.filter`. Add your own
ontology to `tag:stardog:api:context:schema`, which is also in both lists.

## Installing into an existing database

```
$ kits install examples/bfo_cco -t my_endpoint -d existing_db
```

This loads the same graphs, namespaces and the named reasoning schema `bfo_cco`. Nothing
already in the database is changed. The `kits` CLI does not change the options of an existing
database, so one step is left to you: **add the kit's graphs to the default reasoning schema.**
The reasoner reads only the graphs in `reasoning.schema.graphs` by default, and Voicebox uses
the default. The named schema `bfo_cco` is used only by a query that passes `schema=bfo_cco`, and
it does not include your own ontology graph.

1. Read the current setting:

   ```
   $ curl -u admin:admin http://localhost:5820/admin/databases/existing_db/options
   ```

2. Post the full list: the existing entries plus the three kit graphs. The database can stay
   online.

   ```
   $ curl -u admin:admin -X POST http://localhost:5820/admin/databases/existing_db/options \
       -H 'Content-Type: application/json' \
       -d '{"reasoning.schema.graphs": ["<existing graphs>",
            "urn:stardog:bfo_cco:bfo", "urn:stardog:bfo_cco:cco", "urn:stardog:bfo_cco:supplements"]}'
   ```

   The install has already added these graphs to `search.semantic.index.contexts.filter`
   (Stardog does this when a named schema is set), so this step does not fail with `422`.

3. **Verify.** Once aligned data exists, a reasoning query such as
   `SELECT (COUNT(*) AS ?n) { ?x a <http://purl.obolibrary.org/obo/BFO_0000001> }` returns
   more than 0.

On 12.1.1, installing into an existing Voicebox database took about a minute to commit while
Stardog indexed CCO for semantic search.

## Uninstalling

```
$ kits uninstall ontologies:bfo-cco:1.0 -t my_endpoint -d existing_db
```

This clears the four kit graphs and the kit's metadata graph. Your own graphs, including
`tag:stardog:api:context:schema`, are not touched, because the kit never writes to them. With
the current `kits` CLI, check three things afterwards:

- **Uninstall deletes every stored query on the database**, not only the kit's. Export the
  stored queries you want to keep first.
- The named schema `bfo_cco` stays in `reasoning.schemas`, and the alias
  `tag:stardog:kit:alias:bfo_cco` stays in `tag:stardog:api:graph:aliases`. Both are harmless,
  and you can remove them by hand.
- Remove the three kit graphs from `reasoning.schema.graphs` if you added them.

## Aligning your ontology

Your data is typed with your own classes and linked with your own properties. For BFO/CCO
queries and the supplements to apply, add alignment axioms to a graph that is in the default
reasoning schema, for example `tag:stardog:api:context:schema`:

- make each domain class `rdfs:subClassOf` its closest CCO (or BFO) class;
- make each relationship property `rdfs:subPropertyOf` the matching BFO relation.

```turtle
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix obo:  <http://purl.obolibrary.org/obo/> .
@prefix cco:  <https://www.commoncoreontologies.org/> .
@prefix ex:   <https://example.org/ops#> .

# Classes -> CCO classes
ex:Drone          rdfs:subClassOf cco:ont00001043 .   # Aircraft
ex:SupplyTruck    rdfs:subClassOf cco:ont00000053 .   # Ground Motor Vehicle
ex:Engine         rdfs:subClassOf cco:ont00000210 .   # Engine
ex:Camera         rdfs:subClassOf cco:ont00000199 .   # Camera
ex:Depot          rdfs:subClassOf cco:ont00000192 .   # Facility
ex:ImagingCapability rdfs:subClassOf cco:ont00001241 .  # Sensor Function
ex:RepairJob      rdfs:subClassOf cco:ont00000950 .   # Act of Maintenance

# Properties -> BFO relations
ex:installedOn    rdfs:subPropertyOf obo:BFO_0000176 .  # continuant part of
ex:componentOf    rdfs:subPropertyOf obo:BFO_0000176 .  # continuant part of
ex:stationedAt    rdfs:subPropertyOf obo:BFO_0000171 .  # located in
ex:hasCapability  rdfs:subPropertyOf obo:BFO_0000196 .  # bearer of
ex:performedOn    rdfs:subPropertyOf obo:BFO_0000057 .  # has participant
```

The supplements depend on these BFO relations. Map your properties to them to get the
corresponding behavior:

| BFO relation | Map your property here if it means… | Enables |
|---|---|---|
| `BFO_0000176` continuant part of (inverse `BFO_0000178` has continuant part) | component of, installed on, mounted on | `bfo_cco:continuantPartOfTransitive` / `hasContinuantPartTransitive`: parts at any depth |
| `BFO_0000171` located in (inverse `BFO_0000124` location of) | housed in, stationed at, located at | `bfo_cco:locatedInTransitive` / `locationOfTransitive`: everything at a place at any depth |
| `BFO_0000196` bearer of (inverse `BFO_0000197` inheres in) | has capability, has function, has role | Classification as CCO **Sensor** or **Sensor Platform** when the capability is a Sensor Function or Sensor Role (or a sub-class of one) |
| `BFO_0000055` realizes | an activity that uses a capability | Classification as **Sensing Process** or **Planned Act** |
| `BFO_0000059` concretizes | a role or disposition that carries out a plan or order | **Planned Act** (with realizes) |

Guidelines:

- **Check what CCO already asserts.** For example, CCO already makes every *Act of
  Maintenance* a *Planned Act*.
- **Don't align something that is a design or a specification to a physical-object class.**
  A platform *model* is an information content entity (for example CCO Artifact Model), not
  a Material Artifact.
- **Use `rdfs:subClassOf` / `rdfs:subPropertyOf`, not `owl:equivalentClass`.** Equivalence
  would also type CCO instances as your classes.
- **After aligning, run the verification queries below.** Also compare your domain class
  counts with reasoning on and off; they should not change.

### Verification queries

Run these with reasoning on. Each rdf:type object is a constant IRI, which keeps reasoning
queries fast (see [Known issues](#known-issues)).

```sparql
PREFIX cco: <https://www.commoncoreontologies.org/>
PREFIX obo: <http://purl.obolibrary.org/obo/>
PREFIX bfo_cco: <urn:stardog:bfo_cco#>

# Roll-up by CCO category
SELECT ?type (COUNT(DISTINCT ?x) AS ?n) WHERE {
  { ?x a cco:ont00001043 . BIND("Aircraft" AS ?type) }
  UNION { ?x a cco:ont00000618 . BIND("Ground Vehicle" AS ?type) }
  UNION { ?x a obo:BFO_0000040 . BIND("All material entities" AS ?type) }
} GROUP BY ?type

# Everything that is part of something, at any depth
SELECT ?whole ?part WHERE { ?whole bfo_cco:hasContinuantPartTransitive ?part }

# Sensors inferred from capabilities
SELECT ?sensor WHERE { ?sensor a cco:ont00000569 }

# Data quality: anything that is both a continuant and an occurrent
SELECT ?x WHERE { ?x a obo:BFO_0000002 ; a obo:BFO_0000003 }
```

## Contents

| Graph | Source | What it is |
|---|---|---|
| `urn:stardog:bfo_cco:bfo` | BFO-2020 tag `release-2024-01-29`, `src/owl/bfo-core.ttl` | BFO 2020 core. 1,015 triples. |
| `urn:stardog:bfo_cco:cco` | CommonCoreOntologies tag `v2.2`, the 11 files in `src/cco-modules/` | CCO v2.2. 12,988 triples. |
| `urn:stardog:bfo_cco:supplements` | `schema/bfo_cco-stardog-inferences.ttl` | Stardog supplements (160 triples, described below). |
| `urn:stardog:bfo_cco:constraints` | `constraints/bfo_cco-disjointness-shacl.ttl` | 42 SHACL shapes, one per disjoint class pair. Not part of the reasoning schema. |
| `tag:stardog:kit:ontologies:bfo-cco:1.0` | written by `kits` | Kit metadata: this readme, the graphs, and PROV-O provenance for each loaded file, including its source URL. |

The first three graphs form the named reasoning schema `bfo_cco` and are added to the default
reasoning schema (see above). The alias `tag:stardog:kit:alias:bfo_cco` covers all four.

Other files: `tools/gen_disjointness_shacl.py` regenerates the SHACL file from the BFO and CCO
files listed in `kit.yaml` (needs `rdflib` and `PyYAML`), and `tests/` holds the structural test
suite.

Registered namespaces: `cco:`, `obo:`, `bfo_cco:` (`urn:stardog:bfo_cco#`, the kit's own terms),
and `rdf:`, `rdfs:`, `owl:`, `xsd:`, `skos:`. The default `:` prefix is left for your domain
ontology.

**Why BFO and CCO are loaded as separate sources.** CCO's merged file
(`src/cco-merged/CommonCoreOntologiesMerged.ttl`) already contains BFO core, so loading it with
`bfo-core.ttl` would load BFO twice. Instead, the kit loads BFO from the BFO repository and CCO's
11 modules, which import BFO rather than contain it. The result is logically the same as the
merged file: the only differences are the text of 17 BFO `skos:scopeNote` annotations and one
`owl:inverseOf` axiom stated in the other direction. The SHACL shapes generated from either
source are identical.

## Stardog inference supplements

Stardog's SL reasoner skips 38 axioms of BFO + CCO as "Not a valid SL axiom". The warnings are
logged in `stardog.log` on the first reasoning query. The supplement file adds no new
warnings.

### 1. Transitive closures of parthood and location

BFO defines *continuant part of* (`BFO_0000176`) and *located in* (`BFO_0000171`) as
holding **at some time**. Relations defined that way are not transitive, and BFO correctly
does not declare them transitive. This kit leaves the BFO relations unchanged and adds
kit-owned transitive super-properties instead:

| Property | Closure of |
|---|---|
| `bfo_cco:continuantPartOfTransitive` | continuant part of, including its sub-properties (member part of, spatial part of, …) |
| `bfo_cco:hasContinuantPartTransitive` | has continuant part |
| `bfo_cco:locatedInTransitive` | located in |
| `bfo_cco:locationOfTransitive` | location of |

Query these properties for "directly or indirectly" roll-ups, such as every component of
an aircraft at any depth. Each link in a chain holds at some time. The chain does not claim
that all links hold at the same time.

### 2. Sufficient conditions for CCO's defined classes

CCO defines Sensor, Sensor Platform, Sensing Process, Planned Act and Geospatial Location
with `owl:equivalentClass` over a union. That is not valid in SL, so Stardog drops the
whole axiom and never classifies anything into these classes. The supplement splits each
union into SL-valid sufficient conditions, for example *material entity and bearer of some
Sensor Function* ⊑ *Sensor*. These classifications then work with the default
`reasoning.approximate=false`.

Geospatial Location's condition, "location of some (independent continuant and not spatial
region)", cannot be expressed in SL. It is under-approximated with material entity, site
and continuant fiat boundary. The result is sound but slightly incomplete.

### Not approximated

The other 33 skipped axioms are deliberately left out:

- 23 domain and range axioms over unions, for example on "participates in", "has
  participant" and "concretizes";
- 10 universal restrictions over unions.

Sound weakenings exist; for example, a union domain could be replaced by a common
superclass such as independent continuant. They were left out because they add little for
query answering.

## SHACL constraints

There is one `sh:NodeShape` per disjoint class pair: 21 pairs from `owl:disjointWith` and
21 more expanded from 5 `owl:AllDisjointClasses` axioms. Each has `sh:severity
sh:Violation`. The shapes flag, for example, anything that is both a continuant and an
occurrent. They are standard SHACL, and pyshacl gives the same report as Stardog.

Stardog reads shapes from `shacl.shape.graphs`, which defaults to all local graphs, so the
shapes in `urn:stardog:bfo_cco:constraints` apply without any setting. `sh:targetClass` and
`sh:class` follow `rdfs:subClassOf` in the data graph, so validate over graphs that include the
BFO/CCO graphs; the default `context:local` does.

```
$ stardog icv report db        # add -r to validate with reasoning
```

Avoid `stardog reasoning consistency` on a CCO database. On 12.1.1 it hung for more than 2
minutes and left background processes running.

## Using it with Voicebox

- A new database gets the Voicebox options and the semantic index filter from the kit. For
  an existing database, see [Installing into an existing database](#installing-into-an-existing-database).
- CCO documents its classes with `skos:definition` rather than `rdfs:comment`. Voicebox
  found CCO classes such as Sensor by label without problems.
- Set `query.timeout` (the kit sets 60 s on a new database). Voicebox sometimes generates
  queries with a variable `rdf:type` object (see [Known issues](#known-issues)).

**Testing.** The [fleet example kit](../bfo_cco_fleet/readme.md) includes a Voicebox A/B harness.
On 12.1.1 with GPT-6 Luna (OpenRouter), one run of 13 questions: 13 of 13 correct with this kit,
9 of 13 on the same data without BFO/CCO. The four misses were all BFO/CCO questions (inferred
sensors, parts at any depth, all physical objects, sensor platforms); domain-only questions were
6 of 6 both ways.

## Known issues

- **Variable-type reasoning queries are slow.** On a CCO database with very little data,
  `<x> a ?t` took about 12 s and `?s a ?c GROUP BY ?c` about 80 s. Binding the type through
  `VALUES` does not help; one query per class does. LLM-generated SPARQL produces these
  shapes, so set `query.timeout`: a 60 s timeout cancels them cleanly with HTTP 410.
- **Installing into an existing database needs one manual options step**, described above.
- **`kits uninstall` side effects**, described under [Uninstalling](#uninstalling).

## Tests

The structural tests check every supplement axiom (including negative cases), the hierarchy
and the SHACL shapes. They need only the Python standard library. Run them on a test database
that has the kit installed:

```
$ python3 tests/run_structural_tests.py kit-bfo-cco --endpoint http://localhost:5820 --load
```

On 12.1.1: 22 of 22 pass, the same as the archetype version of this content. With plain CCO,
without the supplements and shapes, 9 of 22 pass.

## Updating the BFO or CCO version

1. Change the tag in the BFO and CCO URLs in `kit.yaml` (and in `../bfo_cco_fleet/kit.yaml`),
   and bump the kit `version`.
2. Run `python tools/gen_disjointness_shacl.py`.
3. Install into a test database and run one reasoning query. Compare the "Not a valid SL
   axiom" warnings in `stardog.log` with section 2 of the supplement file. A defined class
   that has changed may need its sufficient conditions updated.
4. Run `tests/run_structural_tests.py`, and the fleet example's stored queries.

## Licenses

- **BFO 2020** is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Source: <https://github.com/BFO-ontology/BFO-2020>.
- **CCO** is © CUBRC, Inc. and licensed under the
  [BSD 3-Clause License](https://github.com/CommonCoreOntology/CommonCoreOntologies/blob/v2.2/LICENSE).
  Source: <https://github.com/CommonCoreOntology/CommonCoreOntologies>.
- This kit does not redistribute either ontology; `kits install` downloads them from their
  repositories. The supplements, shapes, tools and tests in this folder are original to this
  kit.
