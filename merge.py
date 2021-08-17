from rdflib import Graph
import sys

def merge(file1, file2, output):
    g1 = Graph()
    g1.parse(file1, format="turtle")
    g2 = Graph()
    g2.parse(file2, format="turtle")  
    g = Graph() 
    g = g1 + g2
    g.serialize(output, format='turtle')




if __name__ == "__main__":
    merge(sys.argv[1], sys.argv[2], sys.argv[3] )
