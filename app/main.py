import os
from decimal import Decimal
from urllib.parse import quote
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE = os.getenv('FUSEKI_URL', 'http://localhost:3030').rstrip('/')
AUTH = (os.getenv('FUSEKI_USER', 'admin'), os.getenv('FUSEKI_PASSWORD', 'change-me-local'))
EX = 'http://example.com/ecommerce/'
app = FastAPI(title='Ontology-backed Ecommerce API')

class Product(BaseModel):
    id: str = Field(pattern=r'^[A-Za-z0-9_-]+$')
    name: str
    price: Decimal = Field(ge=0)

class Customer(BaseModel):
    id: str = Field(pattern=r'^[A-Za-z0-9_-]+$')
    name: str
    email: str

class Order(BaseModel):
    id: str = Field(pattern=r'^[A-Za-z0-9_-]+$')
    customer_id: str = Field(pattern=r'^[A-Za-z0-9_-]+$')
    product_id: str = Field(pattern=r'^[A-Za-z0-9_-]+$')


def sparql(query, update=False):
    url = BASE + ('/ecommerce/update' if update else '/ecommerce/sparql')
    try:
        if update:
            r = requests.post(url, data={'update': query}, auth=AUTH, timeout=15)
        else:
            r = requests.post(url, data={'query': query}, headers={'Accept': 'application/sparql-results+json'}, timeout=15)
        r.raise_for_status()
        return None if update else r.json()['results']['bindings']
    except requests.RequestException as e:
        raise HTTPException(502, f'Fuseki request failed: {e}')

def lit(value):
    # RDFLib safely escapes SPARQL literals.
    from rdflib import Literal
    return Literal(value).n3()

@app.get('/health')
def health():
    try:
        sparql('ASK {}')
        return {'status': 'ok'}
    except HTTPException:
        raise HTTPException(503, 'Fuseki unavailable')

@app.get('/products')
def products():
    q = f'''PREFIX ex: <{EX}>
    SELECT ?product ?name ?price WHERE {{ ?product a ex:Product ; ex:productName ?name ; ex:productPrice ?price . }}'''
    return [{'id': x['product']['value'].split('#')[-1], 'name': x['name']['value'], 'price': x['price']['value']} for x in sparql(q)]

@app.post('/products', status_code=201)
def create_product(p: Product):
    iri = f'<{EX}{p.id}>'
    sparql(f'''PREFIX ex: <{EX}> INSERT DATA {{ {iri} a ex:Product ; ex:productName {lit(p.name)} ; ex:productPrice {lit(p.price)} . }}''', update=True)
    return {'id': p.id}

@app.post('/customers', status_code=201)
def create_customer(c: Customer):
    iri = f'<{EX}{c.id}>'
    sparql(f'''PREFIX ex: <{EX}> INSERT DATA {{ {iri} a ex:Customer ; ex:customerName {lit(c.name)} ; ex:customerEmail {lit(c.email)} . }}''', update=True)
    return {'id': c.id}

@app.post('/orders', status_code=201)
def create_order(o: Order):
    customer, product, order = [f'<{EX}{x}>' for x in (o.customer_id, o.product_id, o.id)]
    ask = f'''PREFIX ex: <{EX}> ASK {{ {customer} a ex:Customer . {product} a ex:Product . }}'''
    # ASK returns a boolean, not SELECT bindings.
    r = requests.post(BASE + '/ecommerce/sparql', data={'query': ask}, headers={'Accept': 'application/sparql-results+json'}, timeout=15)
    r.raise_for_status()
    if not r.json().get('boolean'):
        raise HTTPException(400, 'Customer or product not found')
    sparql(f'''PREFIX ex: <{EX}> INSERT DATA {{ {order} a ex:Order ; ex:orderStatus "Created" ; ex:containsProduct {product} . {customer} ex:placesOrder {order} . }}''', update=True)
    return {'id': o.id}

@app.get('/customers/{customer_id}/orders')
def customer_orders(customer_id: str):
    if not customer_id.replace('-', '').replace('_', '').isalnum():
        raise HTTPException(400, 'Invalid customer ID')
    q = f'''PREFIX ex: <{EX}> SELECT ?order ?product WHERE {{
      <{EX}{customer_id}> ex:placesOrder ?order .
      ?order ex:containsProduct ?product . }}'''
    return [{'order': x['order']['value'], 'product': x['product']['value']} for x in sparql(q)]

from fastapi.responses import FileResponse
from pathlib import Path

@app.get('/', include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')
