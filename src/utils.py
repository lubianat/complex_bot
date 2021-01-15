# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src


from wikidataintegrator.wdi_core import WDItemEngine
from collections import defaultdict
from functools import lru_cache, reduce
from ftplib import FTP
import pandas as pd


def get_wikidata_complexes():
    """Gets all Wikidata items with a Complex Portal ID property"""

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


def get_complex_portal_datasets():
    """Gets a dictionary of Complex portal datasets
    Returns a dictionary of species as keys and dataset url as values.
    """
    domain = "ftp.ebi.ac.uk"
    complex_data = "pub/databases/intact/complex/current/complextab/"

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


def return_missing_from_wikidata(complexp_dataframe):
    """
    Return complex portal entities that don't have Wikidata links.
    """
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
        "Identifiers (and stoichiometry) of molecules in complex",
        "Description",
    ]

    missing_from_wikidata = missing_from_wikidata[keep]

    return missing_from_wikidata