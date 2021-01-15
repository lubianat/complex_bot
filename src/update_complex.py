# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src

# %%
from wikidataintegrator import wdi_core, wdi_login
from time import gmtime, strftime
import pandas as pd
from utils import (
    get_complex_portal_datasets,
    return_missing_from_wikidata,
    get_wikidata_item_by_propertyvalue,
)

datasets = get_complex_portal_datasets()


def process_species_complextab(complextab_dataframe):
    """Clean and process complextab data

    Removes entries present in Wikidata and processes it into a "long"
    format, more friendly for editing.

    Args:
        complextab_dataframe (DataFrame): one of the species datasets,

    """
    species_missing_raw = return_missing_from_wikidata(complextab_dataframe)

    # Cleaning molecules column, they follow this format: 
    # uniprot_id(quantity)|another_uniprot_id(n)...
    molecules_column = "Identifiers (and stoichiometry) of molecules in complex"
    species_missing = separate_columns(species_missing_raw, molecules_column)

    return species_missing

def separate_columns(species_missing_raw, molecules_column):
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

    # Also need to group the resulting molecules, to avoid duplicates
    species_missing = (
        species_missing_raw.groupby(
            ["#Complex ac", "Recommended name", "Taxonomy identifier", "uniprot_id"]
        )
        .agg(has_part_quantity=pd.NamedAgg("has_part_quantity", "count"))
        .reset_index()
    )
    return species_missing


cov2_complextab = pd.read_table(datasets["sars-cov-2"], na_values=["-"])
cov2 = process_species_complextab(cov2_complextab)
cov2["found_in_taxon"] = [
    get_wikidata_item_by_propertyvalue("P685", int(taxid))
    for taxid in cov2["Taxonomy identifier"].to_list()
]
cov2["has_part"] = [
    get_wikidata_item_by_propertyvalue("P352", uniprot_id)
    for uniprot_id in cov2["uniprot_id"].to_list()
]

# Make a dataframe for each unique complex
complex_dfs = [
    cov2[cov2["#Complex ac"] == unique_complex].reset_index()
    for unique_complex in cov2["#Complex ac"].unique()
]
# %%
# login_instance = wdi_login.WDLogin(user='<bot user name>', pwd='<bot password>')

stated_in = wdi_core.WDItemID(value="Q47196990", prop_nr="P248", is_reference=True)
wikidata_time = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
retrieved = wdi_core.WDTime(wikidata_time, prop_nr="P813", is_reference=True)
references = [stated_in, retrieved]


for df in complex_dfs:

    update_complex(df, references)


def update_complex(complex_dataframe, references):
    """
    Args:
        complex_dataframe (DataFrame): information about a complex properly formatted. 
    """
    current_complex = complex_dataframe["#Complex ac"].unique()[0]
    taxon_id = complex_dataframe["found_in_taxon"][0]
    components = df["has_part"]

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