from shexer.shaper import Shaper
from shexer.consts import NT
import time

list_of_names = [
                 # "infobox_properties_mapped_en",
                 "infobox_properties_en",
                 "instance_types_en",
                 "mappingbased_objects_en",
                 "persondata_en",
                 "specific_mappingbased_properties_en",
                 # "topical_concepts_en"
]

template_file = "C:\\Users\\Dani\\Documents\\EII\\doctorado\\datasets\\dbpedia_endpoint\\{}.ttl"

namespaces_dict = {
    "http://id.loc.gov/ontologies/bibframe.rdf/" : "bf",
    "http://weso.es/" : "",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.wikidata.org/prop/direct/": "wdt",
    "http://www.wikidata.org/prop/": "wd",
    "http://dbpedia.org/ontology/": "dbo",
    "http://dbpedia.org/resource/": "dbr",
    "http://www.w3.org/2001/XMLSchema#" : "xsd",
    "http://dbpedia.org/class/yago/" : "yago",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#" : "rdf",
    "http://www.w3.org/2003/01/geo/wgs84_pos#" : "geo",
    "http://xmlns.com/foaf/0.1/" : "foaf",
    "http://purl.org/dc/elements/1.1/" : "dc",
    "http://dbpedia.org/resource/Category:" : "dbc",
    "http://dbpedia.org/property/" : "dbp",
    "http://www.w3.org/XML/1998/namespace" : "xml"
}

print("Starting...")
stime = time.time()

shaper = Shaper(target_classes=["http://dbpedia.org/ontology/Award"],
                graph_list_of_files_input=[template_file.format(a_file) for a_file in list_of_names],
                input_format=NT,
                namespaces_to_ignore=namespaces_dict,
                instances_file_input=template_file.format("instance_types_en"),
                all_instances_are_compliant_mode=True)


result = shaper.shex_graph(string_output=True, acceptance_threshold=0.4)


etime = time.time()
print("Time ", etime - stime)
print(result)
print("Done!")
