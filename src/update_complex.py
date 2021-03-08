# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src

import pandas as pd
from wikidataintegrator import wdi_login
import utils
from login import WDPASS, WDUSER
import argparse
import sys
parser = argparse.ArgumentParser()

def main():
    parser.add_argument('--species', '-s', help="a species id", type= str)
    parser.add_argument('--wikidata', '-w', help="1 to exclude complexes on Wikidata, 0 to include", type= int, default= 1)
    
    args = parser.parse_args()

    if len(sys. argv) < 4:
        sys.exit("Usage: python3 update_complex.py -s [species id] -w [boolean]")
    id = args.species
    test_on_wikidata = bool(args.wikidata)
    dataset_urls = utils.get_complex_portal_dataset_urls()

    # Make a dataframe for all complexes of a given species
    list_of_complexes = utils.get_list_of_complexes(dataset_urls, species_id=id,test_on_wikidata=test_on_wikidata)
    login_instance = wdi_login.WDLogin(user=WDUSER, pwd=WDPASS)

    references = utils.prepare_refs(species_id=id)

    print("===== Updating complexes on Wikidata =====")
    for protein_complex in list_of_complexes:
        print(protein_complex.complex_id)
        utils.update_complex(login_instance, protein_complex, references)

if __name__ == "__main__":
    main()