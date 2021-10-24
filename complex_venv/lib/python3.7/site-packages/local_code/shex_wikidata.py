
from shexer.shaper import Shaper

namespaces_dict = {
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.wikidata.org/prop/": "p",
    "http://www.wikidata.org/prop/direct/": "wdt",
    "http://www.wikidata.org/entity/": "wd",
    "http://www.w3.org/2001/XMLSchema#": "xsd",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://wikiba.se/ontology#": "wikibase",
    "http://schema.org/": "schema",
    "http://www.w3.org/2004/02/skos/core#": "skos"
}


"""
# shape_map_raw --> sheXer focus on some target structures to associate shapes with. 
                    You can use these shape maps: single-column SPARQL queries, node selectors, focus nodes.
                    You can use several selectors writting them in differente lines.
                    At the moment, each selector should be in a single line.
                    
                    Instead of shape maps, you can specify class URIs  with a list in the param  target_classes.
                    With that, all the instances of a given class will be used to build its shape.
                    
                    
# namespaces to ignore --> I'm telling shexer to ignore properties which are direct child of the namespaces in the
                    specified list.
# url_endpoint -->  Configured to work against Wikidata endpoint. It can work with local files as well and different
                    RDF syntax (shexer is a general RDF tool, not a Wikidata-specific one).
# instantiation_property ---> The property to instantiate classes is used in special ways at several points.
                    When it is not specified, rdf:type is used by default.
# namespaces_dict   ---> they will be used both to interpret prefixes in the shape maps and target RDF graph and
                    in the shex output.
# disable_comments   ---> Set to True to avoid getting the ratio of each triple constraint in the output.

# shape_qualifiers_mode AND namespaces_for_qualifier_props  ---> if shape_qualifiers_mode is set to True, then 
                    shexer will generate shapes for qualifiers. Shexer will consider qualifiers (according 
                    to Wikidata model) those nodes pointed by a property in any of the namespaces specified 
                    in 'namespaces_for_qualifier_props'
                    
#  depth_for_building_subgraph  ---> When using shexer against an endpoint, the library retrieves content starting
                   in the target nodes (specified via shape map, list of target classes, etc). All the triples in which
                   a target node is subject will be tracked. Then, it will repeat recursively this process with the
                   objects of those triples for a number of iterations specified in 'depth_for_building_subgraph'.
                   Depending on the targeted graph, setting this param to a high number could cause a huge performance 
                   cost. To get a shape for qualifiers, of the target nodes, the depth should be set to 2, at least.                
 
rest of params ---> shexer has multiple configuration params, but maybe just let those booleans as they are there 
                    for a first usage.                     

"""

shape_map_raw = "SPARQL'SELECT DISTINCT ?virus WHERE {   VALUES ?virus {  wd:Q82069695  }  }'@<Virus>  " # wd:Q8351095  wd:Q16983356 wd:Q4902157  wd:Q278567 wd:Q16983360 wd:Q16991954

shaper = Shaper(shape_map_raw=shape_map_raw,
                url_endpoint="https://query.wikidata.org/sparql",
                all_instances_are_compliant_mode=True,
                infer_numeric_types_for_untyped_literals=True,
                discard_useless_constraints_with_positive_closure=True,
                keep_less_specific=True,
                instantiation_property="http://www.wikidata.org/prop/direct/P31",
                namespaces_dict=namespaces_dict,
                depth_for_building_subgraph=2,
                namespaces_for_qualifier_props=["http://www.wikidata.org/prop/"],
                shape_qualifiers_mode=True,
                # disable_comments=True,
                all_classes_mode=False)




"""

string_output --> if set to true, result will be printed in the console. Alternatively you can specify an output
               file with a param output_file.
aceptance_threshold --> (I'm aware of the typo) it sets a threshold to ignore topological features associated to a
                  shape that happen in less than aceptance_threshold*100 percent of the entities used to build a shape.
                  

"""
result = shaper.shex_graph(string_output=True, acceptance_threshold=0)


print(result)
print("Done!")