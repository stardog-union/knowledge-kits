This is a knowledge graph focused on a Manufacturing Digital Thread use case. In this demo, a product quality SME is investigating to determine the possible root cause for Customer Feedback about beer. 

The product quality SME looks at the Suppliers, Raw Materials, Recipes, Equipment, Plants, Sensors, Products, and Distributors that are connected to Customer Feedback. It brings together data from many different domains and sources.

Pictured below is the basic data model for this use case. The data was generated and/or derived from using [Mockaroo](https://www.mockaroo.com/) and [Open Data DC](https://opendata.dc.gov/) datasets.

![Model in Explorer](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_schema.png)

# Getting Started

We will browse this demo in [Explorer](https://docs.stardog.com/stardog-applications/explorer/), Stardog's no-code search and visualization tool that allows anyone to explore complex data fabrics easily.

To get started, **click on "Open in Explorer"**, the blue CTA in the header of this demo. Alternatively, you can install this kit into your own database to use it in [Designer](https://docs.stardog.com/stardog-applications/designer/) or [Studio](https://docs.stardog.com/stardog-applications/studio/).

Once in Explorer, we'll browse the relationships of Munich Dunkel Keg 50L, an instance of the Finished Product class. You can expand grouped instances with a single click and see the details of each instance with a right click.

![Single-click and double-click](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_overview_2.gif)

You can also switch between the views "List" and "Graph" using the icons in the upper-left corner:
![List view](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_overview_3.gif)
ttps://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_overview_3.gif.gif

To visualize the entire data model, execute a blank search.

![Full data model](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_overview_4.gif)

# Query Builder

Query Builder allows you to visually uncover insights based on classes, relationships, and attributes.

![Query Builder overview](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_qbuilder_1.gif)

To get started, click on Query Builder, located to the right of the search bar. As an exercise, try to look for trucks that had skids stored on them that received customer feedback that their beer was flat.

![Exercise](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_qbuilder_2.png)
![Exercise](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_qbuilder_3.png)

If you found Truck *Truck 002*, congratulations! If you didn't, review all fields and run your query again.

# Reasoning

Reasoning enables Stardog's Inference Engine, which associates related information to infer new connections. **You can turn it on in Explorer by clicking on the settings icon, located to the right of the navbar.**

In this demo, if a truck has a temperature sensor that has sensor outputs equal to or greater than 50 degrees Fahrenheit, reasoning infers that the truck has an anomaly associated with it.

![Reasoning overview](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_reasoning_2.png)
![Reasoning overview](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_reasoning_3.png)

For example, reasoning infers that Truck 002 has 11 anomalies because it has a temperature sensor that has 11 outputs equal to or greater than 50 degrees Fahrenheit. Here's how the data looks with reasoning off and then with reasoning on:

![Reasoning off](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_reasoning_4_and_5.png)

Reasoning in action: use Query Builder to find Truck 002 (label) and expand its anomalies. Don't forget to enable reasoning by clicking on the settings icon before running your search.

![Reasoning results](https://stardog-knowledge-kits.s3.amazonaws.com/beer1.0/beer_reasoning_6.gif)