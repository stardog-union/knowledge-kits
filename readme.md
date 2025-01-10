# Stardog Knowledge Kits

Knowledge Kits define the structure, data, and metadata for treating knowledge graphs in a "KG as Code" manner. Coupled with some simple tooling, they offer a standardized way to automate, version, and share graph deployments, making it easier to manage complex graph systems. 

# Kit Specification

This specification defines the structure and elements used for describing the configuration of a Stardog Knowledge Graph using YAML. It supports configurations in a "knowledge graph as code" manner, enabling automation and versioning.

## Root Elements

These top-level fields define the identity and basic setup of the Knowledge Kit.

### `group`
- **Type**: `string`
- **Description**: The category or group under which the kit.
- **Example**: 
  ```yaml
  group: tutorial
  ```

### `name`
- **Type**: `string`
- **Description**: The name of the kit.
- **Example**:
  ```yaml
  name: music
  ```

### `version`
- **Type**: `string`
- **Description**: The version of the kit, following semantic versioning.
- **Example**:
  ```yaml
  version: 1.0
  ```

### `label`
- **Type**: `string`
- **Description**: A human readable label for the kit
- **Example**:
  ```yaml
  description: "SPARQL Tutorial: Music"
  ```

### `description`
- **Type**: `string`
- **Description**: A detailed description of the kit.
- **Example**:
  ```yaml
  description: "SPARQL Tutorial: Music"
  ```

### `options`
- **Type**: `map`
- **Description**: [Database configuration options](https://docs.stardog.com/operating-stardog/database-administration/database-configuration#database-options) for installing the kit in a new database.
- **Example**:
  ```yaml
  options:
    database.name: kit-music
    search.enabled: true
    graph.aliases: true
  ```

### `alias`
- **Type**: `string`
- **Description**: The alias of the data graph. This is the union of all of your graphs to allow for easy use in Voicebox, Explorer, and Studio.
- **Example**:
  ```yaml
  alias: music_data
  ```

## Data

Defines the data that makes up the contents of the kit

### `file`
- **Type**: `string`
- **Description**: The path to the data file. This is relative to the "root" of the kit; where `kit.yaml` is stored. Mutually exclusive with `source`.
- **Example**:
  ```yaml
  file: data.ttl
  ```

### `source`
- **Type**: `string`
- **Description**: Name of the [data source](#sources). Mutually exclusive with `file`. 
- **Example**:
  ```yaml
  source: my_databricks
  ```

### `name`
- **Type**: `string`
- **Description**: The name for the [Virtual Graph](https://docs.stardog.com/virtual-graphs/) that is to be created. Should be used with `source`
- **Example**:
  ```yaml
  name: my_vg
  ```

### `graph`
- **Type**: `string`
- **Description**: The named graph that the data will be loaded into. If `graph` is omitted, data will be stored in the default graph _unless_ it is an RDF file that supports named graphs, such as Trig. In those cases, the data will be loaded into the same graphs as the file. This is only used for `file` data sources.
- **Example**:
  ```yaml
  graph: "stardog-tutorial:music:music_data"
  ```

### `mappings`
- **Type**: `string`
- **Description**: Path to [SMS mapping](https://docs.stardog.com/virtual-graphs/mapping-data-sources) file for enabling transformation from non RDF data sources. Can be used with static files (JSON, CSV) or can be used as a part of a virtual graph.
- **Example**:
  ```yaml
  mappings: mappings/characters.sms
  ```


## Schemas

This section defines the [schemas](https://docs.stardog.com/inference-engine/#reasoning-schemas) associated with the knowledge kit.

### `name`
- **Type**: `string`
- **Description**: The name of the schema.
- **Example**:
  ```yaml
  name: "music"
  ```

### `graphs`
- **Type**: `array of strings`
- **Description**: A list of graph URIs that belong to the schema.
- **Example**:
  ```yaml
  graphs:
    - "stardog-tutorial:music:music_schema"
  ```

## Namespaces

A collection of namespace definitions that can be used throughout the knowledge kit.

- **Type**: `map`
- **Description**: Define namespaces for shorthand references in the kit.
- **Example**:
  ```yaml
  namespaces:
    catalog: "tag:stardog:api:catalog:"
    m: "urn:stardog:modules:"
    kg: "tag:stardog:api:context:"
    sqs: "tag:stardog:api:sqs:"
  ```

## Sources

Defines a which Stardog [Data Sources](https://docs.stardog.com/virtual-graphs/data-sources/) are used by the Virtual Graphs of the kit.


Details Coming Soon.


## Queries

- **Type**: `string`
- **Description**: Path to a file containing stored queries for the knowledge graph.
- **Example**:
  ```yaml
  queries: "test_stored_queries.ttl"
  ```

## User Defined Metadata

Metadata associated with the knowledge graph project, including licensing, contributors, and tags. This information is not used by the Knowledge Kit tooling; it is intended for use by Kit creators.

### `license`
- **Type**: `map`
- **Description**: License information for the project.
- **Subfields**:
  - `name`: License name (e.g., "Apache 2.0").
  - `link`: Link to the full license text.
- **Example**:
  ```yaml
  license:
    name: "Apache 2 License"
    link: "https://www.apache.org/licenses/LICENSE-2.0"
  ```

### `marketplace`

Information when kits are published on Stardog Cloud.

- **Type**: `map`
- **Description**: Marketplace-related metadata for the knowledge kit.
- **Subfields**:
  - `publisher`: The publisher of the knowledge graph.
  - `contributor`: List of contributors.
  - `status`: Current status (e.g., "Published").
  - `icon`: An icon representing the project.
  - `tags`: A list of tags relevant to the graph.
  - `subject`: The subject or category of the graph.
  - `type`: The type of the graph (e.g., "Tutorial", "Demo").
- **Example**:
  ```yaml
  marketplace:
    publisher: sd:Stardog
    contributor:
        - sd:users:mike
    status: Published
    icon: "learning"
    tags:
        - SPARQL
        - Studio
    subject:
        - General
    type:
        - Tutorial
    initialSearch: "`http://stardog.com/tutorial/ABBA`"
  ```

### `publisher`
- **Type**: `string`
- **Description**: The publisher of the knowledge kit.
- **Example**:
  ```yaml
  publisher: sd:Stardog
  ```

### `contributor`
- **Type**: `array of strings`
- **Description**: List of contributors to the project.
- **Example**:
  ```yaml
  contributor:
    - sd:users:mike
  ```

### `status`
- **Type**: `string`
- **Description**: The current status of the knowledge kit (e.g., "Published", "Draft", "Archive").
- **Example**:
  ```yaml
  status: Published
  ```

### `icon`
- **Type**: `string`
- **Description**: Icon used to represent the kit in interfaces.
- **Example**:
  ```yaml
  icon: "learning"
  ```

### `primaryConcept`
- **Type**: `string`
- **Description**: URI of the primary concept represented by the kit.
- **Example**:
  ```yaml
  primaryConcept: "http://stardog.com/tutorial/Band"
  ```

### `initialSearch`
- **Type**: `string`
- **Description**: A SPARQL query or URI representing the initial search or focus of the knowledge kit.
- **Example**:
  ```yaml
  initialSearch: "`http://stardog.com/tutorial/ABBA`"
  ```

### `kitDb`
- **Type**: `string`
- **Description**: The database name associated with the kit.
- **Example**:
  ```yaml
  kitDb: "kit-starwars"
  ```
