from typing import Callable

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app.cache import TTLCache
from app.data import PRODUCTS
from app.models import Product
from app.rate_limiter import FixedWindowRateLimiter

API_PREFIX = "/api"
CACHE_TTL_SECONDS = 30
RATE_LIMIT = 10
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_EXEMPT_PATHS = {
    "/health",
    f"{API_PREFIX}/docs",
    f"{API_PREFIX}/openapi.json",
    f"{API_PREFIX}/redoc",
}

app = FastAPI(
    title="Mini Product Catalog API",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)
router = APIRouter(prefix=API_PREFIX)
cache = TTLCache(ttl_seconds=CACHE_TTL_SECONDS)
rate_limiter = FixedWindowRateLimiter(
    limit=RATE_LIMIT, window_seconds=RATE_LIMIT_WINDOW_SECONDS
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in RATE_LIMIT_EXEMPT_PATHS:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    result = rate_limiter.check(client_ip)

    if not result.allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Try again later.",
                "limit": RATE_LIMIT,
                "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
                "retry_after": result.retry_after,
            },
            headers={"Retry-After": str(result.retry_after)},
        )

    return await call_next(request)


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


@router.get("/products")
def list_products(request: Request, response: Response) -> list[Product]:
    return get_or_compute(request, response, lambda: list(PRODUCTS.values()))


@router.get("/products/{product_id}")
def get_product(product_id: int, request: Request, response: Response) -> Product:
    return get_or_compute(request, response, lambda: find_product(product_id))


app.include_router(router)