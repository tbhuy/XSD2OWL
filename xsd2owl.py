import os, sys
from lxml import etree
import fnmatch

from rdflib import ConjunctiveGraph, Namespace, exceptions
from rdflib import URIRef, RDFS, RDF, OWL, BNode, Literal

def get_tag_no_ns(tname):
    if "}" in tname: 
        return tname[tname.index("}")+1:]
    else:
        return tname
        
class UnknownPrefixException(Exception):
    pass
    
def parse_dom(filename):
    """
    parse xml document from given filename and returns rdflib.ConjunctiveGraph instance containing OWL ontology statements
    """
    def reg_name(node):
        """
        recursively traverse document tree for named tags and store in a global map for later referencing
        """
        if "name" in node.attrib:
            tagmap[node.attrib["name"]] = node
            print("reg_name", node.attrib)
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
        
    def process_choice(ename, childs):
        anon_cls = ename+"_anon_class"
        anon_list = anon_cls+"_list"
        g.add(( NS[ename], OWL.subClassOf, BNode(anon_cls)))
        g.add(( BNode(anon_cls), RDF.type, OWL.Class))
        g.add(( BNode(anon_cls), OWL.unionOf, BNode(anon_list) ))
        
        #generate anonymous restricted classes (ARC)
        ch2arc = {} #mapping from child property name to ARC
        for ch in childs:
            anon_list_r = "_%s_r" % (ch["name"])
            item = NS[anon_list_r]
            is_first = True
            g.add(( item, RDF.type, OWL.Class ))
            
            prop_node = NS[property_prefix+ch["name"]]
            
            g.add(( item, OWL.intersectionOf, BNode(anon_list_r) ))
            if "minCardinality" in ch:
                restriction_node = BNode("%s_on_%s" % (anon_list_r, "minCardinality"))

                g.add(( restriction_node, RDF.type, OWL.Restriction ))
                g.add(( restriction_node, OWL.onProperty, prop_node ))
                g.add(( restriction_node, OWL.minCardinality, Literal(int(ch["minCardinality"])) ))
                
                g.add(( BNode(anon_list_r),  RDF.first, restriction_node))
                is_first = False
                
            if "maxCardinality" in ch:
                if not is_first:
                    #close previous list
                    next_node = "%s_next_%s" % (anon_list_r, "maxCardinality")
                    g.add(( BNode(anon_list_r),  RDF.rest, BNode(next_node) ))
                    anon_list_r = next_node
                    is_first = False
                    
                restriction_node = BNode("%s_on_%s" % (anon_list_r, "maxCardinality"))

                g.add(( restriction_node, RDF.type, OWL.Restriction ))
                g.add(( restriction_node, OWL.onProperty, prop_node ))
                g.add(( restriction_node, OWL.maxCardinality, Literal(int(ch["maxCardinality"])) ))
                
                g.add(( BNode(anon_list_r),  RDF.first, restriction_node))
                
            if "range" in ch:
                if not is_first:
                    #close previous list
                    next_node = "%s_next_%s" % (anon_list_r, "range")
                    g.add(( BNode(anon_list_r),  RDF.rest, BNode(next_node) ))
                    anon_list_r = next_node
                    
                restriction_node = BNode("%s_on_%s" % (anon_list_r, "range"))

                g.add(( restriction_node, RDF.type, OWL.Restriction ))
                g.add(( restriction_node, OWL.onProperty, prop_node ))
                if ":" in ch["range"]:
                    prop_obj = URIRef(ch["range"])
                else:
                    prop_obj = NS[ch["range"]]
                g.add(( restriction_node, OWL.allValuesFrom, prop_obj ))
                g.add(( BNode(anon_list_r),  RDF.first, restriction_node))
                
            g.add(( BNode(anon_list_r),  RDF.rest, RDF.nil))
            ch2arc[ch["name"]] = item
        
        #generate set differenced classes of ARCs (SDARC)
        sdarcs = []
        for ch in childs:          
            complement_classes = [c["name"] for c in childs if c["name"] != ch["name"]]
            sdarc = "_%s_without_%s" % (ch["name"], "".join(complement_classes))
            
            g.add(( NS[sdarc], RDF.type, OWL.Class ))
            
            intersection_node = "%s_setdiff_" % (ch["name"])
            g.add(( NS[sdarc], OWL.intersectionOf, BNode(intersection_node) ))
            g.add(( BNode(intersection_node), RDF.first, NS["_%s_r" % (ch["name"])] ))
            
            next_intersection = "%s_setdiff_next" % (ch["name"])
            g.add(( BNode(intersection_node), RDF.rest, BNode(next_intersection) ))
            intersection_node = next_intersection
            
            next_intersection =  "%s_setdiff_next_item" % (ch["name"])
            g.add(( BNode(intersection_node), RDF.first, BNode(next_intersection) ))
            
            g.add(( BNode(intersection_node), RDF.rest, RDF.nil ))
            
            union_of_complements = "%s_uoc" % (sdarc)
            comp_list = "%s_complist" % (sdarc)
            g.add(( BNode(next_intersection), OWL.complementOf, BNode(union_of_complements) ))
            g.add(( BNode(union_of_complements), OWL.unionOf,  BNode(comp_list) ))
            
            for cci, cc in enumerate(complement_classes):
                g.add(( BNode(comp_list),  RDF.first, NS["_%s_r" % (cc)]))
                
                if cci == len(complement_classes)-1:
                    g.add(( BNode(comp_list),  RDF.rest, RDF.nil))
                else:
                    next_node = "%s_complist_%s" % (sdarc, cc)
                    g.add(( BNode(comp_list),  RDF.rest, BNode(next_node) ))
                    comp_list = next_node
                    
            
            sdarcs.append(sdarc)
                
        #generate unions of SDARCs
        for si, sdarc in enumerate(sdarcs):
            g.add(( BNode(anon_list),  RDF.first, NS[sdarc] ))
            if si == len(sdarcs)-1:
                g.add(( BNode(anon_list),  RDF.rest, RDF.nil))
            else:
                next_node = "%s_complist_%s" % (anon_cls, sdarc)
                g.add(( BNode(anon_list),  RDF.rest, BNode(next_node) ))
                anon_list = next_node
        
    def process_seq_all(ename, childs):
        anon_cls = ename+"_anon_class"
        anon_list = anon_cls+"_list"
        g.add(( NS[ename], OWL.subClassOf, BNode(anon_cls)))
        g.add(( BNode(anon_cls), RDF.type, OWL.Class))
        g.add(( BNode(anon_cls), OWL.intersectionOf, BNode(anon_list) ))
        
        restrictions = []
        for ci,ch in enumerate(childs):
            if "minCardinality" in ch: 
                rst_item = {}
                rst_item["property"] = NS[property_prefix+ch["name"]]
                rst_item["predicate"] = OWL.minCardinality
                rst_item["object"] = Literal(int(ch["minCardinality"]))
                restrictions.append(rst_item)
            if "maxCardinality" in ch:
                rst_item = {}
                rst_item["property"] = NS[property_prefix+ch["name"]]
                rst_item["predicate"] = OWL.maxCardinality
                rst_item["object"] = Literal(int(ch["maxCardinality"]))
                restrictions.append(rst_item)
            if "range" in ch:
                rst_item = {}
                rst_item["property"] = NS[property_prefix+ch["name"]]
                rst_item["predicate"] = OWL.allValuesFrom
                if ":" in ch["range"]:
                    rst_item["object"] = URIRef(ch["range"])
                else:
                    rst_item["object"] = NS[ch["range"]]
                restrictions.append(rst_item)
            
        for ci, ch in enumerate(restrictions):
            #construct list of intersectionOf items
            restriction_node = BNode(ch["property"]+"_anon_"+str(ci))

            g.add(( restriction_node, RDF.type, OWL.Restriction ))
            g.add(( restriction_node, OWL.onProperty, ch["property"] ))
            g.add(( restriction_node, ch["predicate"], ch["object"] ))
            
            g.add(( BNode(anon_list),  RDF.first, restriction_node))
            if ci == len(childs)-1:
                g.add(( BNode(anon_list),  RDF.rest, RDF.nil))
            else:
                next_node = anon_cls+"_%d" % ci
                g.add(( BNode(anon_list),  RDF.rest, BNode(next_node) ))
                anon_list = next_node
            
    def convert_namedtype(node):
        """
        handle types (simpleType and complexType) elements
        """
        is_dt = False
        
        tname = node.attrib["name"]
        print("Convert named type", tname)
        if tname not in types:
            if node.tag == xs_st:
                print(tname, "is DatatypeProperty")
                g.add(( NS[tname], RDF.type, OWL.DatatypeProperty ))
                is_dt = True
                #check for restriction
            elif node.tag == xs_ct:
                print(tname, "is Class")
                g.add(( NS[tname], RDF.type, OWL.Class ))
                for cc in node:
                    tag = get_tag_no_ns(cc.tag)
                    if tag == "attribute":
                        aname = cc.attrib["name"]
                        if "type" in cc.attrib:
                            atype = resolve_type_instr(cc.attrib["type"])
                            g.add(( NS[property_prefix+aname], RDFS.range, URIRef(atype) ))
                        else:
                            pass
                        print(aname, "is DatatypeProperty from attr")
                        g.add(( NS[property_prefix+aname], RDF.type, OWL.DatatypeProperty ))
                        g.add(( NS[property_prefix+aname], RDFS.domain, NS[tname] ))
                    elif tag in ["sequence", "choice", "all"]:
                        childs = []
                        
                        for ce in cc:
                            #child element of named ct
                            if ce.tag == xs_el:
                                has_child = True
                                cename, info = convert_element(ce)
                                childs.append(info)
                                if not info["isClass"]:
                                    g.add(( NS[property_prefix + cename], RDFS.domain, NS[tname] ))
                        
                        if len(childs)>0:
                            if tag in ["sequence", "all"]:
                                process_seq_all(tname, childs)
                            elif tag == "choice":
                                process_choice(tname, childs)
                                
            types.append(tname)
        return tname, is_dt
        
    def convert_element(node, myclass, is_global=False):
        """
        handle element conversion
        """
        #print(node)
        info = {}
        has_cac = False #has child, attribute, or content
        if "name" in node.attrib:
            ename = node.attrib["name"]
            print("convert_element", ename)
            print("node attribute", node.attrib)
            info["name"] = ename
            if "minOccurs" in node.attrib:
                info["minCardinality"] = node.attrib["minOccurs"]
            if "maxOccurs" in node.attrib:
                info["maxCardinality"] = node.attrib["maxOccurs"]

            if "type" in node.attrib:
                etype = resolve_type_instr(node.attrib["type"])
                
                if XSD in etype:
                    print(ename, "is DatatypeProperty")
                    g.add(( NS[property_prefix+ename], RDF.type, OWL.DatatypeProperty ))
                    g.add(( NS[property_prefix+ename], RDFS.range, URIRef(etype) ))
                    g.add(( NS[property_prefix+ename], RDFS.domain, URIRef(myclass) ))
                    info["range"] = etype
                else: #unknown type name
                    print("custom type:", etype)
                    g.add(( NS[property_prefix+ename], RDF.type, OWL.ObjectProperty ))
                    g.add(( NS[property_prefix+ename], RDFS.domain, URIRef(myclass) ))
                    if "http" in etype:
                        g.add(( NS[property_prefix+ename], RDFS.range, URIRef(etype) ))
                    else:
                        g.add(( NS[property_prefix+ename], RDFS.range, URIRef(NS[etype]) ))
                    #g.add(( URIRef(NS[etype]) , RDF.type, OWL.Class))
                    info["range"] = etype
                    
            else:
                for child in node:
                    #anonymous type
                    if child.tag == xs_st:
                        #element declared as simpleType converted into owl:DatatypeProperty
                        print(ename, " is DatatypeProperty")
                        g.add(( NS[property_prefix+ename], RDF.type, OWL.DatatypeProperty ))
                    elif child.tag == xs_ct:
                        #element declared as complexType converted into owl:Class
                        for cc in child:
                            tag = get_tag_no_ns(cc.tag)
                            if tag == "attribute":
                                has_cac = True
                                aname = cc.attrib["name"]
                                if "type" in cc.attrib:
                                    atype = resolve_type_instr(cc.attrib["type"])
                                    g.add(( NS[property_prefix+aname], RDFS.range, URIRef(atype) ))
                                else:
                                    pass
                                print(aname, "is DatatypeProperty from attr")
                                g.add(( NS[property_prefix+aname], RDF.type, OWL.DatatypeProperty ))
                                g.add(( NS[property_prefix+aname], RDFS.domain, NS[ename] ))
                                
                            elif "Content" in tag:
                                #TODO
                                #simpleContent with attribute extension converted to Class with generated content property
                                #complexContent is a class with generated properties
                                has_cac = True
                            elif tag in ["sequence", "choice", "all"]:
                                #subelement specifier converted using set operations on equivalent classes
                                childs = []
                                for ce in cc:
                                    #child element of anon ct
                                    if ce.tag == xs_el:
                                        has_cac = True
                                        cename, chinfo = convert_element(ce)
                                        childs.append(chinfo)
                                        if chinfo["isClass"]:
                                            #declare object property
                                            g.add(( NS[property_prefix+cename], RDF.type, OWL.ObjectProperty ))
                                        else:
                                            g.add(( NS[property_prefix+cename], RDFS.domain, NS[ename] ))
                                
                                if len(childs)>0:
                                    if tag in ["sequence", "all"]:
                                        process_seq_all(ename, childs)
                                    elif tag == "choice":
                                        process_choice(ename, childs)

                        if has_cac:
                            g.add(( NS[ename], RDF.type, OWL.Class ))
                            print(ename, "is Class")
        else:
            ename = "Noname"
        info["isClass"] = has_cac
        return ename, info
            
    with open(filename, "r") as f: root = etree.parse(f).getroot()
    #print(etree.tostring(root, pretty_print=True))
    tagmap = {}
    types = []
    reg_name(root)
    
    #predeclaration
    XSD = "http://www.w3.org/2001/XMLSchema"
    elements = []
    #elements.append(".//{%s}%s" % (XSD, "simpleType"))
    #elements.append(".//{%s}%s" % (XSD, "complexType"))
    elements.append(".//{%s}%s" % (XSD, "element"))
    elements.append(".//{%s}%s" % (XSD, "attribute"))
    xs_st = ".//{%s}%s" % (XSD, "simpleType")
    xs_ct = ".//{%s}%s" % (XSD, "complexType")
    xs_el = ".//{%s}%s" % (XSD, "element")
    xs_at = ".//{%s}%s" % (XSD, "attribute")
    #print("====>", xs_el)
    #graph
    g = ConjunctiveGraph()
   
    
    for k, v in root.nsmap.items():
        if k is not None:
            g.bind(k, v)
            print("Bind ", k, v)
        #if myclass.lower() in k:
        #    myclass = v + myclass    
    if "targetNamespace" in root.attrib:
        NS = Namespace(root.attrib["targetNamespace"])
    else:
        NS = Namespace("http://example.org/xsdowl#")
    
    g.bind(None, NS)
    g.bind("owl", OWL)
    g.bind("xsd", XSD+"#")
    
    property_prefix = "has_"
    #myclass = ":" + myclass
    
    #g.add((URIRef(myclass), RDF.type, OWL.Class))
    #do traversal directed translation
    #print(root.findall(xs_el))
    myclass = root.findall(xs_ct)
    if myclass:
        myclass = myclass[0].attrib["name"]
        g.add((NS[myclass], RDF.type, OWL.Class))
    else:
        myclass = "NotAClass"
    print(myclass)
    #myclass = myclass.lower()+":" + myclass
    
    print("myClass=", NS[myclass])
    for element in elements:
        print("PROCESSING ", element)
        for el in root.findall(element):
            #print("convert", el)
            convert_element(el, NS[myclass], True)
            #print("Graph size=",len(g))
    return g

if __name__ == "__main__":
    if len(sys.argv)>1:
        print("=========== PARSING FILES ===============")
        my_graph = ConjunctiveGraph()
        for path,dirs,files in os.walk(sys.argv[1]):
            for f in fnmatch.filter(files,'*.xsd'):
                fullname = os.path.abspath(os.path.join(path,f))
                print("Parsing file:", fullname)
                graph = parse_dom(fullname)
                my_graph = my_graph + graph
        print("=========== SERIALIZING  ===============")
        print("Graph size=",len(my_graph))
        out_put = os.path.join(sys.argv[1],'onto_py.ttl')
        print("Output= ",out_put)
        my_graph.serialize(out_put, format='turtle')
    else:
        print("============= USAGE ================")
        print("python3 xsd2owl [Folder containing XSD files]")
