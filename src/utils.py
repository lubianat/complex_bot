# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src

import math
import re
from collections import defaultdict
from ftplib import FTP
from functools import lru_cache, reduce
from time import gmtime, strftime
import pandas as pd
from wikidata2df import wikidata2df
from wikidataintegrator import wdi_core
from wikidataintegrator.wdi_core import WDItemEngine
import json

with open("mappings.json", "r") as fp:
    MAPPINGS = json.load(fp)


def get_list_of_complexes(
    datasets, species_id, test_on_wikidata=True, max_complexes=999999
):
    """
    Clean and process table of complexes

    Parses table of complexes into Complex classes

    Args:
        datasets (DataFrame): one of the species datasets
        species_id (str): The NCBI species ID
        test_on_wikidata (bool): A boolean indicating whether to return only complexes that are or aren't on Wikidata. Defaults to True.
        max_complexes (str): The maximum number of complexes to be modified on Wikidata

    Returns:
        list_of_complexes (list): Objects of the Complex class

    """
    raw_table = pd.read_table(datasets[species_id], na_values=["-"])

    if test_on_wikidata:
        raw_table = remove_rows_on_wikidata(raw_table)

    columns_to_keep = get_columns_to_keep()
    raw_table = raw_table[columns_to_keep]

    list_of_complexes = []
    print("====== Parsing list to extract into class Complex ======")
    # Counter for bot test
    counter = 0
    for complex_id in raw_table["#Complex ac"]:
        counter = counter + 1
        list_of_complexes.append(Complex(raw_table, complex_id))
        if counter == max_complexes:
            break
    return list_of_complexes


def update_complex(login_instance, protein_complex, references):
    """

    Updates the information for an existing complex on Wikidata.
    Args:
        login_instance: A Wikidata Integrator login instance
        protein_complex: An object of the class Complex containing the information for a protein complex
        references: The set of references for WDI
    """

    instance_of = wdi_core.WDItemID(
        value="Q22325163", prop_nr="P279", references=references
    )

    subclass_of = wdi_core.WDItemID(
        value="Q107509287", prop_nr="P31", references=references
    )

    found_in_taxon = wdi_core.WDItemID(
        value=protein_complex.taxon_qid, prop_nr="P703", references=references
    )

    complex_portal_id = wdi_core.WDString(
        value=protein_complex.complex_id, prop_nr="P7718", references=references
    )

    data = [instance_of, subclass_of, found_in_taxon, complex_portal_id]
    has_parts = []
    for component in protein_complex.list_of_components:
        quantity = component.quantity
        component_qid = component.qid
        print(f"Component QID: {component_qid}")

        def is_nan(string):
            return string != string

        if is_nan(component_qid):
            break

        if quantity != "0" and not math.isnan(int(quantity)):
            print(f"Quantity of this component: {str(quantity)}")
            # Quantity is valid. 0 represents unknown in Complex Portal.

            quantity_qualifier = wdi_core.WDQuantity(
                value=int(quantity), prop_nr="P1114", is_qualifier=True
            )
            statement = wdi_core.WDItemID(
                value=component_qid,
                prop_nr="P527",
                qualifiers=[quantity_qualifier],
                references=references,
            )
        else:
            statement = wdi_core.WDItemID(
                value=component_qid, prop_nr="P527", references=references
            )

        has_parts.append(statement)

    data.extend(has_parts)

    # Reference table via https://w.wiki/3dTC
    go_statements = []
    go_reference = pd.read_csv("./reference_go_terms.csv")
    for go_term in protein_complex.go_ids:
        # Considers  that each term has only one GO type
        try:
            row = go_reference[go_reference["id"] == go_term]
            obj = row["go_term_qid"].values[0]
            label = row["go_termLabel"].values[0]
            prop = row["go_props_qid"].values[0]

            # Heuristic: Cell components containing the word "complex" in the label
            # are actually superclasses.
            if "complex" in label and prop == "P681":
                prop = "P279"

            statement = wdi_core.WDItemID(
                value=obj, prop_nr=prop, references=references
            )
            go_statements.append(statement)
        except BaseException as e:
            print(e)
            print("Problem with " + go_term)
            with open("errors/log.csv", "a") as f:
                f.write(f"{go_term},'problem with GO term'\n")

    data.extend(go_statements)
    label = protein_complex.name
    aliases = protein_complex.aliases

    taxon_name = get_wikidata_label(protein_complex.taxon_qid)
    descriptions = {
        "en": "macromolecular complex found in " + taxon_name,
        "pt": "complexo macromolecular encontrado em " + taxon_name,
        "pt-br": "complexo macromolecular encontrado em " + taxon_name,
        "nl": "macromoleculair complex gevonden in " + taxon_name,
        "de": "makromolekularer Komplex auffindbar in " + taxon_name,
    }

    # For the list below, the bot will not remove values added on Wikidata
    properties_to_append_value = ["P703", "P680", "P681", "P682", "P527"]

    wd_item = wdi_core.WDItemEngine(
        data=data,
        append_value=properties_to_append_value,
        debug=True,
    )
    wd_item.set_label(label=label, lang="en")
    wd_item.set_aliases(aliases, lang="en")

    # As fast-run is set, I will not update descriptions.
    for lang, description in descriptions.items():
        wd_item.set_description(description, lang=lang)

    wd_item.write(login_instance)


class ComplexComponent:
    def __init__(self, external_id, quantity):
        self.external_id = external_id
        self.quantity = quantity
        self.get_qid_for_component()

    def get_qid_for_component(self):
        external_id = self.external_id
        print(external_id)
        if "CHEBI" in self.external_id:
            external_id = external_id.replace("CHEBI:", "")
            # ChEBI ID (P683)
            self.qid = get_wikidata_item_by_propertyvalue("P683", external_id)
        elif "CPX" in self.external_id:
            # Complex Portal ID (P7718)
            self.qid = get_wikidata_item_by_propertyvalue("P7718", self.external_id)
        elif "URS" in self.external_id:
            # RNACentral ID (P8697)
            self.qid = get_wikidata_item_by_propertyvalue("P8697", self.external_id)

        else:
            # UniProt protein ID (P352)
            self.qid = get_wikidata_item_by_propertyvalue("P352", self.external_id)


class Complex:
    def __init__(self, dataset, complex_id):
        self.complex_id = complex_id

        # Info is a 1 row data frame with the following columns:
        # #Complex ac
        # Recommended name
        # Aliases for complex
        # Taxonomy identifier
        # Identifiers (and stoichiometry) of molecules in complex
        # Confidence
        # Experimental evidence
        # Go Annotations
        # Cross references
        # Description
        # Complex properties
        # Complex assembly
        # Ligand
        # Disease
        # Agonist
        # Antagonist
        # Comment
        # Source
        # Expanded participant list

        self.info = dataset[dataset["#Complex ac"] == complex_id]
        self.list_of_components = []
        self.go_ids = []
        self.extract_fields()
        print(f"Parsing {self.name}")

    def extract_fields(self):
        self.get_name()
        self.get_aliases()
        self.get_components()
        self.get_go_ids()
        self.get_wikidata_ids()

    def get_name(self):
        self.name = self.info["Recommended name"].values[0]

    def get_aliases(self):
        aliases_string = self.info["Aliases for complex"].values[0]
        # "-" represents NA in this column
        # Sometimes we get true NAs there
        if aliases_string == "-" or not isinstance(aliases_string, str):
            self.aliases = []
        else:
            self.aliases = aliases_string.split("|")

    def get_components(self):
        molecules_column = "Identifiers (and stoichiometry) of molecules in complex"
        molecules_string = self.info[molecules_column].values[0]
        molecules = molecules_string.split("|")

        matches_quantities = [re.search(r"\((.*)\)", i) for i in molecules]
        quantities = [m.group(1) for m in matches_quantities]

        matches_uniprot_ids = [re.search(r"(.*)\(.*\)", i) for i in molecules]
        uniprot_ids = [m.group(1) for m in matches_uniprot_ids]

        component_and_quantities = dict(zip(uniprot_ids, quantities))
        for external_id in component_and_quantities:
            component = ComplexComponent(
                external_id, component_and_quantities[external_id]
            )
            self.list_of_components.append(component)

    def get_go_ids(self):
        go_column = "Go Annotations"
        try:
            go_string = self.info[go_column].values[0]
            go_list = re.findall(pattern="GO:[0-9]*", string=go_string)
            self.go_ids = go_list
        except Exception:
            print(f"No GOs for {self.complex_id}")

    def get_wikidata_ids(self):
        # NCBI taxonomy ID (P685)
        tax_id = self.info["Taxonomy identifier"].values[0]
        self.taxon_qid = get_wikidata_item_by_propertyvalue("P685", int(tax_id))


def get_wikidata_complexes():
    """Gets all Wikidata items with a Complex Portal ID property"""
    print("======  Getting complexes on Wikidata  ======")
    get_macromolecular = """
    SELECT ?item ?ComplexPortalID
    WHERE
    {
    ?item wdt:P7718 ?ComplexPortalID .
    }"""
    wikidata_complexes = WDItemEngine.execute_sparql_query(
        get_macromolecular, as_dataframe=True
    ).replace({"http://www.wikidata.org/entity/": ""}, regex=True)

    return wikidata_complexes


def get_wikidata_label(qid, langcode="en"):
    """Gets a Wikidata item for a determined property-value pair
    Args:
        qid (str): The qid to get the label
        langcode (str): The language code of the label
    """
    query_result = WDItemEngine.execute_sparql_query(
        f'SELECT ?label WHERE {{ wd:{qid} rdfs:label ?label. FILTER(LANG(?label)="{langcode}") }}'
    )
    try:
        match = query_result["results"]["bindings"][0]
    except IndexError:
        print(f"Couldn't find label for {qid}")
        raise ("label nof found for " + qid)
    label = match["label"]["value"]
    return label


@lru_cache(maxsize=None)
def get_wikidata_item_by_propertyvalue(property, value, mappings=MAPPINGS):
    """Gets a Wikidata item for a determined property-value pair
    Args:
        property (str): The property to search
        value (str): The value of said property
    """

    try:
        qid = mappings[property][value]
        return str(qid)
    except:
        pass

    query_result = WDItemEngine.execute_sparql_query(
        f'SELECT distinct ?item WHERE {{ ?item wdt:{property} "{value}" }}'
    )

    try:
        match = query_result["results"]["bindings"][0]
    except IndexError:
        print(f"Couldn't find item for {value}")

        if "URS" in value:
            with open("errors/rna_central_log.csv", "a") as f:
                f.write(f"{value},'not found'\n")

        with open("errors/log.csv", "a") as f:
            f.write(f"{value},'not found'\n")
        return pd.np.NaN

    qid = match["item"]["value"]
    qid = qid.split("/")[4]

    try:
        mappings[property][str(value)] = str(qid)
    except:
        mappings[property] = {}
        mappings[property][str(value)] = str(qid)

    with open("mappings.json", "w") as fp:
        json.dump(MAPPINGS, fp, sort_keys=True, indent=4)
    return qid


def get_complex_portal_species_ids():
    """Gets a dictionary of Complex portal datasets
    Returns a dictionary of species as keys and dataset url as values.
    """
    domain = "ftp.ebi.ac.uk"
    complex_data = "pub/databases/intact/complex/current/complextab/"
    print("======  Getting Complex Portal Species IDs  ======")
    ftp = FTP(domain)
    ftp.login()
    ftp.cwd(complex_data)
    files = ftp.nlst()
    species_list = []

    for species in files:
        if "tsv" in species:
            species_list.append(species.replace(".tsv", "").strip())

    query = (
        """
    SELECT ?itemLabel ?id WHERE {
        VALUES ?id { """
        + '"'
        + '" "'.join(species_list)
        + '"'
        + """ }
        ?item wdt:P685 ?id. 
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }

    }

    """
    )
    df = wikidata2df(query)
    return df


def get_complex_portal_dataset_urls():
    """Gets a dictionary of Complex portal datasets
    Returns a dictionary of species as keys and dataset url as values.
    """
    domain = "ftp.ebi.ac.uk"
    complex_data = "pub/databases/intact/complex/current/complextab/"
    print("======  Getting Complex Portal datasets via FTP  ======")
    ftp = FTP(domain)
    ftp.login()
    ftp.cwd(complex_data)
    files = ftp.nlst()
    string_replacements = (".tsv", ""), ("_", " ")
    cp_datasets = defaultdict()

    for species in files:
        if "README" not in species:
            current_key = reduce(
                lambda a, kv: a.replace(*kv), string_replacements, species
            )
            cp_datasets[current_key] = f"ftp://{domain}/{complex_data}{species}"

    return cp_datasets


def remove_rows_on_wikidata(complex_dataframe):
    """
    Return complex portal entities that don't have Wikidata links.
    """

    print("======  Checking which complexes are not on Wikidata  ======")

    wikidata_complexes = get_wikidata_complexes()
    merged_data = pd.merge(
        wikidata_complexes,
        complex_dataframe,
        how="outer",
        left_on=["ComplexPortalID"],
        right_on=["#Complex ac"],
        indicator=True,
    )
    missing_from_wikidata = merged_data[merged_data["_merge"] == "right_only"][
        complex_dataframe.columns
    ]
    keep = get_columns_to_keep()
    missing_from_wikidata = missing_from_wikidata[keep]
    return missing_from_wikidata


def split_complexes(species_dataframe):
    complex_dfs = [
        species_dataframe[
            species_dataframe["#Complex ac"] == unique_complex
        ].reset_index()
        for unique_complex in species_dataframe["#Complex ac"].unique()
    ]
    return complex_dfs


def prepare_refs(species_id):
    stated_in = wdi_core.WDItemID(value="Q47196990", prop_nr="P248", is_reference=True)
    wikidata_time = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
    retrieved = wdi_core.WDTime(wikidata_time, prop_nr="P813", is_reference=True)
    ftp_url = "https://ftp.ebi.ac.uk/pub/databases/intact/complex/current/complextab"
    ref_url = wdi_core.WDString(ftp_url, prop_nr="P854", is_reference=True)
    filename_in_archive = f"{species_id}.tsv"
    # reference of filename in archive (P7793)
    ref_filename = wdi_core.WDString(
        filename_in_archive, prop_nr="P7793", is_reference=True
    )
    references = [[stated_in, retrieved, ref_url, ref_filename]]
    return references


def get_columns_to_keep():
    keep = [
        "#Complex ac",
        "Recommended name",
        "Aliases for complex",
        "Taxonomy identifier",
        "Go Annotations",
        "Identifiers (and stoichiometry) of molecules in complex",
        "Description",
    ]
    return keep
