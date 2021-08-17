import os, sys
from lxml import etree
import fnmatch
from rdflib import ConjunctiveGraph, Namespace, exceptions
from rdflib import URIRef, RDFS, RDF, OWL, BNode, Literal
from rdflib.extras import infixowl
import requests
from bs4 import BeautifulSoup
import PyPDF2


enums = {}
elements = []

def get_pdf_enumvalue_description(value, my_text): 
    keywords=['Name','Data Type','Description','Example'] 
    #Enumeration Values
     
    print("Getting " + value +" enum value info from the PDF")          
    desc = ""
    for i in range(len(my_text)):
            #print(i)
        if value == my_text[i]:
            return my_text[i+2]
    return "Source PDF: Not found"


def get_pdf_prop_description(value, my_text): 
    value = value[0].upper() + value[1:]
    keywords=['Name','Data Type','Description','Example'] 
    #Enumeration Values
     
    print("Getting " + value +" prop info from the PDF")          
    desc = ""
    found = False
    count = 0
    for i in range(len(my_text)):
            #print(i)
        if value == my_text[i]:
            print("Found at ", i)
            k = 0
            i = i + 4
            while k < 1:
                if my_text[i].strip():
                    desc = desc + my_text[i]
                else:
                    k = k + 1   

                i = i + 1
            if desc:
                return desc

            """for j in range(i, 0, -1):
                print("My text:", my_text[j])
                if my_text[j]:
                    if my_text[j] in keywords:
                        count = count + 1
                        found = True
                    else:
                        if found:
                            print("Count ",count)
                            desc = ""
                            k = 0
                            i = i + 2
                            while k < count:
                                if my_text[i]:
                                    desc = desc + my_text[i]
                                    k = k +1
                                i = i + 1
                            return desc
            """            
    return "Source PDF: Not found"




def get_pdf_description(el, el_type, my_text):  
    keywords=['Name','Data Type','Description','Example'] 
     
    print("Getting info from the PDF")
    el_type=el_type[0].upper() + el_type[1:]
    print(el, el_type)       
    desc = ""
    for i in range(len(my_text)):
            #print(i)
        if (el == my_text[i] and el_type == my_text[i+2]) or (my_text[i] == (el + " " + el_type)):
            #print("acc")
            for j in range(i+2, len(my_text)):
                if len(my_text[j]) >= 8:
                    if (my_text[j][1] != ".") and (my_text[j][3] != ".") and (my_text[j][5] != ".") and (my_text[j][7] != "."):
                        desc = desc + my_text[j]  
                    else:
                        break
                else:
                    desc = desc + my_text[j] 
            if desc == "":
                desc = "No comment"
            #print("Found desc:", desc)
            desc = desc.replace("D3.1 e-CISE Data Model description  Copyright  ANDROMEDA Consortium. All rights reserved.","")
            desc = desc.replace("D.3.1 e-CISE Data Model description  Copyright  ANDROMEDA Consortium. All rights reserved.","")
            return "Source PDF: " + desc.strip().replace("\n","")
    if el_type == "Enumeration":
        #try to find with "Class" instead
        return get_pdf_description(el, "Class", my_text)
    if el_type == "Association Class":
        #try to find with "Class" instead
        return get_pdf_description(el, "Class", my_text)
    
    return "Source PDF: Not found"
    
    
def get_tag_no_ns(tname):
    if "}" in tname: 
        return tname[tname.index("}")+1:]
    else:
        return tname
        
class UnknownPrefixException(Exception):
    pass
    
def parse_dom(filename, sourcename, pdffile):
    """
    parse xml document from given filename and returns rdflib.ConjunctiveGraph instance containing OWL ontology statements
    """
    def reg_name(node):
        """
        recursively traverse document tree for named tags and store in a global map for later referencing
        """
        if "name" in node.attrib:
            tagmap[node.attrib["name"]] = node
            #print("reg_name", node.attrib)
        for child in node:
            reg_name(child)
            
    def resolve_type_instr(etype):
        if ":" in etype:
            #resolve prefixed to full qualified name
            prefix = etype[:etype.index(":")]
            if prefix in root.nsmap:
                #lookup from declared namespace
                full_prefix = root.nsmap[prefix]
                if "targetNamespace" in root.attrib and full_prefix == root.attrib["targetNamespace"]:
                    etype = etype[etype.index(":")+1:]
                else:
                    if full_prefix[-1] != "/": full_prefix += "#"
                    etype = full_prefix+etype[etype.index(":")+1:]
        return etype      
                  
    def convert_data_prop(node, my_class, my_class_name, my_text):
        node_name = node.attrib["name"]
        if (node_name+my_class_name) in elements:
            print(node_name + "processed!")
            return
        elements.append(node_name+my_class_name)
        etype = resolve_type_instr(node.attrib["type"])
        print(node_name + " is an data property of " + my_class_name)
        node_name = node_name[0].lower() + node_name[1:]
        g.add(( NS[node_name], RDF.type, OWL.DatatypeProperty ))
        #comment = get_description(my_class_name+" "+node_name, "prop")
        #if comment:
        #    g.add(( NS[node_name], RDFS.comment, Literal(comment)))
        comment = get_pdf_prop_description(node_name, my_text)
        if comment:
            g.add(( NS[node_name], RDFS.comment, Literal(comment)))
        
        g.add(( NS[node_name], RDFS.range, URIRef(etype) ))
        g.add(( NS[node_name], RDFS.domain, URIRef(my_class) ))
        if "minOccurs" in node.attrib:
            if node.attrib["minOccurs"] != "0":
                print("========== min ================")
                infixowl.Restriction(NS[node_name], graph=g, minCardinality=Literal(int(node.attrib["minOccurs"])))
        if "maxOccurs" in node.attrib:
            if node.attrib["maxOccurs"] != "unbounded":
                print("========== max ================")
                infixowl.Restriction(NS[node_name], graph=g, maxCardinality=Literal(int(node.attrib["maxOccurs"])))

                
        


    def convert_object_prop(node, my_class, my_class_name, ename, my_text, nary=False):
        print(ename + " is an object property of " + my_class_name)
        node_name = node.attrib["name"]
        if (node_name+my_class_name) in elements:
            print(node_name + "processed!")
            return
        #print(child_name)
        g.add((NS[property_prefix+node_name], RDF.type, OWL.ObjectProperty))
        g.add((NS[property_prefix+node_name], RDFS.domain, URIRef(my_class)))  
        etype = resolve_type_instr(node.attrib["type"])
       
        if "http" in etype:
            g.add((NS[property_prefix+node_name], RDFS.range, URIRef(etype)))
        else:
            g.add((NS[property_prefix+node_name], RDFS.range, URIRef(NS[etype])))
        #comment = get_description(my_class_name+" "+ etype, "objectprop")
        #if comment:
        #    g.add(( NS[property_prefix+node_name], RDFS.comment, Literal(comment)))
        if nary:
            g.add(( NS[property_prefix+node_name], RDFS.comment, Literal("Association relation")))     
        else:
            comment = get_pdf_prop_description(node_name, my_text)
            if comment:
                g.add(( NS[property_prefix+node_name], RDFS.comment, Literal(comment)))

        
        elements.append(node_name+my_class_name)
        if "minOccurs" in node.attrib:
            if node.attrib["minOccurs"] != "0":                
                infixowl.Restriction(NS[node_name], graph=g, minCardinality=Literal(int(node.attrib["minOccurs"])))
        if "maxOccurs" in node.attrib:
            if node.attrib["maxOccurs"] != "unbounded":
                infixowl.Restriction(NS[node_name], graph=g, maxCardinality=Literal(int(node.attrib["maxOccurs"])))


    def convert_nary_relation(node, my_class, my_class_name, ename, my_text):
        #print(ename + " is an nary class")
        if ename in elements:
            print(ename + "processed!")
            return
        elements.append(ename)
        print("Convert nary: class=" + my_class_name + ", ename=" + ename)
        print("New name:", my_class_name, node[0].attrib["name"])
        # Just for ECISE
        ename = ename.replace("Rel","")
        #print(node)
        g.add((NS[my_class_name+ename], RDF.type, OWL.Class))
        g.add((NS[my_class_name+ename], RDFS.label, Literal(my_class_name +  node[0].attrib["name"]))) 
        #g.add((NS[my_class_name+ename], RDFS.comment, Literal("Association class"))) 
        g.add((NS[my_class_name+ename], RDFS.subClassOf, URIRef("http://melodi.irit.fr/ontologies/ecise#AssociationClass") ))
        g.add((NS[property_prefix+"Involved"+my_class_name], RDF.type, OWL.ObjectProperty))
        #g.add((NS[property_prefix+"Involved"+my_class_name], RDFS.comment, Literal("Nary relation"))) 
        g.add((NS[property_prefix+"Involved"+my_class_name], RDFS.range, URIRef(my_class)))  
        g.add((NS[property_prefix+"Involved"+my_class_name], RDFS.domain, URIRef(NS[my_class_name+ename]))) 
        #comment = get_description(my_class_name+" "+ ename, "objectprop")
        #if comment:
        #    g.add(( NS[property_prefix+ename], RDFS.comment, Literal(comment) ))  
        #    g.add(( NS[my_class_name+ename], RDFS.comment, Literal(comment) ))  
        comment = get_pdf_description(my_class_name+node[0].attrib["name"], "Association Class", my_text)
        if comment:             
            g.add(( NS[my_class_name+ename], RDFS.comment, Literal(comment) )) 
                                
        #Supposed that the first relation is for connecting the other class                     
        for i in range(len(node)):           
            child = node[i]  
            if "name" in child.attrib:
                child_name = child.attrib["name"]

                #frist child
                if i == 0:
                    if (child.tag == "{http://www.w3.org/2001/XMLSchema}element") and ("type" in child.attrib):
                        child.attrib["name"] = "Involved" + child.attrib["name"]
                        convert_object_prop(child, my_class+ename, my_class_name+ename, child_name, my_text, True)
                        continue
                #g.add((NS[property_prefix+child_name], RDF.type, OWL.ObjectProperty))
                #g.add(( NS[property_prefix+child_name], RDFS.comment, Literal("Nary relation") ))  
                #g.add((NS[property_prefix+child_name], RDFS.domain, URIRef(NS[ename]))) 
                #print("Processing ", child_name, child.attrib, child.tag) 
                if (child.tag == "{http://www.w3.org/2001/XMLSchema}element") and ("type" in child.attrib):

                    etype = resolve_type_instr(child.attrib["type"])

                    if XSD in etype:
                        convert_data_prop(child, my_class + ename, my_class_name + child_name, my_text)
                    else:
                        convert_object_prop(child, my_class+ename, my_class_name+ename, child_name, my_text)

                else:
                    if len(child)>0:
                        if child[0].tag == "{http://www.w3.org/2001/XMLSchema}complexType":

                            extension = child[0][0][0]
                    #print(extension.attrib)
                            if len(extension)>0:
                                if "base" in extension.attrib:
                                    if extension.attrib["base"] == "rel:Relationship":
                                        if len(extension[0]) > 1:                       
                                            # Just for CISE files:

                                            #convert_nary_relation(extension[0], my_class+ename, node[0].attrib["name"], child_name)  
                                            convert_nary_relation(extension[0], my_class+ename, my_class_name+ename, child_name, my_text)  
                                        else:
                                            #print(my_class+ename)
                                            #Just for CISE files
                                            #convert_object_prop(extension[0][0], my_class+ename, node[0].attrib["name"], child_name)

                                            convert_object_prop(extension[0][0], my_class+ename, my_class_name+ename, child_name, my_text)
                 
    def convert_enum(node, sourcename):
        node_name = node.attrib["name"]
        print(node_name + " is an enumeration")        
        #g.add(( NS[node_name], RDF.type, RDFS.Datatype))
        if len(node)>0:
            if node[0][0].text:
                g.add(( NS[node_name], RDFS.comment, Literal("Source: " + sourcename + " - " + node[0][0].text))) 
        else:
            #comment = get_description(node_name,"enum")
            #if comment:
            #    g.add(( NS[node_name], RDFS.comment, Literal(comment)))  
            comment = get_pdf_description(node_name, "Enumeration", my_text)
            if comment:
                g.add(( NS[node_name], RDFS.comment, Literal(comment)))   
        g.add(( NS[node_name], RDF.type, OWL.Class))
        g.add(( NS[node_name], RDFS.subClassOf, URIRef("http://melodi.irit.fr/ontologies/ecise#EnumerationType")))
        #g.add(( NS[node_name], RDFS.subClassOf, OWL.Thing))
        #g.add(( NS[node_name + "_Enumeration"], RDF.type, OWL.NamedIndividual))
        #g.add(( NS[node_name + "_Enumeration"], RDF.type, URIRef("http://melodi.irit.fr/ontologies/ecise#Enumeration")))

        #get all child of the last node (representing the content)   
        for child in node[len(node)-1]:
            if child.tag == "{http://www.w3.org/2001/XMLSchema}enumeration":
                value = child.attrib["value"].strip()
                value = value.replace(" ","_")
                value = value.replace("/","_")
                value = value.replace("(","_")
                value = value.replace(")","")
                        #print("Enumeration - Individual, value =",  value)
                        #print( NS[ename + "_" +  value])
                g.add(( NS[node_name + "_" +  value], RDF.type, OWL.NamedIndividual))
                g.add((NS[node_name + "_" +  value], RDF.type,  NS[node_name]))
                #g.add(( NS[node_name + "_" +  value], URIRef("http://melodi.irit.fr/ontologies/ecise#hasValue"),  Literal(value)))
                #g.add(( NS[node_name + "_Enumeration"], URIRef("http://melodi.irit.fr/ontologies/ecise#hasValue"), NS[node_name + "_" +  value]))
                g.add(( NS[node_name  + "_" +  value], RDFS.label, Literal(value)))
                if len(child) > 0:
                    g.add((NS[node_name  + "_" +  value], RDFS.comment, Literal("Source: " + sourcename + " - " + child[0][0].text))) 
                #comment = get_description(node_name  + " " +  value,"enumvalue")
                #if comment:
                #    g.add(( NS[node_name  + "_" +  value], RDFS.comment, Literal(comment)))
                comment = get_pdf_enumvalue_description(value, my_text)
                if comment:
                    g.add(( NS[node_name  + "_" +  value], RDFS.comment, Literal(comment))) 
                    

     
    def convert_class(node, sourcename):
        my_class_name = node.attrib["name"]
        myclass = node
        g.add((NS[my_class_name], RDF.type, OWL.Class))
        g.add((NS[my_class_name], RDFS.label, Literal(my_class_name)))        
        # get Parent class
        # if not herited
        content = 0
        if node[0].tag == "{http://www.w3.org/2001/XMLSchema}annotation":
            print("Get description from XSD")
            if node[0][0].text:
                g.add((NS[my_class_name], RDFS.comment, Literal("Source: " + sourcename + " - " + node[0][0].text) ))
            content = 1
        
        if node[content].tag ==  "{http://www.w3.org/2001/XMLSchema}sequence":
            childs = node[content]
        else:    
            my_parent_class = node[content][0].attrib["base"]
            my_parent_class_prefix = my_parent_class[0:my_parent_class.index(":")]
            my_parent_class_name = my_parent_class[my_parent_class.index(":")+1:]
            g.add((NS[my_class_name], RDFS.subClassOf, URIRef(root.nsmap[my_parent_class_prefix]+my_parent_class_name)))            
            comment = get_pdf_description(my_class_name, "class", my_text)
            if comment:
                g.add(( NS[my_class_name], RDFS.comment, Literal(comment) ))
            childs = node[content][0][0]
       
        for node in childs:
            if "name" in node.attrib:
                ename = node.attrib["name"]
                #print("==> Processing ", ename, myclassname)
                if (ename+my_class_name) in elements:
                    print(ename + " processed")
                    return
                #elements.append(ename)
                #print("convert_element:", ename, "node attribute:", node.attrib, "node tag:", node.tag)
                    
                #convert relation
                if node.tag == "{http://www.w3.org/2001/XMLSchema}element" and "type" not in node.attrib:
                    #print("Assoc")
                    extension = node[0][0][0]
                    #print(extension.attrib)
                    #print("extension:", extension.attrib["name"], "node attribute:", extension.attrib, "node tag:", extension.tag)
                    if len(extension)>0:
                        if "base" in extension.attrib:
                            if extension.attrib["base"] == "rel:Relationship":
                                if len(extension[0]) > 1:
                                    convert_nary_relation(extension[0], NS[my_class_name], my_class_name, ename,my_text)                                    
                                else:
                                    convert_object_prop(extension[0][0], NS[my_class_name], my_class_name, ename, my_text)                          
                                                                
                #convert property
                elif "type" in node.attrib:
                    etype = resolve_type_instr(node.attrib["type"])
                    #convert data property
                    if XSD in etype:
                        convert_data_prop(node, NS[my_class_name], my_class_name, my_text)     
                    #convert object property
                    else:
                        convert_object_prop(node, NS[my_class_name], my_class_name, ename, my_text)
        
    def convert_element(root, sourcename):
        """
        handle element conversion
        """
        #print(root.getparent().attrib)
        #convert class
        #print( len(root[0][0]))
        #print(root.attrib)
        #print(root[0].attrib)  
        if root.tag == "{http://www.w3.org/2001/XMLSchema}complexType":
            convert_class(root, sourcename)
        #convert enum                    
        elif root.tag == "{http://www.w3.org/2001/XMLSchema}simpleType":
            convert_enum(root, sourcename)

        return
            
    with open(filename, "r") as f: root = etree.parse(f).getroot()
    
    tagmap = {}
    types = []
    reg_name(root)
    
    #predeclaration
    XSD = "http://www.w3.org/2001/XMLSchema"
    els = []
    els.append(".//{%s}%s" % (XSD, "simpleType"))
    els.append(".//{%s}%s" % (XSD, "complexType"))
    #elements.append(".//{%s}%s" % (XSD, "element"))
    #elements.append(".//{%s}%s" % (XSD, "attribute"))
    xs_st = ".//{%s}%s" % (XSD, "simpleType")
    xs_ct = ".//{%s}%s" % (XSD, "complexType")
    xs_el = ".//{%s}%s" % (XSD, "element")
    xs_at = ".//{%s}%s" % (XSD, "attribute")
    
    #graph
    g = ConjunctiveGraph()
   
    
    for k, v in root.nsmap.items():
        if k is not None:
            g.bind(k, v)
            #print("Bind ", k, v)

    if "targetNamespace" in root.attrib:
        NS = Namespace(root.attrib["targetNamespace"])
    else:
        NS = Namespace("http://melodi.irit.fr/ontologies/example#")
    
    g.bind(None, NS)
    g.bind("owl", OWL)
    g.bind("xsd", XSD+"#")
    g.bind("ecise", "http://melodi.irit.fr/ontologies/ecise")   
    property_prefix = "has"
    g.add(( URIRef("http://melodi.irit.fr/ontologies/ecise#EnumerationType"), RDFS.subClassOf, OWL.Thing))
    g.add((URIRef("http://melodi.irit.fr/ontologies/ecise#AssociationClass"), RDFS.subClassOf, OWL.Thing))
    #print("Root",root[0].attrib)

    for element in els:
        #print("PROCESSING ", element)
        for el in root.findall(element):
            #convert only first level child nodes
            if el.getparent().tag == "{http://www.w3.org/2001/XMLSchema}schema":                
                convert_element(el, sourcename) 

                
         
    return g

if __name__ == "__main__":

    my_text = []
    summary = []
    if len(sys.argv) > 3:

        print("Reading the PDF..")
        
        pdfFileObj = open(sys.argv[3], 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj, overwriteWarnings=False)
        count = pdfReader.numPages
        pdf_text = ""
        for i in range(count):
              
            if i>=30: 
                page = pdfReader.getPage(i)         
                pdf_text = pdf_text + page.extractText()
            #if i==34:
            #    print(page.extractText())
        pdfFileObj.close()
        my_text = pdf_text.split("\n")
    
    if len(sys.argv) > 2:
        
        #my_text = ""
        print("=========== PARSING FILES ===============")
        my_graph = ConjunctiveGraph()
        sourcename = sys.argv[1]
        if os.path.isfile(sys.argv[2]):
            print("Parsing file:", sys.argv[2])
            my_graph = parse_dom(sys.argv[2], sys.argv[1], my_text)
            summary.append(sys.argv[2] + ": " + str(len(graph)) + "triples")
            '''
            print("=========== SERIALIZING  ===============")
            print("Graph size:",len(my_graph))
            out_put = os.path.join(os.path.dirname(sys.argv[2]),'ontology-ecise.ttl')
            print("Output: ",out_put)
          
            my_graph.update("""Prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix owl: <http://www.w3.org/2002/07/owl#> 
                insert
                {
                ?p rdfs:domain ?s.
                }
                where 
                {
                ?s rdfs:subClassOf ?o.
                ?p rdfs:domain ?o.
                ?p a owl:ObjectProperty.
                }""")   

            my_graph.update("""Prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix owl: <http://www.w3.org/2002/07/owl#> 
                insert
                {
                ?p rdfs:domain ?s.
                }
                where 
                {
                ?s rdfs:subClassOf ?o.
                ?p rdfs:domain ?o.
                ?p a owl:DatatypeProperty.
                }""") 

            #add source description
            query = 'INSERT {?s <http://melodi.irit.fr/ontologies/ecise#from' + sourcename[0].upper()+ sourcename[1:] + '> true.} ' +  """WHERE {
                  ?s ?p ?o.
               }"""

            my_graph.update(query) 
            my_graph.serialize(out_put, format='turtle')
            
            '''
        else:
            for path,dirs,files in os.walk(sys.argv[2]):
                for f in fnmatch.filter(files,'*.xsd'):
                    fullname = os.path.abspath(os.path.join(path,f))
                    print("Parsing file:", fullname)
                    graph = parse_dom(fullname, sys.argv[1], my_text)
                    graph.serialize(fullname[:-3] + "ttl", format='turtle')
                    summary.append(fullname + ": " + str(len(graph)) + "triples")
                    my_graph = my_graph + graph
                    
        print("=========== SERIALIZING  ===============")
        print("Graph size:",len(my_graph))
        out_put = os.path.join(sys.argv[2],'ontology-ecise.ttl')
        print("Output: ",out_put)
        my_graph.update("""Prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix owl: <http://www.w3.org/2002/07/owl#> 
                insert
                {
                ?p rdfs:domain ?s.
                }
                where 
                {
                ?s rdfs:subClassOf ?o.
                ?p rdfs:domain ?o.
                ?p a owl:ObjectProperty.
                }""")   

        my_graph.update("""Prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix owl: <http://www.w3.org/2002/07/owl#> 
                insert
                {
                ?p rdfs:domain ?s.
                }
                where 
                {
                ?s rdfs:subClassOf ?o.
                ?p rdfs:domain ?o.
                ?p a owl:DatatypeProperty.
                }""") 

            #add source description
        query = 'INSERT {?s <http://melodi.irit.fr/ontologies/ecise#from' + sourcename[0].upper()+ sourcename[1:] + '> true.} ' +  """WHERE {
                  ?s ?p ?o.
               }"""

        my_graph.update(query) 
        my_graph.serialize(out_put, format='turtle')
        with open("summary-ecise.txt", "w") as outfile:
            outfile.write("\n".join(summary))
            
            
    else:
        print("============= USAGE ================")
        print("python3 [scriptname] [source name]  [Folder containing XSD files] [Optional PDF file]")
    
