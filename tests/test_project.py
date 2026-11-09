
"""
E-commerce Ontology - Local Test Suite

Run from the project root:

    python -m pytest tests/test_project.py -v

Dependencies:

    pip install pytest rdflib pyshacl

Validates:
    1. RDF graph loading
    2. OWL class declarations
    3. OWL object property declarations
    4. Object property domains and ranges
    5. Individual class membership
    6. Customer -> Order -> Product relationships
    7. Order -> Payment relationships
    8. SPARQL queries
    9. SHACL validation (positive)
   10. SHACL validation (negative)
"""

from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS


# ============================================================
# 1. Project configuration
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

ONTOLOGY = ROOT / "ontology" / "ecommerce.ttl"
DATA = ROOT / "ontology" / "sample-data.ttl"
SHAPES = ROOT / "shapes" / "ecommerce-shapes.ttl"


# ============================================================
# 2. Fixtures
# ============================================================

@pytest.fixture(scope="module")
def model():
    """Load ontology and instance data into a combined RDF graph."""

    for path in (ONTOLOGY, DATA, SHAPES):
        assert path.is_file(), f"Missing required file: {path}"

    graph = Graph()

    graph.parse(ONTOLOGY, format="turtle")
    graph.parse(DATA, format="turtle")

    # Detect the ontology namespace from the Customer class.
    customer_iris = [
        subject
        for subject in graph.subjects(RDF.type, OWL.Class)
        if str(subject).endswith(("#Customer", "/Customer"))
    ]

    assert len(customer_iris) == 1, (
        "Expected exactly one Customer OWL class. "
        f"Found: {customer_iris}"
    )

    customer_iri = str(customer_iris[0])
    namespace = Namespace(customer_iri[:-len("Customer")])

    return graph, namespace


@pytest.fixture(scope="module")
def shapes_graph():
    """Load SHACL constraints separately."""

    assert SHAPES.is_file(), f"Missing SHACL file: {SHAPES}"

    graph = Graph()
    graph.parse(SHAPES, format="turtle")

    return graph


@pytest.fixture(scope="module")
def schema_graph():
    """Load only ontology schema triples."""

    assert ONTOLOGY.is_file(), f"Missing ontology: {ONTOLOGY}"

    graph = Graph()
    graph.parse(ONTOLOGY, format="turtle")

    return graph


# ============================================================
# 3. RDF graph loading
# ============================================================

def test_graph_loaded(model):
    graph, _ = model

    assert len(graph) > 0, "RDF graph is empty"


def test_schema_loaded(schema_graph):
    assert len(schema_graph) > 0, "Ontology schema is empty"


def test_shapes_loaded(shapes_graph):
    assert len(shapes_graph) > 0, "SHACL shapes graph is empty"


# ============================================================
# 4. OWL class declarations
# ============================================================

@pytest.mark.parametrize(
    "class_name",
    [
        "Customer",
        "Product",
        "Order",
        "Payment",
    ]
)
def test_classes_exist(model, class_name):
    graph, ec = model

    class_uri = ec[class_name]

    assert (class_uri, RDF.type, OWL.Class) in graph, (
        f"Missing OWL class: {class_uri}"
    )


# ============================================================
# 5. OWL object property declarations
# ============================================================

@pytest.mark.parametrize(
    "property_name",
    [
        "placesOrder",
        "containsProduct",
        "hasPayment",
    ]
)
def test_object_properties_exist(model, property_name):
    graph, ec = model

    property_uri = ec[property_name]

    assert (property_uri, RDF.type, OWL.ObjectProperty) in graph, (
        f"Missing OWL ObjectProperty: {property_uri}"
    )


# ============================================================
# 6. Object property domain and range
# ============================================================

@pytest.mark.parametrize(
    "prop,domain,range_name",
    [
        ("placesOrder", "Customer", "Order"),
        ("containsProduct", "Order", "Product"),
        ("hasPayment", "Order", "Payment"),
    ]
)
def test_object_property_schema(model, prop, domain, range_name):
    graph, ec = model

    property_uri = ec[prop]

    assert (property_uri, RDF.type, OWL.ObjectProperty) in graph, (
        f"{prop} is not an OWL ObjectProperty"
    )

    actual_domains = list(
        graph.objects(property_uri, RDFS.domain)
    )

    assert ec[domain] in actual_domains, (
        f"\nProperty: {prop}\n"
        f"Expected domain: {ec[domain]}\n"
        f"Actual domains: {actual_domains}\n"
        "Check the rdfs:domain declaration in ecommerce.ttl."
    )

    actual_ranges = list(
        graph.objects(property_uri, RDFS.range)
    )

    assert ec[range_name] in actual_ranges, (
        f"\nProperty: {prop}\n"
        f"Expected range: {ec[range_name]}\n"
        f"Actual ranges: {actual_ranges}\n"
        "Check the rdfs:range declaration in ecommerce.ttl."
    )


# ============================================================
# 7. Individual class membership
# ============================================================

@pytest.mark.parametrize(
    "individual,class_name",
    [
        ("Customer101", "Customer"),
        ("Product101", "Product"),
        ("Order101", "Order"),
        ("Payment101", "Payment"),
    ]
)
def test_individual_types(model, individual, class_name):
    graph, ec = model

    individual_uri = ec[individual]
    class_uri = ec[class_name]

    assert (individual_uri, RDF.type, class_uri) in graph, (
        f"{individual} is not declared as {class_name}"
    )


# ============================================================
# 8. Customer -> Order relationship
# ============================================================

def test_customer_places_order(model):
    graph, ec = model

    assert (
        ec.Customer101,
        ec.placesOrder,
        ec.Order101
    ) in graph, (
        "Customer101 does not place Order101"
    )


# ============================================================
# 9. Order -> Product relationship
# ============================================================

def test_order_contains_product(model):
    graph, ec = model

    assert (
        ec.Order101,
        ec.containsProduct,
        ec.Product101
    ) in graph, (
        "Order101 does not contain Product101"
    )


# ============================================================
# 10. Order -> Payment relationship
# ============================================================

def test_order_has_payment(model):
    graph, ec = model

    assert (
        ec.Order101,
        ec.hasPayment,
        ec.Payment101
    ) in graph, (
        "Order101 is not associated with Payment101"
    )


# ============================================================
# 11. Complete customer -> order -> product path
# ============================================================

def test_customer_order_product_path(model):
    graph, ec = model

    customer_order = (
        ec.Customer101,
        ec.placesOrder,
        ec.Order101
    )

    order_product = (
        ec.Order101,
        ec.containsProduct,
        ec.Product101
    )

    assert customer_order in graph, (
        "Customer -> Order relationship missing"
    )

    assert order_product in graph, (
        "Order -> Product relationship missing"
    )


# ============================================================
# 12. SPARQL: Customer ordered products
# ============================================================

def test_sparql_customer_products(model):
    graph, ec = model

    query = """
        SELECT ?product
        WHERE {
            ?customer ec:placesOrder ?order .
            ?order ec:containsProduct ?product .
        }
    """

    rows = list(
        graph.query(
            query,
            initNs={"ec": ec},
            initBindings={
                "customer": ec.Customer101
            }
        )
    )

    products = [row.product for row in rows]

    assert ec.Product101 in products, (
        "SPARQL did not return Product101 for Customer101"
    )


# ============================================================
# 13. SPARQL: Customer orders
# ============================================================

def test_sparql_customer_orders(model):
    graph, ec = model

    query = """
        SELECT ?order
        WHERE {
            ?customer ec:placesOrder ?order .
        }
    """

    rows = list(
        graph.query(
            query,
            initNs={"ec": ec},
            initBindings={
                "customer": ec.Customer101
            }
        )
    )

    orders = [row.order for row in rows]

    assert ec.Order101 in orders, (
        "SPARQL did not return Order101 for Customer101"
    )


# ============================================================
# 14. SPARQL: Order payment
# ============================================================

def test_sparql_order_payment(model):
    graph, ec = model

    query = """
        SELECT ?payment
        WHERE {
            ?order ec:hasPayment ?payment .
        }
    """

    rows = list(
        graph.query(
            query,
            initNs={"ec": ec},
            initBindings={
                "order": ec.Order101
            }
        )
    )

    payments = [row.payment for row in rows]

    assert ec.Payment101 in payments, (
        "SPARQL did not return Payment101 for Order101"
    )


# ============================================================
# 15. SHACL: Valid data
# ============================================================

def test_shacl_valid_data(model, shapes_graph):
    graph, _ = model

    conforms, _, report = validate(
        data_graph=graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        advanced=False,
    )

    assert conforms, (
        f"SHACL validation failed:\n{report}"
    )


# ============================================================
# 16. SHACL: Reject missing customer name
# ============================================================

def test_shacl_rejects_missing_customer_name(
    model,
    shapes_graph
):
    graph, ec = model

    # Copy to avoid modifying the shared fixture.
    invalid_graph = Graph()
    invalid_graph += graph

    invalid_graph.remove(
        (
            ec.Customer101,
            ec.customerName,
            None
        )
    )

    conforms, _, report = validate(
        data_graph=invalid_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
    )

    assert not conforms, (
        "SHACL accepted a Customer without customerName. "
        "Check sh:minCount 1 in CustomerShape.\n"
        f"{report}"
    )


# ============================================================
# 17. SHACL: Reject missing customer email
# ============================================================

def test_shacl_rejects_missing_customer_email(
    model,
    shapes_graph
):
    graph, ec = model

    invalid_graph = Graph()
    invalid_graph += graph

    invalid_graph.remove(
        (
            ec.Customer101,
            ec.customerEmail,
            None
        )
    )

    conforms, _, report = validate(
        data_graph=invalid_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
    )

    assert not conforms, (
        "SHACL accepted a Customer without customerEmail. "
        "Check the CustomerShape constraints.\n"
        f"{report}"
    )


# ============================================================
# 18. Namespace consistency
# ============================================================

def test_namespace_consistency(model):
    graph, ec = model

    expected_classes = [
        ec.Customer,
        ec.Product,
        ec.Order,
        ec.Payment,
    ]

    for class_uri in expected_classes:
        assert isinstance(class_uri, URIRef)

        assert (class_uri, RDF.type, OWL.Class) in graph, (
            f"Namespace mismatch or missing class: {class_uri}"
        )


# ============================================================
# End of test suite
# ============================================================
