import sys
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL

path = sys.argv[1] if len(sys.argv) > 1 else 'ontology/ecommerce.ttl'
g = Graph().parse(path, format='turtle')
print(f'Loaded {len(g)} triples from {path}')
for kind, name in [(OWL.Class, 'Classes'), (OWL.ObjectProperty, 'Object properties'), (OWL.DatatypeProperty, 'Data properties')]:
    print(f'\n{name}:')
    for s in sorted(g.subjects(RDF.type, kind), key=str):
        print(' -', next((str(x) for x in g.objects(s, RDFS.label)), str(s)))
print('\nSample triples:')
for i, (s, p, o) in enumerate(g):
    if i == 10: break
    print(s, p, o)
