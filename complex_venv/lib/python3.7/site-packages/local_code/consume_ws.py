import requests

################ url_web_service

url_web_service = "http://156.35.86.6:8080/shexer"
# url_web_service = "http://localhost/shexer"



################ namespace

# This ones are inclided by default:

# default_namespaces = {"http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
#                       "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
#                       "http://www.w3.org/2001/XMLSchema#": "xml",
#                       "http://www.w3.org/XML/1998/namespace/": "xml",
#                       "http://www.w3.org/2002/07/owl#": "owl",
#
#                       }

new_namespaces = {
    "http://wikiba.se/ontology#": "wikibase",
    "http://www.bigdata.com/rdf#": "bd",
    "http://www.wikidata.org/entity/": "wd",
    "http://www.wikidata.org/prop/direct/": "wdt",
    "http://www.wikidata.org/prop/direct-normalized/": "wdtn",
    "http://www.wikidata.org/entity/statement/": "wds",
    "http://www.wikidata.org/prop/": "p",
    "http://www.wikidata.org/reference/": "wdref",
    "http://www.wikidata.org/value/": "wdv",
    "http://www.wikidata.org/prop/statement/": "ps",
    "http://www.wikidata.org/prop/statement/value/": "psv",
    "http://www.wikidata.org/prop/statement/value-normalized/": "psn",
    "http://www.wikidata.org/prop/qualifier/": "pq",
    "http://www.wikidata.org/prop/qualifier/value/": "pqv",
    "http://www.wikidata.org/prop/qualifier/value-normalized/": "pqn",
    "http://www.wikidata.org/prop/reference/": "pr",
    "http://www.wikidata.org/prop/reference/value/": "prv",
    "http://www.wikidata.org/prop/reference/value-normalized/": "prn",
    "http://www.wikidata.org/prop/novalue/": "wdno"
}



################ PARAM NAMES AND DOC

TARGET_CLASSES_PARAM = "target_classes"
"""
List of strings: List of target classes to associate a shape with
"""

TARGET_GRAPH_PARAM = "raw_graph"
"""
String: RDF content to be analyzed
"""

INPUT_FORMAT_PARAM = "input_format"
"""
String: RDF syntax used. Ntriples is used by default Accepted values -->

"nt" (n-triples)
"turtle" (turtle)
"xml" (RDF/XML)
"n3" (n3)
"json-ld" (JSON LD)
"tsv_spo" (lines with subject predicate and object separated by tab '\\t' chars 
"""


INSTANTIATION_PROPERTY_PARAM = "instantiation_prop"
"""
String: property used to links an instance with its class. rdf:type by default.
"""


NAMESPACES_TO_IGNORE_PARAM = "ignore"
"""
List of Strings: List of namespaces whose properties should be ignored during the shexing process.
"""

INFER_NUMERIC_TYPES_PARAM = "infer_untyped_nums"
"""
Bool: default, True. If True, it tries to infer the numeric type (xsd:int, xsd:float..) of 
untyped numeric literals 
"""

DISCARD_USELESS_CONSTRAINTS_PARAM = "discard_useless_constraints"
"""
Bool: default, True. default, True. If True, it keeps just the most possible specific constraint w.r.t. cardinality 
"""

ALL_INSTANCES_COMPLIANT_PARAM = "all_compliant"
"""
Bool: default, True. default, True. If False, the shapes produced may not be compliant with all the entities considered
to build them. This is because it won't use Kleene closeres for any constraint. 
"""

KEEP_LESS_SPECIFIC_PARAM = "keep_less_specific"
"""
Bool: default, True. It prefers to use "+" closures rather than exact cardinalities in the triple constraints
"""

ACEPTANCE_THRESHOLD_PARAM = "threshold"
"""
Float: number in [0,1] that indicates the minimum proportion of entities that should have a given feature for this
to be accepted as a triple constraint in the produced shape.
"""

ALL_CLASSES_MODE_PARAM = "all_classes"
"""
Bool: default, False. If True, it generates a shape for every elements with at least an instance 
in the considered graph.
"""
SHAPE_MAP_PARAM = "shape_map"
"""
String: shape map to associate nodes with shapes. It uses the same syntax of validation shape maps. 
"""

REMOTE_GRAPH_PARAM = "graph_url"
"""
String: URL to retrieve an online raw graph.
"""

ENDPOINT_GRAPH_PARAM = "endpoint"
"""
String: URL of an SPARQL endpoint.
"""

NAMESPACES_PARAM = "prefixes"
"""
Dict. key are namespaces and values are prefixes. The pairs key value provided here will be used 
to parse the RDF content and t write the resulting shapes.
"""

QUERY_DEPTH_PARAM = "query_depth"
"""
Integer: default, 1. It indicates the depth to generate queries when targeting a SPARQL endpoint.
Currently it can be 1 or 2.
"""

DISABLE_COMMENTS_PARAM = "disable_comments"
"""
Bool: default, False. When set to True, the shapes do not include comment 
with ratio of entities compliant with a triple constraint
"""

QUALIFIER_NAMESPACES_PARAM = "namespaces_for_qualifiers"
"""
List. Default, None. When a list with elements is provided, the properties in the namespaces specified are considered
to be pointers to qualifier nodes.
"""

SHAPE_QUALIFIERS_MODE_PARAM = "shape_qualifiers_mode"
"""
Bool: default, False. When set to true, a shape is generated for those nodes detected as qualifiers according to
Wikidata data model and the properties pointing to them specified in QUALIFIER_NAMESPACES_PARAM
"""



############ Param definition for a use case

shape_map = "SPARQL'SELECT DISTINCT ?virus WHERE {   VALUES ?virus {  wd:Q82069695  }  }'@<Virus>  " # wd:Q16983360 wd:Q16991954 wd:Q8351095  wd:Q16983356 wd:Q4902157  wd:Q278567


params = {NAMESPACES_PARAM: new_namespaces,
          SHAPE_MAP_PARAM: shape_map,
          ENDPOINT_GRAPH_PARAM: "https://query.wikidata.org/sparql",
          ALL_CLASSES_MODE_PARAM: False,
          QUERY_DEPTH_PARAM: 2,
          ACEPTANCE_THRESHOLD_PARAM: 0,
          INSTANTIATION_PROPERTY_PARAM: "http://www.wikidata.org/prop/direct/P31",
          DISABLE_COMMENTS_PARAM: True,
          SHAPE_QUALIFIERS_MODE_PARAM: True,
          QUALIFIER_NAMESPACES_PARAM: ["http://www.wikidata.org/prop/"]

          }

############ Calling web service

r = requests.post(url=url_web_service, json=params)


data = r.json()
print(data["result"])
print("Done!")