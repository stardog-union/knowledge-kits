# BFO/CCO worked example: fleet readiness

This kit is the [bfo-cco kit](../bfo_cco/readme.md) plus a small fleet-maintenance knowledge
graph aligned to CCO, and seven stored queries that show what BFO/CCO adds. The fleet ontology
has no BFO/CCO terms. A 24-axiom alignment (`data/fleet_cco_alignment.ttl`) connects it to CCO,
and that alignment is the only domain-specific work.

```
$ kits install examples/bfo_cco_fleet -t my_endpoint     # creates kit-bfo-cco-fleet
```

The BFO, CCO, supplement and SHACL entries are the same as in `../bfo_cco/kit.yaml`. This kit
repeats them because kits cannot depend on other kits, so a single install builds the whole
example.

## Files

| File | Graph | What it is |
|---|---|---|
| `data/fleet_ontology.ttl` | `urn:fleet:ontology`, `urn:fleet:kg` | The domain ontology: 17 classes (fighter and transport aircraft, tanks, trucks, satellites, engines and their modules, targeting pods, cameras, bases, hangars, maintenance events, …) and 12 properties. |
| `data/fleet_cco_alignment.ttl` | `urn:fleet:ontology`, `urn:fleet:kg` | The alignment: 17 `rdfs:subClassOf` axioms to CCO classes and 7 `rdfs:subPropertyOf` axioms to BFO relations. Use it as the template for aligning your own ontology. |
| `data/fleet_data.ttl` | `urn:fleet:kg` | 14 aircraft, 26 engines (each with a fan module, a core module and a fan blade set), 11 ground vehicles, 2 satellites, 6 targeting pods with infrared cameras, 3 bases, 5 facilities and 12 maintenance events. |
| `data/incoming_batch.ttl` | `urn:fleet:incoming` | An unmerged batch with one mapping error: AF-1011 is typed as both an aircraft and a maintenance event. |
| `queries/*.rq` | stored queries | The seven queries, installed as `kit-bfo-cco-fleet_<name>` with reasoning on. Each header gives the question and the expected result. |
| `tests/voicebox/` | not loaded | Voicebox A/B harness (`voicebox_eval.py`, `analyze_results.py`, 13 questions). |

`urn:fleet:ontology` is in the reasoning schema. `urn:fleet:kg` is the graph the queries and
Voicebox read, so the ontology is loaded there too.

## Expected results

With reasoning on, on Stardog 12.1.1. The "without" column is the same data in a database
without BFO/CCO.

| Stored query | Without BFO/CCO | With this kit |
|---|---|---|
| `vehicles_by_type` | no rows | Aircraft 14, Ground Vehicle 11, Spacecraft 2 |
| `sensors_inferred` (nothing is typed Sensor in the data) | no rows | 8: six infrared cameras and two satellites, classified through their sensor capability |
| `components_any_depth` (AF-1001) | no rows | 6: engine, fan module, core module, fan blade set, targeting pod, infrared camera |
| `located_any_depth` (Kirtland AFB, including inside its hangars) | no rows | 9: two hangars and seven aircraft |
| `physical_inventory` | no rows | 151 material entities (27 vehicles, 26 engines, 8 facilities, 6 imaging instruments, …) |
| `bad_record_in_batch` | no rows | AF-1011 |
| `control_domain_query` (number of fighter aircraft) | 10 | 10 |

The SHACL shapes report the same AF-1011 error, through the continuant/occurrent disjointness
shape: `stardog icv report kit-bfo-cco-fleet`.

What to take from it:

- Queries 01–06 depend on the alignment: without it, they return no rows even with BFO/CCO
  installed.
- Query 07 shows that adding BFO/CCO does not change answers to existing domain queries.
- Every query binds its `rdf:type` objects to constant IRIs, which keeps reasoning queries
  fast (see "Known issues" in the bfo-cco readme).

## Voicebox comparison

`tests/voicebox` asks Voicebox 13 questions: seven depend on BFO/CCO and six are domain-only
controls. One run per question, GPT-6 Luna on OpenRouter, Stardog 12.1.1:

| | With this kit | Without BFO/CCO |
|---|---|---|
| All questions | 13 of 13 | 9 of 13 |
| BFO/CCO questions | 7 of 7 | 3 of 7 |
| Domain-only questions | 6 of 6 | 6 of 6 |

Without BFO/CCO, Voicebox missed inferred sensors, parts at any depth, all physical objects and
sensor platforms. With the kit, its generated SPARQL used CCO and BFO terms such as Sensor,
material entity and *continuant part of*, found through the semantic index.

```
$ VOICEBOX_TOKEN=<Stardog JWT> python3 tests/voicebox/voicebox_eval.py out.jsonl --runs 3 \
    --stardog-for-voicebox http://stardog:5820 --db kit-bfo-cco-fleet --db <baseline db>
$ python3 tests/voicebox/analyze_results.py out.jsonl
```

## Licenses

BFO 2020 (CC BY 4.0) and CCO (© CUBRC, Inc., BSD 3-Clause) are downloaded from their GitHub
repositories at install time; see the bfo-cco readme. The fleet ontology, data, queries and
tests are original to this kit.
