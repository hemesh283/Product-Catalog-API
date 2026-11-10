from fastapi import FastAPI, HTTPException

from app.data import PRODUCTS
from app.models import Product

app = FastAPI(title="Mini Product Catalog API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products")
def list_products() -> list[Product]:
    return list(PRODUCTS.values())


@app.get("/products/{product_id}")
def get_product(product_id: int) -> Product:
    product = PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product