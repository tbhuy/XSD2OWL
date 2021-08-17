from rdflib import Graph
import sys

def insert(ontology_file, axioms_file, output):
    g1 = Graph()
    g1.parse(ontology_file, format="turtle")
    g2 = Graph()
    g2.parse(axioms_file, format="turtle")  
    g = Graph() 
    g = g1 + g2
    g.serialize(output, format='turtle')




if __name__ == "__main__":
    insert(sys.argv[1], sys.argv[2], sys.argv[3] )