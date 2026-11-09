import sys
from rdflib import Graph
from pyshacl import validate

ontology = sys.argv[1] if len(sys.argv) > 1 else 'ontology/ecommerce.ttl'
data = sys.argv[2] if len(sys.argv) > 2 else 'ontology/sample-data.ttl'
shapes = sys.argv[3] if len(sys.argv) > 3 else 'shapes/ecommerce-shapes.ttl'
g = Graph().parse(ontology, format='turtle')
g.parse(data, format='turtle')
s = Graph().parse(shapes, format='turtle')
conforms, _, report = validate(g, shacl_graph=s, inference='rdfs', abort_on_first=False)
print(report)
sys.exit(0 if conforms else 1)
