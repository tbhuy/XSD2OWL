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

def get_pdf_description(el, el_type, my_text):   
     
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
            return "From D3.1: " + desc.strip().replace("\n","")
    if el_type == "Enumeration":
        #try to find with "Class" instead
        return get_pdf_description(el, "Class")
    if el_type == "Association Class":
        #try to find with "Class" instead
        return get_pdf_description(el, "Class")
    
    return "From D3.1: Not found"
    
    
 
#Just for cise documentation
#http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/info/
def get_description(el, el_type):
    
    print("Getting info from the EMSA website")
    if el_type == "prop":
        my_class = el.split()[0]
        my_prop = el.split()[1]
        #print(my_prop)
        #print("Getting information: http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/" + my_class + ".html")
        
        try:
            if enums.get(my_class):
                #print("cached")
                my_div = BeautifulSoup(enums.get(my_class), 'html.parser')
            else:
                page = requests.get("http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/" + my_class + ".html")
                soup = BeautifulSoup(page.text, 'html.parser')
                my_div = soup.find_all("table", {"class": "table-condensed"})[0]   
                page.close()    
            anchor = 'name="'+ my_class.lower()+ "_" + my_prop.lower() +'"'
            #print("find:", anchor)
            if my_div:                     
                my_rows = my_div.find_all("tr")
                for row in my_rows:
                    if anchor in row.prettify(): 
                        #print(row.find_all("td")[2].get_text())                
                        return "Source EMSA-CISE: :" + row.find_all("td")[2].get_text().strip().replace("\n","")
        except:
            #print("Error")
            return "Source EMSA-CISE: : not found"

    elif el_type == "class":
        #print("Getting information: http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/" + el+".html")
        page = requests.get("http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/" + el+".html")
        soup = BeautifulSoup(page.text, 'html.parser')
        my_div = soup.find_all("div", {"class": "container"})
        if my_div:                     
            #print("Caching", el)
            enums[el] = my_div[0].prettify()
            my_row = my_div[0].find_all("div", {"class": "row"})
            if my_row:               
                return "Source EMSA-CISE: : " + my_row[3].get_text().strip().replace("\n","")
        

    elif el_type == "objectprop":
        my_class = el.split()[0]
        my_object = el.split()[1].replace("Rel","")
        #print(my_object)
        #print("Getting information: http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/" + my_class + ".html")
       
        try:
            if enums.get(my_class):
                #print("cached")
                my_div = BeautifulSoup(enums.get(my_class), 'html.parser')
            else:
                page = requests.get("http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/" + my_class + ".html")
                soup = BeautifulSoup(page.text, 'html.parser')
                my_div = soup.find_all("table", {"class": "table-condensed"})[1]  
                page.close()     
            if "http" in my_object:
                my_object=my_object[my_object.rindex("/")+1:]
            anchor = 'name="'+ my_class.lower()+ "_" + my_object.lower() +'"'
            #print("find:", anchor)
            if my_div:                     
                my_rows = my_div.find_all("tr")
                for row in my_rows:
                    if anchor in row.prettify(): 
                        #print(row.find_all("td")[2].get_text()  )                
                        return "Source EMSA-CISE: : " + row.find_all("td")[2].get_text().strip().replace("\n","")
                anchor = my_object.lower() +'"'
                #print("find", anchor)
                for row in my_rows:
                    if anchor in row.prettify(): 
                        #print(row.find_all("td")[2].get_text())              
                        return "Source EMSA-CISE: : " + row.find_all("td")[2].get_text().strip().replace("\n","")
        except:
            #print("Error")
            return "Source EMSA-CISE: : not found"       
              
    elif el_type == "enum":        
        res = [idx for idx in range(len(el)) if el[idx].isupper()]        
        #print("Getting information: http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/enum/" + el[:res[1]] + "_" + el +".html")
        page = requests.get("http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/enum/" + el[:res[1]] + "_" + el +".html")
        soup = BeautifulSoup(page.text, 'html.parser')
        page.close()
        try:
            my_div = soup.find_all("div", {"class": "container"})
            #print("Caching",el)
            enums[el] = my_div[0].prettify()
            if my_div:                     
                my_row = my_div[0].find_all("div", {"class": "row"})
                if my_row:               
                    return "Source EMSA-CISE: : " + my_row[0].get_text().strip()
        except:
            #print("Error getting info")
            enums[el] = "Error"
            return "Source EMSA-CISE: : not found"
    elif el_type == "enumvalue":
        my_type = el.split()[0]
        my_value = el.split()[1]
        try:
            if enums.get(my_type):
                #print("cached")
                soup = BeautifulSoup(enums.get(my_type), 'html.parser')
                my_div = soup.find_all("tbody")[0]
            else:    
                res = [idx for idx in range(len(my_type)) if my_type[idx].isupper()]
                #print("Getting information: http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/enum/" + my_type[:res[1]] + "_" + my_type +".html")
                page = requests.get("http://emsa.europa.eu/cise-documentation/cise-data-model-1.5.3/model/enum/" + my_type[:res[1]] + "_" + my_type +".html")
                soup = BeautifulSoup(page.text, 'html.parser')
                my_div = soup.find_all("tbody")[0]
                page.close()
            anchor = 'name="'+ my_value +'"'
            if my_div:                     
                my_rows = my_div.find_all("tr")
                for row in my_rows:                
                    if anchor in row.find_all("td")[0].prettify(): 
                        #print(row.find_all("td")[2].get_text()  )              
                        return "Source EMSA-CISE: : " + row.find_all("td")[2].get_text().strip()  
        except:
            #print("Error getting info")
            return "Source EMSA-CISE: : not found"            
    else:
        return "Source EMSA-CISE: : not found"
  

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
                  
    def convert_data_prop(node, my_class, my_class_name):
        node_name = node.attrib["name"]
        if (node_name+my_class_name) in elements:
            print(node_name + "processed!")
            return
        elements.append(node_name+my_class_name)
        etype = resolve_type_instr(node.attrib["type"])
        print(node_name + " is an data property of " + my_class_name)
        node_name = node_name[0].lower() + node_name[1:]
        g.add(( NS[node_name], RDF.type, OWL.DatatypeProperty ))
        comment = get_description(my_class_name+" "+node_name, "prop")
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

                
        


    def convert_object_prop(node, my_class, my_class_name, ename, nary=False):
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
        if nary:
            g.add(( NS[property_prefix+node_name], RDFS.comment, Literal("Association relation")))
        else:
            comment = get_description(my_class_name+" "+ etype, "objectprop")
            if comment:
                g.add(( NS[property_prefix+node_name], RDFS.comment, Literal(comment)))
        elements.append(node_name+my_class_name)
        if "minOccurs" in node.attrib:
            if node.attrib["minOccurs"] != "0":                
                infixowl.Restriction(NS[node_name], graph=g, minCardinality=Literal(int(node.attrib["minOccurs"])))
        if "maxOccurs" in node.attrib:
            if node.attrib["maxOccurs"] != "unbounded":
                infixowl.Restriction(NS[node_name], graph=g, maxCardinality=Literal(int(node.attrib["maxOccurs"])))


    def convert_nary_relation(node, my_class, my_class_name, ename):
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
        comment = get_description(my_class_name+" "+ ename, "objectprop")
        if comment:            
            g.add(( NS[my_class_name+ename], RDFS.comment, Literal(comment) ))  
            
        #comment = get_pdf_description(my_class_name+node[0].attrib["name"], "Association Class")
        #if comment:
        #    g.add(( NS[property_prefix+ename], RDFS.comment, Literal(comment) ))  
        #    g.add(( NS[my_class_name+ename], RDFS.comment, Literal(comment) )) 
                                
        #Supposed that the first relation is for connecting the other class                     
        for i in range(len(node)):           
            child = node[i]
            if "name" in child.attrib:
                child_name = child.attrib["name"]
            
                #frist child
                if i == 0:
                    if (child.tag == "{http://www.w3.org/2001/XMLSchema}element") and ("type" in child.attrib):
                        child.attrib["name"] = "Involved" + child.attrib["name"]
                        convert_object_prop(child, my_class+ename, my_class_name+ename, child_name, True)
                        continue
                #g.add((NS[property_prefix+child_name], RDF.type, OWL.ObjectProperty))
                #g.add(( NS[property_prefix+child_name], RDFS.comment, Literal("Nary relation") ))  
                #g.add((NS[property_prefix+child_name], RDFS.domain, URIRef(NS[ename]))) 
                #print("Processing ", child_name, child.attrib, child.tag) 
                if (child.tag == "{http://www.w3.org/2001/XMLSchema}element") and ("type" in child.attrib):

                    etype = resolve_type_instr(child.attrib["type"])

                    if XSD in etype:
                        convert_data_prop(child, my_class + ename, my_class_name + child_name)
                    else:
                        convert_object_prop(child, my_class+ename, my_class_name+ename, child_name)

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
                                            convert_nary_relation(extension[0], my_class+ename, my_class_name+ename, child_name)  
                                        else:
                                            #print(my_class+ename)
                                            #Just for CISE files
                                            #convert_object_prop(extension[0][0], my_class+ename, node[0].attrib["name"], child_name)

                                            convert_object_prop(extension[0][0], my_class+ename, my_class_name+ename, child_name)
                 
    def convert_enum(node,  sourcename):
        node_name = node.attrib["name"]
        print(node_name + " is an enumeration")        
        g.add(( NS[node_name], RDF.type, RDFS.Datatype))
        if len(node)>0:
            if(node[0][0].text):
                g.add(( NS[node_name], RDFS.comment, Literal("Source: " + sourcename + " - " + node[0][0].text))) 
        #else:
            #comment = get_description(node_name,"enum")
            #if comment:
            #    g.add(( NS[node_name], RDFS.comment, Literal(comment)))  
            #comment = get_pdf_description(node_name, "Enumeration")
            #if comment:
            #    g.add(( NS[node_name], RDFS.comment, Literal(comment)))   
        g.add(( NS[node_name], RDF.type, OWL.Class))
        g.add(( NS[node_name], RDFS.subClassOf, URIRef("http://melodi.irit.fr/ontologies/ecise#EnumerationType")))
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
                                    convert_nary_relation(extension[0], NS[my_class_name], my_class_name, ename)                                    
                                else:
                                    convert_object_prop(extension[0][0], NS[my_class_name], my_class_name, ename)                          
                                                                
                #convert property
                elif "type" in node.attrib:
                    etype = resolve_type_instr(node.attrib["type"])
                    #convert data property
                    if XSD in etype:
                        convert_data_prop(node, NS[my_class_name], my_class_name)     
                    #convert object property
                    else:
                        convert_object_prop(node, NS[my_class_name], my_class_name, ename)
                        
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
            
    with open(filename, "r", encoding="utf8") as f: root = etree.parse(f).getroot()
    
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
    sourcename = sys.argv[1]
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
        if os.path.isfile(sys.argv[2]):
            print("Parsing file:", sys.argv[2])
            my_graph = parse_dom(sys.argv[2], sys.argv[1], my_text)
            print("=========== SERIALIZING  ===============")
            print("Graph size:",len(my_graph))
            out_put = os.path.join(os.path.dirname(sys.argv[2]),'ontology-cise.ttl')
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
        else:
            for path,dirs,files in os.walk(sys.argv[2]):
                for f in fnmatch.filter(files,'*.xsd'):
                    fullname = os.path.abspath(os.path.join(path,f))
                    print("Parsing file:", fullname)
                    graph = parse_dom(fullname, sys.argv[1], my_text)
                    my_graph = my_graph + graph
            print("=========== SERIALIZING  ===============")
            print("Graph size:",len(my_graph))
            out_put = os.path.join(sys.argv[2],'ontology-cise.ttl')
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
    else:
        print("============= USAGE ================")
        print("python3 xsd2owl [source name] [Optional PDF file] [Folder containing XSD files]")
    
