from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Response

from app.cache import TTLCache
from app.data import PRODUCTS
from app.models import Product

CACHE_TTL_SECONDS = 30

app = FastAPI(title="Mini Product Catalog API")
cache = TTLCache(ttl_seconds=CACHE_TTL_SECONDS)


def cache_key(request: Request) -> str:
    query = request.url.query
    return f"{request.url.path}?{query}" if query else request.url.path


def get_or_compute(request: Request, response: Response, compute: Callable):
    key = cache_key(request)
    cached = cache.get(key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return cached

    value = compute()
    cache.set(key, value)
    response.headers["X-Cache"] = "MISS"
    return value


def find_product(product_id: int) -> Product:
    product = PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products")
def list_products(request: Request, response: Response) -> list[Product]:
    return get_or_compute(request, response, lambda: list(PRODUCTS.values()))


@app.get("/products/{product_id}")
def get_product(product_id: int, request: Request, response: Response) -> Product:
    return get_or_compute(request, response, lambda: find_product(product_id))