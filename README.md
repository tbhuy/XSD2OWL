# XSD2OWL
XSD2OWL is a python script for transforming XSD to OWL.
The script is based on [the work of Pebbie](https://gist.github.com/pebbie/5704765) and the transformation rules of [OntMalizer](https://github.com/srdc/ontmalizer). 


## Major improvements:
  * Transformation of all schema files into a single ontology (not in Pebbie's work)
  * Declaration of domain, range and enumeration (list of instances) (not in Pebbie's work)
  * Simplification of the axiom set (compared with OntMalizer)
  * Declaration of cardinalities


## Usage

```
python3 xsd2owl [Folder containing XSD files]
```
