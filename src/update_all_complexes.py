# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src

import pandas as pd
from wikidataintegrator import wdi_login
import utils

# Imported from the environment on Jenkins
# from login import WDPASS, WDUSER
import argparse
import sys
import os

print("Logging in...")
if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WDUSER = os.environ["WDUSER"]
    WDPASS = os.environ["WDPASS"]
else:
    raise ValueError(
        "WDUSER and WDPASS must be specified in local.py or as environment variables"
    )

parser = argparse.ArgumentParser()


def main():
    parser.add_argument(
        "--wikidata",
        "-w",
        help="1 to exclude complexes on Wikidata, 0 to include",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--number",
        "-n",
        help="the number of complexes per species to add",
        type=int,
        default=999999,
    )

    args = parser.parse_args()

    if len(sys.argv) < 3:
        sys.exit(
            "Usage: python3 update_all_complexes.py -w [boolean] -n [number of complexes]"
        )
    species_df = utils.get_complex_portal_species_ids()
    species_ids = species_df["id"].values

    test_on_wikidata = bool(args.wikidata)
    number_of_complexes_to_add = args.number
    dataset_urls = utils.get_complex_portal_dataset_urls()

    for species_id in species_ids:
        # Make a dataframe for all complexes of a given species
        list_of_complexes = utils.get_list_of_complexes(
            dataset_urls,
            species_id=species_id,
            test_on_wikidata=test_on_wikidata,
            max_complexes=number_of_complexes_to_add,
        )
        login_instance = wdi_login.WDLogin(user=WDUSER, pwd=WDPASS)

        references = utils.prepare_refs(species_id=species_id)

        print("===== Updating complexes on Wikidata =====")

        for protein_complex in list_of_complexes:
            print(protein_complex.complex_id)
            utils.update_complex(login_instance, protein_complex, references)


if __name__ == "__main__":
    main()
