This tutorial introduces the Inference Engine, one of the foundational aspects of a Knowledge Graph.

# Getting Started

To view the data model for this Kit in Explorer:

* Open Stardog Explorer and select the database into which you installed this Kit
* Open the Settings dialog by clicking the "sliders" icon in the upper right hand of the Explorer home page
  * Select the `music_data` graph
  * Select the `music` model
  * Click the `Save` button
* Click the `Visualize` button

You should see something like this:

![Music Schema](https://stardog-knowledge-kits.s3.amazonaws.com/music-schema.png)

If you want to explore the graph further you can click on any concept of interest and follow wherever the graph leads you.

# Getting started with Reasoning

Stardog's Inference Engine is built directly into the Platform and is typically enabled with a toggle in our tools. The Inference Engine uses your data model and data to dynamically infer _new facts_ in your knowledge graph. This process is typically referred to as inferencing or reasoning. While the Inference Engine does just one thing, infer new data, it is a very powerful mechanism that can be used to implement your [business logic](https://www.stardog.com/blog/where-does-business-logic-go/) on top of all of your enterprise data. 

Let's look at a simple example in our music tutorial dataset. We'll start by focusing on John Lennon. You can search for him, or navigate directly to his node using the search bar: ``http://stardog.com/tutorial/John_Lennon``. 

Paul McCartney and John Lennon were members of the Beatles and cowrote a lot of the group's work. We can see an example of that here:

![noco](https://stardog-knowledge-kits.s3.amazonaws.com/reasoning-nocowriter.png)

If I want to find all of the songs with cowriters, get a particular artist's cowriters, or find the most prolific pair of cowriters, I have to encode the business logic of what a cowriter is into my query. This is very typical with relational and plain graph systems. (The logic may also get put into an application tier.)

Knowledge Graphs provide another option, in the data model. Let's see how the Inference Engine can be used to perform this logic for us, without writing any code. We can see the structure of our graph above, and we know we want to directly link artists who match the co-writing "pattern". So _if_ we see that pattern, _then_ we infer they are cowriters:

```sparl
IF {
   ?song :writer ?artist .
   ?song :writer ?cowriter
   FILTER (?artist != ?cowriter)
}
THEN {
   ?artist :cowriter ?cowriter
}
```

This code already exists in our model, so to see this rule in action, we just need to turn on the Inference Engine in Explorer:

![enable reasoning](https://stardog-knowledge-kits.s3.amazonaws.com/enable-reasoning.png)

And as soon as you save your settings, you will see the cowriter relationships for John Lennon:

![inferred graph](https://stardog-knowledge-kits.s3.amazonaws.com/reasoning-cowriter.png)

If you jump to [Studio](https://cloud.stardog.com/), you can query this inferred data directly. You will need to make sure you toggle reasoning to *ON* within your Editor; it's at the top of the editor in the control bar next to the Run button.

```sparql
PREFIX : <http://stardog.com/tutorial/>

SELECT * {
    :Paul_McCartney :cowriter ?cowriter
}
```

One other thing the Inference Engine does that you can easily see in Explorer is classify all of our data based on our concept hierarchy (this is sometimes known as a taxonomy). Our data model says a few basic things:

* Songwriter, SoloArtist, and Band are specializations (aka subclasses) of Artist
* Songwriter, SoloArtist, and Producer are specializations (aka subclasses) of Person

The inference engine can leverage this information to infer new types for an individual. If you look at John Lennon's types, as shown below, you see his three explicit types that we've grouped together, `Songwriter`, `SoloArtist`, `Producer`, and his inferred types, `Artist` and `Person`:

![inferred graph](https://stardog-knowledge-kits.s3.amazonaws.com/reasoning-alltypes.png)

And like with our cowriter rule, we leverage this information via SPARQL:

```sparql
PREFIX : <http://stardog.com/tutorial/>

SELECT * {
    ?artist a :Artist
}
```

These "subclass of" statements are not written as rules; they're part of our concept definition in our data model. These are sometimes referred to as axioms, but you can think of them as built-in rules. Stardog supports a number of these built-in concepts based on the semantic web open standards, namely OWL and SWRL. For now, you don't need to worry about the details of those. You will primarily use rules to define your business logic, but you can take advantage of our built-ins, such as transitivity and inverses, whenever you need it. 

# Extending this example

If you want to build your own rules for this dataset, add any new rules you write to the `stardog-tutorial-music:music_schema` graph. To do this in Studio, go to Models, select the database where you've installed this kit, and select the `music` schema (which corresponds to the `stardog-tutorial-music:music_schema` graph). A "Confirm Namespace" dialogue will pop up. Under Prefix, select the default namespace (which will be blank in the dropdown), and hit Confirm. From there, navigate to the Text Editor. If you scroll to the bottom, you will see the cowriter rule we created above. You can use this as a guide for creating new rules for the dataset.