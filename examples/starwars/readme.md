This is a knowledge graph focused on the universe of Star Wars. The files used to create this dataset were sourced from https://www.kaggle.com/datasets/jsphyg/star-wars.


# Getting Started

We will browse this demo in [Explorer](https://docs.stardog.com/stardog-applications/explorer/), Stardog's no-code search and visualization tool that allows anyone to explore complex data fabrics easily.

To get started, **click on "Open in Explorer"** under **Try It Out**.

Once in Explorer, we'll first browse the relationships of Tatooine, an instance of the class Planet. You can expand grouped instances with a single click and see the details of each instance with a right click.

![Single-click and double-click](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_overview_2.gif)

You can also switch between the views "List" and "Graph" using the icons in the upper-left corner:

![List view](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_overview_3.gif)

To visualize the entire data model, execute a blank search.

![Full data model](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_overview_4.gif)


# Query Builder

Query Builder allows you to visually uncover insights based on classes, relationships, and attributes.

![Query Builder overview](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_qbuilder_1.gif)

To get started, click on Query Builder, located to the right of the search bar. As an exercise, try to look for characters whose home planet is located in the Gold System:

![Exercise](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_qbuilder_2.png)

![Exercise](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_qbuilder_3.png)

If you found the character *Lando Calrissian*, congratulations! If you didn't, review all fields and run your query again.

# Reasoning

Reasoning enables Stardog’s Inference Engine, which associates related information to infer new connections. **You can turn it on in Explorer by clicking on the settings icon, located to the right of the navbar.**

In this demo, reasoning classifies spacecraft with a hyperdrive rating of 1.5 or less as Fast Hyperdrive.

![Reasoning overview](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_reasoning_1.png)

For example, reasoning classifies spacecraft arc-170 as Fast Hyperdrive because it has a 1.0 hyperdriveRating:

![Reasoning example](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_reasoning_2.png)

Reasoning in action: select the class Spacecraft and search for arc-170 to see its inferred sub-class (Fast Hyperdrive). Don't forget to enable reasoning by clicking on the settings icon before running your search.

![Reasoning results](https://stardog-knowledge-kits.s3.amazonaws.com/star-wars-demo_reasoning_3.gif)
