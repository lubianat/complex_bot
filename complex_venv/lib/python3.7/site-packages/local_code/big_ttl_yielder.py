from shexer.io.graph.yielder.big_ttl_triples_yielder import BigTtlTriplesYielder


source_file = r"F:\datasets\wikidata\wikidata-20150518-all-BETA.ttl\wikidata-20150518-all-BETA.ttl"

yielder = BigTtlTriplesYielder(source_file=source_file,
                               allow_untyped_numbers=True)

for a_triple in yielder.yield_triples():
    print(a_triple[0], a_triple[1], a_triple[2])

# import os.path as pth
#
#
# r = pth.join(pth.dirname(pth.normpath(__file__)), "t_files" + pth.sep)
# print(pth.sep)
# print(r)
# print(type(r))