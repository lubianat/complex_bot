A bot that updates Wikidata with information from the Complex Portal

* [Page on Wikidata](https://www.wikidata.org/wiki/User:ProteinBoxBot/2020_complex_portal#Status)
* [Example of an working bot](https://github.com/SuLab/scheduled-bots/blob/main/scheduled_bots/wikipathways/bot.py)


Data from http://ftp.ebi.ac.uk/pub/databases/intact/complex/current/complextab/.

Usage: python3 update_complex.py -s [species id] -w [boolean]

arser.add_argument('--species', '-s', help="a species id", type= str)
parser.add_argument('--wikidata', '-w', help="1 to exclude complexes on Wikidata, 0 to include", type= int, default= 1)
# Main contributors

* Tiago Lubiana (@lubianat)
* Birgit Meldal
* Egon Willighagen
* Andra Waagmesster
* João Vitor Ferreira ((@jvfe)



(README updated in 15/01/2021)