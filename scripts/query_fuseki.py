import os, requests
base = os.getenv('FUSEKI_URL', 'http://localhost:3030').rstrip('/')
query = '''PREFIX ex: <http://example.com/ecommerce#>
SELECT ?customer ?product WHERE {
 ?customer ex:placesOrder ?order .
 ?order ex:containsProduct ?product .
}'''
r = requests.get(base + '/ecommerce/sparql', params={'query': query}, headers={'Accept': 'application/sparql-results+json'}, timeout=15)
r.raise_for_status()
for item in r.json()['results']['bindings']:
    print(item['customer']['value'], '->', item['product']['value'])
