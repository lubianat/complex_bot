# Code modified from original by @jvfe (BSD2)
# Copyright (c) 2020, jvfe
# https://github.com/jvfe/wdt_contribs/tree/master/complex_portal/src
# Hacked during BioHackathon Europe 2021 by Tiago Lubiana

from time import gmtime, strftime
import pandas as pd
import utils
from login import WDPASS, WDUSER
import argparse
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm

parser = argparse.ArgumentParser()


def main():
    parser.add_argument("--species", "-s", help="a species species_id", type=str)
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
        help="the number of complexes to add",
        type=int,
        default=999999,
    )

    args = parser.parse_args()

    if len(sys.argv) < 2:
        sys.exit("Usage: python3 add_papers_to_complexes.py -s [species id]")

    species_id = args.species
    dataset_urls = utils.get_complex_portal_dataset_urls()

    raw_table = pd.read_table(dataset_urls[species_id], na_values=["-"])

    flag = 0
    import time

    cpx_list = []
    for i, row in tqdm(raw_table.iterrows(), total=raw_table.shape[0]):

        time.sleep(0.3)

        try:
            cpx = row["#Complex ac"]
            tqdm.write(cpx)
            cpx_list.append(cpx)

            cpx_list = list(set(cpx_list))
            xrefs = row["Cross references"]
            xrefs_in_pubmed = []

            for xref in xrefs.split("|"):
                if "pubmed" in xref:
                    xrefs_in_pubmed.append(
                        xref.replace("pubmed:", "").replace("(see-also)", "")
                    )

            xrefs_in_pubmed = list(set(xrefs_in_pubmed))
            pmids_in_sparql_format = '"' + '" "'.join(xrefs_in_pubmed) + '"'

            tqdm.write(pmids_in_sparql_format)
            query = (
                """
            SELECT 
            (REPLACE(STR(?item), ".*Q", "Q") AS ?qid)
            ?pmid
            WHERE {
                VALUES ?pmid { """
                + pmids_in_sparql_format
                + """ }.
                ?item wdt:P698 ?pmid . 

            }
            """
            )
            sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            df = pd.io.json.json_normalize(results["results"]["bindings"])
            df = df[["qid.value", "pmid.value"]]

            pmid_to_qid = {}
            for i, row in df.iterrows():
                pmid_to_qid[row["pmid.value"]] = row["qid.value"]

            cpxs_in_sparql_format = '"' + '" "'.join(cpx_list) + '"'

            query = (
                """
            SELECT 
            (REPLACE(STR(?item), ".*Q", "Q") AS ?qid)
            ?cpx
            WHERE {
                VALUES ?cpx { """
                + cpxs_in_sparql_format
                + """ }.
                ?item wdt:P7718 ?cpx . 

            }
            """
            )
            sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            df = pd.io.json.json_normalize(results["results"]["bindings"])
            df = df[["qid.value", "cpx.value"]]

            cpx_to_qid = {}
            for i, row in df.iterrows():
                cpx_to_qid[row["cpx.value"]] = row["qid.value"]

            with open("add_paper_quickstatements.qs", "a") as f:
                for xref in xrefs_in_pubmed:
                    s = cpx_to_qid[cpx]
                    p = "|P1343|"
                    o = pmid_to_qid[xref]

                    sp1 = "|S248|"
                    so1 = "Q47196990"

                    sp2 = "|S854|"
                    so2 = (
                        '"'
                        + dataset_urls[species_id].replace("ftp://", "https://")
                        + '"'
                    )

                    sp3 = "|S813|"
                    so3 = strftime("+%Y-%m-%dT00:00:00Z/11", gmtime())

                    statement = s + p + o + sp1 + so1 + sp2 + so2 + sp3 + so3
                    f.write(statement + "\n")

        except:
            with open("log.txt", "a") as f2:
                f2.write(cpx + "\n")
            tqdm.write("error")
            pass


if __name__ == "__main__":
    main()
