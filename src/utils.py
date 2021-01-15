# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src

from wikidataintegrator import wdi_core
from wikidataintegrator.wdi_core import WDItemEngine
from time import gmtime, strftime
from collections import defaultdict
from functools import lru_cache, reduce
from ftplib import FTP
import pandas as pd
import re

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
            print(f"===== Getting {current_key} ====== ")
            cp_datasets[current_key] = f"ftp://{domain}/{complex_data}{species}"

    return cp_datasets


def return_missing_from_wikidata(complexp_dataframe):
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


def process_species_complextab(complextab_dataframe):
    """Clean and process complextab data

    Removes entries present in Wikidata and processes it into a "long"
    format, more friendly for editing.

    Args:
        complextab_dataframe (DataFrame): one of the species datasets,

    """
    species_table_raw = return_missing_from_wikidata(complextab_dataframe)

    # Cleaning molecules column, they follow this format: 
    # uniprot_id(quantity)|another_uniprot_id(n)...
    molecules_column = "Identifiers (and stoichiometry) of molecules in complex"
    species_table = separate_molecules_column(species_table_raw, molecules_column)


    go_column = "Go Annotations"

    def extract_go_ids(go_string):
        go_list = re.findall(pattern="GO:[0-9]*", string=go_string)
        return go_list

    print(species_table_raw[go_column])
    go_ids = [extract_go_ids(go_string) for go_string in species_table_raw[go_column]]
    # print(go_ids)
    # species_table["go_ids"] = go_ids
    # species_table["aliases"] = species_table_raw["Aliases for complex"]
    # print(species_table.head(2).explode("go_ids"))


    return species_table

def separate_molecules_column(species_missing_raw, molecules_column):
    species_missing_raw[molecules_column] = species_missing_raw[
        molecules_column
    ].str.split("|")

    species_missing_raw = species_missing_raw.explode(molecules_column)

    species_missing_raw["has_part_quantity"] = species_missing_raw[
        molecules_column
    ].str.extract(r"\(([\d]+)\)", expand=False)

    species_missing_raw["uniprot_id"] = species_missing_raw[
        molecules_column
    ].str.replace(r"\(.*\)", "")

    
    print(species_missing_raw)
    # Also need to group the resulting molecules, to avoid duplicates
    species_missing = (
        species_missing_raw.groupby(
            ["#Complex ac", "Recommended name", "Taxonomy identifier", "uniprot_id"]
        )
        .agg(has_part_quantity=pd.NamedAgg("has_part_quantity", "count"))
        .reset_index()
    )
    print(species_missing)
    return species_missing

def update_complex(complex_dataframe, references):
    """
    Args:
        complex_dataframe (DataFrame): information about a complex properly formatted. 
    """
    current_complex = complex_dataframe["#Complex ac"].unique()[0]
    taxon_id = complex_dataframe["found_in_taxon"][0]
    components = complex_dataframe["has_part"]

    instance_of = wdi_core.WDItemID(value="Q22325163", prop_nr="P31")
    found_in_taxon = wdi_core.WDItemID(value=taxon_id, prop_nr="P703")
    complex_portal_id = wdi_core.WDString(
        value=current_complex, prop_nr="P7718", references=references
    )

    data = [instance_of, found_in_taxon, complex_portal_id]

    has_parts = [
        wdi_core.WDItemID(value=protein, prop_nr="P703") for protein in components
    ]

    data.extend(has_parts)

    # wd_item = wdi_core.WDItemEngine(data=data)
    # wd_item.write(login_instance)


def prepare_species_dataframe(datasets, species_id="sars-cov-2"):
    species_complex_table = pd.read_table(datasets[species_id], na_values=["-"])
    processed_complex_table = process_species_complextab(species_complex_table)

    processed_complex_table["found_in_taxon"] = [
        get_wikidata_item_by_propertyvalue("P685", int(taxid))
        for taxid in processed_complex_table["Taxonomy identifier"].to_list()
    ]

    processed_complex_table["has_part"] = [
        get_wikidata_item_by_propertyvalue("P352", uniprot_id)
        for uniprot_id in processed_complex_table["uniprot_id"].to_list()
    ]
    return processed_complex_table

def split_complexes(species_dataframe):
    complex_dfs = [
    species_dataframe[species_dataframe["#Complex ac"] == unique_complex].reset_index()
    for unique_complex in species_dataframe["#Complex ac"].unique()
    ]
    return(complex_dfs)   


def prepare_refs():
    stated_in = wdi_core.WDItemID(value="Q47196990", prop_nr="P248", is_reference=True)
    wikidata_time = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
    retrieved = wdi_core.WDTime(wikidata_time, prop_nr="P813", is_reference=True)
    references = [stated_in, retrieved]
    return references

   