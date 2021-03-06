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
from wikidataintegrator import wdi_core
from wikidataintegrator.wdi_core import WDItemEngine


def get_list_of_complexes(datasets, species_id, test_on_wikidata=True):
    """
    Clean and process table of complexes

    Parses table of complexes into Complex classes

    Args:
        datasets (DataFrame): one of the species datasets
        species_id: The NCBI species ID
        def get_list_of_complexes(datasets, species_id, test_on_wikidata=True):
    test_on_wikidata: A boolean indicating whether to return only complexes that are or aren't on Wikidata. Defaults to True.

    Returns
        list_of_complexes (list): Objects of the Complex class

    """
    raw_table = pd.read_table(datasets[species_id], na_values=["-"])

    if test_on_wikidata:
        raw_table = remove_rows_on_wikidata(raw_table)

    cols_to_keep = get_cols_to_keep()
    raw_table = raw_table[cols_to_keep]

    list_of_complexes = []
    print("====== Parsing list to extract into class Complex ======")
    # Counter for bot test
    counter = 0
    for complex_id in raw_table["#Complex ac"]:
        counter = counter + 1
        list_of_complexes.append(Complex(raw_table, complex_id))
        if counter == 10:
            break
    return list_of_complexes


def get_cols_to_keep():
    keep = [
        "#Complex ac",
        "Recommended name",
        "Aliases for complex",
        "Taxonomy identifier",
        "Go Annotations",
        "Identifiers (and stoichiometry) of molecules in complex",
        "Description",
    ]
    return(keep)


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
        value=protein_complex.complex_id,
        prop_nr="P7718",
        references=references)

    data = [instance_of, found_in_taxon, complex_portal_id]

    has_parts = []
    for component in protein_complex.list_of_components:

        quantity = component.quantity
        component_qid = component.qid
        print(f"Component QID: {component_qid}")

        def isNaN(string):
            return string != string

        if isNaN(component_qid):
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

    # Reference table via https://w.wiki/uW2
    go_statements = []

    go_reference = pd.read_csv("./reference_go_terms.csv")
    for go_term in protein_complex.go_ids:
        # Considers  that each term has only one GO type
        obj = go_reference[go_reference["id"] == go_term]["go_term"].values[0]
        prop = go_reference[go_reference["id"]
                            == go_term]["go_props"].values[0]
        statement = wdi_core.WDItemID(
            value=obj, prop_nr=prop, references=references)
        go_statements.append(statement)

    data.extend(go_statements)
    label = protein_complex.name
    aliases = protein_complex.aliases
    descriptions = {
        "en": "macromolecular complex",
        "pt": "complexo macromolecular",
        "pt-br": "complexo macromolecular",
        "nl": "macromoleculair complex",
        "de": "makromolekularer Komplex"
    }

    wd_item = wdi_core.WDItemEngine(data=data)
    wd_item.set_label(label=label, lang="en")
    wd_item.set_aliases(aliases, lang='en')
    for lang, description in descriptions.items():
        wd_item.set_description(description, lang=lang)

    wd_item.write(login_instance)


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
        matches = [re.search(r"\((.*)\)", i) for i in molecules]
        quantities = [m.group(1) for m in matches]

        matches = [re.search(r"(.*)\(.*\)", i) for i in molecules]
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
            print(f"No GOs for {self.complex_id}")

    def get_wikidata_ids(self):

        # NCBI taxonomy ID (P685)
        tax_id = self.info["Taxonomy identifier"].values[0]
        self.taxon_qid = get_wikidata_item_by_propertyvalue(
            "P685", int(tax_id))


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
        print(f"Couldn't find item for {value}")
        with open("errors/log.txt", "a") as f:
            f.write(f"Couldn't find item for {value}")
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

    print("======  Getting Complex Portal datasets via FTP  ======")

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
            cp_datasets[current_key] = f"ftp://{domain}/{complex_data}{species}"

    return cp_datasets


def remove_rows_on_wikidata(complexp_dataframe):
    """
    Return complex portal entities that don't have Wikidata links.
    """

    print("======  Checking which complexes are not on Wikidata  ======")

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


def split_complexes(species_dataframe):
    complex_dfs = [
        species_dataframe[
            species_dataframe["#Complex ac"] == unique_complex
        ].reset_index()
        for unique_complex in species_dataframe["#Complex ac"].unique()
    ]
    return complex_dfs


def prepare_refs(species_id):
    stated_in = wdi_core.WDItemID(
        value="Q47196990",
        prop_nr="P248",
        is_reference=True)
    wikidata_time = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
    retrieved = wdi_core.WDTime(
        wikidata_time,
        prop_nr="P813",
        is_reference=True)

    ftp_url = "ftp://ftp.ebi.ac.uk/pub/databases/intact/complex/current/complextab"
    ref_url = wdi_core.WDString(ftp_url, prop_nr="P854", is_reference=True)

    filename_in_archive = f"{species_id}.tsv"
    ref_filename = wdi_core.WDString(
        filename_in_archive, prop_nr="P7793", is_reference=True
    )

    references = [[stated_in, retrieved, ref_url, ref_filename]]
    return references
