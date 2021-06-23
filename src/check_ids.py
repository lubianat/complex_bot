import pandas as pd
from wikidataintegrator import wdi_login
import utils
from login import WDPASS, WDUSER
import argparse
import sys

parser = argparse.ArgumentParser()
df = utils.get_complex_portal_species_ids()

print(df.to_markdown()) 