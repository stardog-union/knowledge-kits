This is part of the Stardog Getting Started series, which puts Knowledge Graph concepts in-action. This tutorial introduces `PATHS` queries. We'll work primarily in Studio.


# Getting Started

To view the data model for this Kit in Explorer:

* Open Stardog Explorer and select the database into which you installed this Kit
* Open the Settings dialog by clicking the "sliders" icon in the upper right hand of the Explorer home page
  * Select the `paths-tutorial-data` graph
  * Select the `stardog_paths-tutorial` model
  * Click the `Save` button
* Click the `Visualize` button

To explore further, enter a movie related term in the search box at the top of the page and click the hour-glass icon to search. Try double-clicking the node displayed in the search results. You can browse directly to Kevin Bacon using the search term ``http://www.imdb.com/name/nm0000102``.

# The Data Model

Pictured below is the basic data model for this dataset; in Explorer you can see all of the relationships that model concepts have with each other. These concepts, ex. `Movie`, also have additional attributes, such as `title` and `release year` which are not displayed in the Model Overview, but are browseable in Explorer. You will see all of the relationships and attributes when you browse the data model in Designer.

![Model in Explorer](https://docs.stardog.com/assets/images/kits/ml-tutorial-schema.png)

# Finding Kevin

As we noted above, you can find Kevin in Explorer with the search term ``http://www.imdb.com/name/nm0000102``. It's just as easy to find him with SPARQL:

```sparql
SELECT *
from <urn:stardog:tutorials:paths:1.0:paths-tutorial-data>
WHERE {
    ?s rdfs:label "Kevin Bacon" .
}
```

This returns Kevin Bacon's unique identifier in the knowledge graph. We can use that identifier to get more information about him. Let's return a graph of all of Kevin Bacon's incoming and outgoing edges:

```sparql
construct { 
    <http://www.imdb.com/name/nm0000102> ?p ?o . 
    ?s ?sp <http://www.imdb.com/name/nm0000102>} 
from <urn:stardog:tutorials:paths:1.0:paths-tutorial-data>
where {
    { <http://www.imdb.com/name/nm0000102> ?p ?o } 
    union 
    { ?s ?sp <http://www.imdb.com/name/nm0000102>}
}
```

The graph that results from this query shows us all of Kevin Bacon's direct neighbors, but that's not enough to answer our original question. For that, we need to go a few edges further into our graph.

# Bringing home the Bacon

To answer the underlying Kevin Bacon problem, we need to use `PATHS` queries. `PATHS` is a type of query, just like `SELECT`, `CONSTRUCT`, or `DESCRIBE`.

As you would expect, `PATHS` queries find the path(s) from one IRI to another. `PATHS` queries can help find specific types of paths as well, e.g. the shortest path or a path connected by a certain kind of relationship. Here’s a basic `PATHS` query:

```sparql
PATHS
from <urn:stardog:tutorials:paths:1.0:paths-tutorial-data>
    START ?x {?x rdfs:label "Kevin Bacon"}
    END ?y {?y rdfs:label "Nick Offerman"}
VIA {
    ?movie so:actor ?x.
    ?movie so:actor ?y.
} LIMIT 1
```


The first line says "I want to get from X to Y, but make sure that X has the name Kevin Bacon to start and Y has the name Nick Offerman to end". Each "hop" of the path will go from an x to a y. At the next stop y from the previous stop becomes x’ and goes to y’, then y’ becomes x" and so on. We know that we start at Kevin Bacon, but this ensures we stop when the y of the hop is Nick Offerman.

The `VIA` clause says how we want to get there. This one says we want to get there by finding a movie that both x and y have acted in.

We add `LIMIT 1` to get one path back, since by default a PATHS query returns any of the shortest paths and there’s likely to be more than one.

If you run this:

![run query](https://docs.stardog.com/assets/images/tutorials/getting-started-series/getting-started-5-bindings.gif)


you’ll see something that looks like a path, and we can tell that Nick Offerman is three degrees away from Kevin Bacon. If you click on *"See Bindings"*, you can see the movie that connects them (note your movies may not be the same as the example here). But all of these IRIs are not readable, and we don’t have actor names or titles because we did not explicitly ask for them. So let’s explicitly ask for them:

```sparql
PATHS
from <urn:stardog:tutorials:paths:1.0:paths-tutorial-data>
    START ?x {?x rdfs:label "Kevin Bacon"}
    END ?y {?y rdfs:label "Nick Offerman"}
VIA {
    ?movie so:actor ?x.
    ?movie so:actor ?y.
    
    ?movie rdfs:label ?title .
    ?x rdfs:label ?xName .
    ?y rdfs:label ?yName .
} LIMIT 1
```


The output looks the same, but now we can click on *"See Bindings"* to see how the connections are made. The easiest way to see the full picture is to click "Run to file" and export to .csv or your preferred file format. Then all the data is in front of you to tell the story in typical "Six Degrees of Kevin Bacon" fashion.

And just like that, we have solved the problem. And look how concise that query is! This is one of the benefits of a Knowledge Graph - since finding connections like this is part of the core use-case, the syntax has language designed to make it easy to write and understand. Think how challenging it would be to write this query in SQL based off of the `personMovies` table we might have used in a relational model.

# More with PATHS

You are not limited to simple paths and getting labels for each node in the path; the `VIA` clause can be used to express sophisticated conditions for path finding. This is how we'd amend our previous example to only find paths between Kevin Bacon and Nick Offerman in movies that have been released since 2010:

```sparql
PATHS
from <urn:stardog:tutorials:paths:1.0:paths-tutorial-data>
    START ?x {?x rdfs:label "Kevin Bacon"}
    END ?y {?y rdfs:label "Nick Offerman"}
VIA {
    ?movie so:actor ?x.
    ?movie so:actor ?y.
    
    ?movie rdfs:label ?title ; 
           so:copyrightYear ?year .
    
    ?x rdfs:label ?xName .
    ?y rdfs:label ?yName .
    FILTER (?year >= 2010)
} LIMIT 1
```

Try out some changes to this query on your own, such as finding all paths that do not go through "A Few Good Men", or with different start/end points. You could even go to Explorer to find new ways this dataset is connected and explore those new paths to knowledge.