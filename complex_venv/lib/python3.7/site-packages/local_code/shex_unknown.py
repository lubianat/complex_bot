from shexer.shaper import Shaper

target_classes = ["<https://schema.org/DataRecord>",
                  "<https://schema.org/DefinedTerm>",
                  "<https://schema.org/PropertyValue>",
                  "<https://schema.org/Protein>",
                  "<https://schema.org/SequenceAnnotation>",
                  "<https://schema.org/SequenceRange>",
                  "<https://schema.org/ScholarlyArticle>",
                  "<https://schema.org/Organization>",
                  "<https://schema.org/Dataset>",
                  "<https://schema.org/Person>",
                  "<https://schema.org/DefinedTermSet>",
                  "<https://schema.org/DataCatalog>",
                  "<https://schema.org/CreativeWork>",
                  "<https://schema.org/Taxon>",
                  "<https://schema.org/AnatomicalStructure>",
                  "<https://schema.org/ChemicalSubstance>",
                  "<https://schema.org/MedicalCondition>",
                  "<https://schema.org/Gene>",
                  "<https://schema.org/Drug>",
                  "<https://schema.org/MedicalSignOrSymptom>"]

namespaces = {"http://schema.org/": "schema",
              "http://www.wikidata.org/prop/direct/": "wdt",
              "http://www.wikidata.org/prop/": "p",
              "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
              "https://schema.org/": "schema",
              "http://www.w3.org/2001/XMLSchema#": "xsd"}

shaper = Shaper(url_endpoint="http://156.35.94.155:8889/bigdata/sparql",
                depth_for_building_subgraph=1,
                track_classes_for_entities_at_last_depth_level=False,
                namespaces_dict=namespaces,
                target_classes=target_classes,
                disable_comments=False,
                limit_remote_instances=30,
                disable_exact_cardinality=True)
result = shaper.shex_graph(string_output=True)
print(result)
print("Done!")
