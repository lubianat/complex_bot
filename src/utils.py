# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src

import logging
import math
import re
from collections import defaultdict
from ftplib import FTP
from functools import lru_cache, reduce
from time import gmtime, strftime

import pandas as pd
from wikidataintegrator import wdi_core
from wikidataintegrator.wdi_core import WDItemEngine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8",
    level=logging.INFO,
)


class ComplexComponent:
    def __init__(self, uniprot_id, quantity):
        self.uniprot_id = uniprot_id
        self.quantity = quantity
        self.get_qid_for_component()

    def get_qid_for_component(self):
        # UniProt protein ID (P352)
        self.qid = get_wikidata_item_by_propertyvalue("P352", self.uniprot_id)


class Complex:
    def __init__(self, dataset, complex_id):
        self.complex_id = complex_id
        self.info = dataset[dataset["#Complex ac"] == complex_id]
        self.list_of_components = []
        self.go_ids = []
        self.get_components()
        self.get_go_ids()
        self.get_wikidata_ids()

    def get_components(self):
        molecules_column = "Identifiers (and stoichiometry) of molecules in complex"
        molecules_string = self.info[molecules_column].values[0]
        molecules = molecules_string.split("|")

        logging.info(molecules)

        matches = [re.search("\((.*)\)", i) for i in molecules]
        quantities = [m.group(1) for m in matches]

        matches = [re.search("(.*)\(.*\)", i) for i in molecules]
        uniprot_ids = [m.group(1) for m in matches]

        component_and_quantities = dict(zip(uniprot_ids, quantities))
        for uniprot_id in component_and_quantities:
            component = ComplexComponent(
                uniprot_id, component_and_quantities[uniprot_id]
            )
            self.list_of_components.append(component)

    def get_go_ids(self):
        go_column = "Go Annotations"
        try:
            go_string = self.info[go_column].values[0]
            go_list = re.findall(pattern="GO:[0-9]*", string=go_string)
            self.go_ids = go_list
        except Exception:
            logging.warning(f"No GOs for {self.complex_id}")

    def get_wikidata_ids(self):

        # NCBI taxonomy ID (P685)
        tax_id = self.info["Taxonomy identifier"].values[0]
        self.taxon_qid = get_wikidata_item_by_propertyvalue("P685", int(tax_id))


def get_list_of_complexes(datasets, species_id):
    """Clean and process table of complexes

    Parses table of complexes into Complex classes

    Args:
        complextab_dataframe (DataFrame): one of the species datasets

    Returns
        list_of_complexes (list): Objects of the Complex class


    """
    table_of_complexes_raw = pd.read_table(datasets[species_id], na_values=["-"])

    # table_of_complexes_raw = return_missing_from_wikidata(table_of_complexes_raw)
    keep = [
        "#Complex ac",
        "Recommended name",
        "Aliases for complex",
        "Taxonomy identifier",
        "Go Annotations",
        "Identifiers (and stoichiometry) of molecules in complex",
        "Description",
    ]

    table_of_complexes_raw = table_of_complexes_raw[keep]

    list_of_complexes = []

    for complex_id in table_of_complexes_raw["#Complex ac"]:
        list_of_complexes.append(Complex(table_of_complexes_raw, complex_id))

    return list_of_complexes


def get_wikidata_complexes():
    """Gets all Wikidata items with a Complex Portal ID property"""

    logging.info("======  Getting complexes on Wikidata  ======")

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


@lru_cache(maxsize=None)
def get_wikidata_item_by_propertyvalue(property, value):
    """Gets a Wikidata item for a determined property-value pair
    Args:
        property (str): The property to search
        value (str): The value of said property
    """

    query_result = WDItemEngine.execute_sparql_query(
        f'SELECT distinct ?item WHERE {{ ?item wdt:{property} "{value}" }}'
    )
    try:
        match = query_result["results"]["bindings"][0]
    except IndexError:
        logging.error(f"Couldn't find item for {value}")
        return pd.np.NaN
    qid = match["item"]["value"]

    qid = qid.split("/")[4]
    return qid


def get_complex_portal_dataset_urls():
    """Gets a dictionary of Complex portal datasets
    Returns a dictionary of species as keys and dataset url as values.
    """
    domain = "ftp.ebi.ac.uk"
    complex_data = "pub/databases/intact/complex/current/complextab/"

    logging.info("======  Getting Complex Portal datasets via FTP  ======")

    ftp = FTP(domain)
    ftp.login()
    ftp.cwd(complex_data)
    files = ftp.nlst()

    cp_datasets = defaultdict()

    string_replacements = (".tsv", ""), ("_", " ")

    for species in files:
        if "README" not in species:

            current_key = reduce(
                lambda a, kv: a.replace(*kv), string_replacements, species
            )
            logging.info(f"===== Getting {current_key} ====== ")
            cp_datasets[current_key] = f"ftp://{domain}/{complex_data}{species}"

    return cp_datasets


def return_missing_from_wikidata(complexp_dataframe):
    """
    Return complex portal entities that don't have Wikidata links.
    """

    logging.info("======  Checking which complexes are not on Wikidata  ======")

    wikidata_complexes = get_wikidata_complexes()

    merged_data = pd.merge(
        wikidata_complexes,
        complexp_dataframe,
        how="outer",
        left_on=["ComplexPortalID"],
        right_on=["#Complex ac"],
        indicator=True,
    )
    missing_from_wikidata = merged_data[merged_data["_merge"] == "right_only"][
        complexp_dataframe.columns
    ]
    keep = [
        "#Complex ac",
        "Recommended name",
        "Aliases for complex",
        "Taxonomy identifier",
        "Go Annotations",
        "Identifiers (and stoichiometry) of molecules in complex",
        "Description",
    ]

    missing_from_wikidata = missing_from_wikidata[keep]

    return missing_from_wikidata


def update_complex(login_instance, protein_complex, references):
    """
    Args:
        complex_dataframe (DataFrame): information about a complex properly formatted.
    """
    instance_of = wdi_core.WDItemID(
        value="Q22325163", prop_nr="P31", references=references
    )

    found_in_taxon = wdi_core.WDItemID(
        value=protein_complex.taxon_qid, prop_nr="P703", references=references
    )

    complex_portal_id = wdi_core.WDString(
        value=protein_complex.complex_id, prop_nr="P7718", references=references
    )

    data = [instance_of, found_in_taxon, complex_portal_id]

    has_parts = []
    for component in protein_complex.list_of_components:

        quantity = component.quantity
        component_qid = component.qid
        logging.info(component_qid)

        def isNaN(string):
            return string != string

        if isNaN(component_qid):
            break

        if quantity != "0" and not math.isnan(int(quantity)):
            logging.info(quantity)
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

    # Reference table via https://w.wiki/uW2
    go_statements = []

    go_reference = pd.read_csv("./reference_go_terms.csv")
    for go_term in protein_complex.go_ids:
        # Considers  that each term has only one GO type
        obj = go_reference[go_reference["id"] == go_term]["go_term"].values[0]
        prop = go_reference[go_reference["id"] == go_term]["go_props"].values[0]
        statement = wdi_core.WDItemID(value=obj, prop_nr=prop, references=references)
        go_statements.append(statement)

    data.extend(go_statements)

    if protein_complex.complex_id == "CPX-5742":
        wd_item = wdi_core.WDItemEngine(data=data)
        wd_item.write(login_instance)


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

    ftp_url = "ftp://ftp.ebi.ac.uk/pub/databases/intact/complex/current/complextab"
    ref_url = wdi_core.WDString(ftp_url, prop_nr="P854", is_reference=True)

    filename_in_archive = f"{species_id}.tsv"
    ref_filename = wdi_core.WDString(
        filename_in_archive, prop_nr="P7793", is_reference=True
    )

    references = [[stated_in, retrieved, ref_url, ref_filename]]
    return references
