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
list_of_complexes = utils.get_list_of_complexes(dataset_urls, species_id="2697049")


login_instance = wdi_login.WDLogin(user=WDUSER, pwd=WDPASS)

# Update Wikidata
references = utils.prepare_refs(species_id="2697049")

for protein_complex in list_of_complexes:
    print(protein_complex.complex_id)
    utils.update_complex(login_instance, protein_complex, references)