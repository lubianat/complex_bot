import pandas as pd
import requests

df = pd.read_csv("errors/rna_central_log.csv")
df = df.drop_duplicates()
taxid = []
genes = []

print(df)
for i, row in df.iterrows():

    rna_id = row["rna"]

    result = requests.get(f"https://rnacentral.org/api/v1/rna/{rna_id}/?format=json")

    info = result.json()
    print(info)

    taxid.append(info["taxid"])
    genes.append(info["genes"])


df.to_csv("errors/rna_central_log.csv")

df["taxid"] = taxid

df["genes"] = genes


df.to_csv("errors/rna_central_log_with_taxon_and_genes.csv")
