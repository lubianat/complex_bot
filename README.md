A bot that updates Wikidata with information from the Complex Portal

* [Page on Wikidata](https://www.wikidata.org/wiki/User:ProteinBoxBot/2020_complex_portal#Status)
* [Example of an working bot](https://github.com/SuLab/scheduled-bots/blob/main/scheduled_bots/wikipathways/bot.py)


Data from http://ftp.ebi.ac.uk/pub/databases/intact/complex/current/complextab/.

Usage: python3 update_complex.py -s [species id] -w [boolean]

Arguments:

    --species/-s : a species NCBI ID
    --wikidata/-w : 1 to add new complex to Wikidata, 0 to also update the existing ones.
    --number/-n: The number of complexes to add to Wikidata.

Currently, errors are added to the errors/log folder.

To run for all species, run: 

```
python3 src/update_all_complexes.py -w 0 -n 99999

```

## Species IDs:

To know the current species covered by Complex Portal, run 

` python3 check_ids.py` .

You should get a table similar to the one below:


|      | itemLabel                       |      id |
| ---: | :------------------------------ | ------: |
|    0 | house mouse                     |   10090 |
|    1 | Marbled electric ray            |    7788 |
|    2 | Oryctolagus cuniculus           |    9986 |
|    3 | Red Junglefowl                  |    9031 |
|    4 | Escherichia coli                |     562 |
|    5 | Tetronarce californica          |    7787 |
|    6 | Caenorhabditis elegans          |    6239 |
|    7 | Drosophila melanogaster         |    7227 |
|    8 | Ovis aries                      |    9940 |
|    9 | Arabidopsis thaliana            |    3702 |
|   10 | Lymnaea stagnalis               |    6523 |
|   11 | Homo sapiens                    |    9606 |
|   12 | Canis lupus familiaris          |    9615 |
|   13 | African clawed frog             |    8355 |
|   14 | Danio rerio                     |    7955 |
|   15 | Bos taurus                      |    9913 |
|   16 | wild boar                       |    9823 |
|   17 | brown rat                       |   10116 |
|   18 | Escherichia coli K-12           |   83333 |
|   19 | SARSr-CoV                       |  694009 |
|   20 | Pseudomonas aeruginosa PAO1     |  208964 |
|   21 | Schizosaccharomyces pombe 972h- |  284812 |
|   22 | Saccharomyces cerevisiae S288c  |  559292 |
|   23 | SARS-CoV-2                      | 2697049 |

# Main contributors

* Tiago Lubiana (@lubianat)
* Birgit Meldal
* Egon Willighagen
* Andra Waagmesster
* João Vitor Ferreira ((@jvfe)



(README updated in 15/01/2021)