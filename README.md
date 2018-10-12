# ALOOF Relations
In this pipeline, we implemented some methods to extract relations (such as hasShape, isA, partOf, among others) about objects that are usually located in domestic evironments (house, rooms). This implementation is part of the project ALOOF (https://project.inria.fr/aloof/).

The goal of ALOOF is to equip autonomous systems with the ability to learn the meaning of objects, i.e. their perceptual and semantic properties and functionalities, from externalized knowledge sources accessible through the Web.

To run this pipeline, it is necessary to have installed Python 2.7.

## Installation
After clone the repository or download the source code, you must install the prerequisite Python packages listed in the file `requirements.txt`.

With `pip`, this is done with:

    $ pip install -r requirements.txt
 
## Configuration
In `src` folder you can find the code and in `resource` folder the resources that we were used.

If you want to change the paths of the input data, in the `main.py` file change these options:

- house_objects_path = "YOUR PATH"
- frame_raw_path = "YOUR PATH"
- visualgenome_raw_path = "YOUR PATH"
- conceptnet_raw_path = "YOUR PATH"

## Execution
The general way to run this program is the following:
```
 $ cd src/
 $ python main.py option
```
Where `option` could be:
- "objects", to extract house's objects.
- "attributes", to extract attributes of objects.
- "frames", to extract relations using Frame Semantics.
- "conceptnet", to extract relations from ConceptNet.

## Example
```
 $ python main.py attributes
```

## Outputs
```
<spoon> <usedFor> <eating>
<spoon> <locatedAt> <dishwasher>
<spoon> <isA> <utensil>
```
```
<http://dbpedia.org/resource/Spoon> <http://ns.inria.fr/deko/ontology/deko.owl#usedFor> <http://dbpedia.org/resource/Eating>
<http://dbpedia.org/resource/Spoon> <http://ns.inria.fr/deko/ontology/deko.owl#locatedAt> <http://dbpedia.org/resource/Dishwasher>
<http://dbpedia.org/resource/Spoon> <http://ns.inria.fr/deko/ontology/deko.owl#isA> <http://dbpedia.org/resource/Utensil>
```

## Notes
For the extraction of attributes, we used the model Word2vec. Specifically, we used the pre-trained vectors obtained from part of Google News dataset (about 100 billion words). This file is large and is not in this repository. You can download the file [here](https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit?usp=sharing) and use it to replace the file `resource/embeddings/googlenews_negative300.bin` in this repository.
