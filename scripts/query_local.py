import sys
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL

ontology = sys.argv[1] if len(sys.argv) > 1 else 'ontology/ecommerce.ttl'

data = sys.argv[2] if len(sys.argv) > 2 else 'ontology/sample-data.ttl'
g = Graph().parse(ontology, format='turtle')
if data: g.parse(data, format='turtle')
print(f'Loaded {len(g)} triples')

# Resolve by rdfs:label so opaque WebProtege IRIs work too.
def find(label, rdf_type=None):
    for s in g.subjects(RDFS.label, None):
        if any(str(v) == label for v in g.objects(s, RDFS.label)):
            if rdf_type is None or (s, RDF.type, rdf_type) in g:
                return s
    for s in set(g.subjects()):
        if str(s).rstrip('/#').split('/')[-1].split('#')[-1] == label:
            return s
    raise ValueError(f'Cannot find entity {label!r}; inspect the exported TTL first')

places = find('placesOrder', OWL.ObjectProperty)
contains = find('containsProduct', OWL.ObjectProperty)
print('Customers and their ordered products:')
query = '''SELECT ?customer ?product WHERE { ?customer ?places ?order . ?order ?contains ?product . }'''
# Predicate variables are explicitly bound with VALUES to avoid dependence on prefixes.
from rdflib.plugins.sparql.processor import prepareQuery
q = prepareQuery('SELECT ?customer ?product WHERE { ?customer ?places ?order . ?order ?contains ?product . }')
for customer, product in g.query(q, initBindings={'places': places, 'contains': contains}):
    print(' -', customer, '->', product)
