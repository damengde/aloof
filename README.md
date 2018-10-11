# ALOOF
ALOOF project: https://project.inria.fr/aloof/

In this pipeline, we implemented some methods to  extracts relations, such as hasShape, isA, partOf among others,  about house’s objects:

## Installation

After cloning the repository or otherwise downloaded the source code, you must installs the prerequisite Python packages listed in the file *requirements.txt*.
With *pip*, this is done with:

    $ pip install -r requirements.txt
 
## Configuration
- House's objects
- Attributes
- Frames
- ConceptNet

In `src` folder, you can find the code and in `resource` folder, the resources that we were used.

## Execution:
To run this program, it is necessary to have installed Python 2.7 or higher.

The general way to run this program is the following:
```
 $ cd src/
 $ python main.py option
```
Where option could be:
- "objects", to extract house's objects.
- "attributes", to extract attributes of objects.
- "frames", to extract relations using Frame Semantics.
- "conceptnet", to extract relations from ConceptNet.

## Example:
```
 $ python main.py attributes
```

## Notes:
If you want to change the paths of the input data, in the `main.py` file change these options:

- house_objects_path = "YOUR PATH"
- frame_raw_path = "YOUR PATH"
- visualgenome_raw_path = "YOUR PATH"
- conceptnet_raw_path = "YOUR PATH"
