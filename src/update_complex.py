# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src

from wikidataintegrator import wdi_login
import pandas as pd
import utils
from login import WDUSER, WDPASS

# Make a dataframe for  all complexes of a species
dataset_urls = utils.get_complex_portal_dataset_urls()

# Make a dataframe for with all complexes of a given species
# 2697049 is SARS-CoV-2
species_dataframe = utils.prepare_species_dataframe(dataset_urls, species_id="2697049")

# Split in a list of unique complexes
complex_dfs = utils.split_complexes(species_dataframe)

login_instance = wdi_login.WDLogin(user=WDUSER, pwd=WDPASS)

# Update Wikidata
references = utils.prepare_refs()

for df in complex_dfs:
    print(df["#Complex ac"].unique()[0])
    utils.update_complex(df, references)