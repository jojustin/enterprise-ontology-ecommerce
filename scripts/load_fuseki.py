
"""
Load e-commerce ontology and sample data into Apache Jena Fuseki.

Run:
    python scripts/load_fuseki.py

Environment variables:
    FUSEKI_URL
    FUSEKI_DATASET
    FUSEKI_USER
    FUSEKI_PASSWORD
"""

from pathlib import Path
import os
import sys

import requests
from requests.auth import HTTPBasicAuth
from rdflib import Graph


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

ONTOLOGY = ROOT / "ontology" / "ecommerce.ttl"
DATA = ROOT / "ontology" / "sample-data.ttl"

FUSEKI_BASE = os.getenv(
    "FUSEKI_URL", "http://localhost:3030"
).rstrip("/")

DATASET = os.getenv("FUSEKI_DATASET", "ecommerce")

FUSEKI_USER = os.getenv("FUSEKI_USER", "admin")
FUSEKI_PASSWORD = os.getenv("FUSEKI_PASSWORD")

if not FUSEKI_PASSWORD:
    sys.exit(
        "ERROR: FUSEKI_PASSWORD environment variable is not set."
    )

AUTH = HTTPBasicAuth(FUSEKI_USER, FUSEKI_PASSWORD)

GRAPH_URL = f"{FUSEKI_BASE}/{DATASET}/data"
QUERY_URL = f"{FUSEKI_BASE}/{DATASET}/query"


# ---------------------------------------------------------
# Load RDF files
# ---------------------------------------------------------

def load_graph():
    graph = Graph()

    for path in [ONTOLOGY, DATA]:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing RDF file: {path}"
            )

        graph.parse(path, format="turtle")
        print(f"Loaded {path.name}")

    print(f"Total local triples: {len(graph)}")

    return graph


# ---------------------------------------------------------
# Upload RDF data to Fuseki
# ---------------------------------------------------------

def upload_to_fuseki(graph):
    payload = graph.serialize(format="turtle")

    print(f"\nUploading to {GRAPH_URL}?default")

    response = requests.put(
        GRAPH_URL,
        params={"default": ""},
        data=payload.encode("utf-8"),
        headers={"Content-Type": "text/turtle"},
        auth=AUTH,
        timeout=30
    )

    if not response.ok:
        print(f"HTTP error: {response.status_code}")
        print("Response:", response.text[:2000])

        if response.status_code == 401:
            print("Authentication failed. Check admin credentials.")

        elif response.status_code == 403:
            print("Authenticated user lacks write permissions.")

        elif response.status_code == 404:
            print("Dataset or Graph Store endpoint not found.")

        elif response.status_code == 405:
            print(
                "Write method not allowed. Check whether "
                "the dataset has a writable /data endpoint."
            )

        response.raise_for_status()

    print("RDF graph uploaded successfully.")


# ---------------------------------------------------------
# Verify data in Fuseki
# ---------------------------------------------------------

def verify_fuseki():
    query = """
        SELECT (COUNT(*) AS ?count)
        WHERE {
            ?s ?p ?o
        }
    """

    response = requests.get(
        QUERY_URL,
        params={"query": query},
        headers={
            "Accept": "application/sparql-results+json"
        },
        auth=AUTH,
        timeout=30
    )

    response.raise_for_status()

    results = response.json()

    count = results["results"]["bindings"][0]["count"]["value"]

    print(f"Fuseki default-graph triple count: {count}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    try:
        graph = load_graph()
        upload_to_fuseki(graph)
        verify_fuseki()

    except requests.RequestException as exc:
        print(f"\nFuseki HTTP error: {exc}")
        sys.exit(1)

    except Exception as exc:
        print(f"\nError: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
