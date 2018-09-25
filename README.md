# ALOOF
ALOOF project: https://project.inria.fr/aloof/

In this pipeline, we implemented some methods to  extracts relations, such as hasShape, isA, partOf among others,  about house’s objects:

- House's objects
- Attributes
- Frames
- ConceptNet

For more information about these methods, we will publish a paper

In "src" folder, you can find the code and in "resource" folder, the resources that we were used.

## Execution:
To run this program, it is necessary to have installed Python 2.7 or higher.

The general way to run this program is the following:
```
 $ python main.py option
```
Where option could be:
- "objects", to extract house's objects.
- "attributes", to extract attributes of objects.
- "frames", to object relations using  using Frame Semantics.
- "conceptnet", to extract relations from ConceptNet.

## Example:
```
 $ python main.py "attributes"
```

## Notes:
If you want to change the paths of the input data, in the main.py file change these options:

- house_objects_path = "YOUR PATH"
- frame_raw_path = "YOUR PATH"
- visualgenome_raw_path = "YOUR PATH"
- conceptnet_raw_path = "YOUR PATH"
