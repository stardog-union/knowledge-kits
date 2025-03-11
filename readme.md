# Stardog Knowledge Kits

Knowledge Kits define the structure, data, and metadata for treating knowledge graphs in a "KG as Code" manner. Coupled with some simple tooling, they offer a standardized way to automate, version, and share graph deployments, making it easier to manage complex graph systems. 

# Getting Started

## Installation

```bash
# set up your venv
$ python -m venv venv
# activate it
$ source venv/bin/activate
# install the package
$ pip install -e .
```

## Creating your first Kit

```bash
$ mkdir mykit
$ cd mykit
$ kits init --name my-first-kit --group tutorial --version 1.0
```

This creates a skeleton for your new Kit. Go into the `kit.yaml` file and update the metadata to describe your Kit. Copy in your own data and model, create a complete readme. Then you're ready to install.

## Installing your Kit

### Setting up your Environment

Create a new environment file from the example.

```bash
$ cp .env.example .env
```

NEVER COMMIT YOUR `.env` FILE TO VERSION CONTROL.

The `default_target` defines which target to use on the CLI when none is specified.

You must then define your targets, a target is a Stardog Endpoint. Targets have a name, which is used on the CLI to lieu of a server & credentials. They also have the server URL in addition to the credentials. The format for definining a target is `[target name]_[property]=[value]`. 

The only required property is `server`, which is the location of the Stardog endpoint:

```bash
my_endpoint_server="https://abc123.stardog.cloud:5820"
```

You must also specify your credentials for the endpoint. If you have a [Stardog Password File](https://docs.stardog.com/operating-stardog/security/managing-users-and-roles#using-a-password-file), you can omit credentials in your environment, the Kits CLI will use the password file. 

To specify credentials in your environment, you use the properties `username` and `password`:

```bash
my_endpoint_username="the_username"
my_endpoint_password="the_password"
```

### Installation

```bash
$ kits install -t my_endpoint
```

## Uninstalling your Kit

```bash
$ kits uninstall -t my_endpoint
```

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

## Data Sources

For any of the [data](#data) which uses [mappings](#mappings), a Stardog [Data Source](https://docs.stardog.com/virtual-graphs/data-sources/) is required to create the virtual graph.

#### Describing a data source

The value of the `sources` key is an array of data source descriptors. The name of the data source should match the exact name of
the source as [defined in the data](#source).

Here is an example data source definition:

```yaml
  - name: CentralDatabricks
    options:
      jdbc.driver: "com.simba.spark.jdbc.Driver"
      jdbc.url : "jdbc:spark://example.cloud.databricks.com:443/default;transportMode=http;ssl=1;AuthMech=3;httpPath=/sql/1.0/endpoints/abcc123def456ghj789;UseNativeQuery=1"
      jdbc.username: "token"
      sql.schemas: "default"
      testOnBorrow: true
      validationQuery: "select 1"
```

The valid options here correspond to the set of valid [Data Source Configuration](https://docs.stardog.com/virtual-graphs/data-sources/data-source-configuration) options.

#### Passwords for data sources

Do NOT put these in your Kit. Kits belong in version control, but passwords do not.

To specify passwords for your data sources, you will need to update your `.env` file. The convention to follow when specifiying these credentials in your environment, is `[source name]_password=mypassword`. For the above data source descriptor example, we would specify the password as such:

```yaml
CentralDatabricks_password="abc123"
```


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
