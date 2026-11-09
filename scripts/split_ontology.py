
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, URIRef

source = Path("ontology/ecommerce-combined.ttl")
schema_file = Path("ontology/ecommerce.ttl")
data_file = Path("ontology/sample-data.ttl")

combined = Graph()
combined.parse(source, format="turtle")

schema = Graph()
data = Graph()

for prefix, namespace in combined.namespaces():
    schema.bind(prefix, namespace)
    data.bind(prefix, namespace)

# Find the four ecommerce classes by their labels
# or their IRI local names.
def local_name(uri):
    return str(uri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]

class_names = {"Customer", "Product", "Order", "Payment"}

domain_classes = set()

for subject in combined.subjects(RDF.type, OWL.Class):
    labels = {
        str(label)
        for label in combined.objects(subject, RDFS.label)
    }
    if local_name(subject) in class_names or labels & class_names:
        domain_classes.add(subject)

# Identify individuals based on their class assertions.
individuals = set()

for subject, cls in combined.subject_objects(RDF.type):
    if cls in domain_classes:
        individuals.add(subject)

# Split simple named-individual assertions from schema.
for s, p, o in combined:
    if s in individuals:
        data.add((s, p, o))
    else:
        schema.add((s, p, o))

schema.serialize(destination=schema_file, format="turtle")
data.serialize(destination=data_file, format="turtle")

print("Classes found:", len(domain_classes))
print("Individuals found:", len(individuals))
print("Schema triples:", len(schema))
print("Data triples:", len(data))
print("Created:", schema_file)
print("Created:", data_file)
