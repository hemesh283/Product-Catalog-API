def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_products_returns_all_products(client):
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 7


def test_get_product_returns_matching_product(client):
    response = client.get("/products/3")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 3
    assert body["name"] == "27-inch Monitor"


def test_get_missing_product_returns_404(client):
    response = client.get("/products/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Product 999 not found"}


def test_invalid_product_id_returns_422(client):
    response = client.get("/products/abc")
    assert response.status_code == 422

# ---------- Caching ----------

def test_first_request_is_miss_then_hit(client):
    first = client.get("/products/3")
    second = client.get("/products/3")
    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"
    assert first.json() == second.json()


def test_product_list_is_cached(client):
    assert client.get("/products").headers["X-Cache"] == "MISS"
    assert client.get("/products").headers["X-Cache"] == "HIT"


def test_cache_still_hits_at_exactly_ttl(client, clock):
    client.get("/products/3")
    clock.advance(30)
    assert client.get("/products/3").headers["X-Cache"] == "HIT"


def test_cache_expires_after_ttl(client, clock):
    client.get("/products/3")
    clock.advance(31)
    assert client.get("/products/3").headers["X-Cache"] == "MISS"


def test_cache_is_separate_per_path(client):
    client.get("/products/3")
    assert client.get("/products/4").headers["X-Cache"] == "MISS"


def test_missing_product_is_not_cached(client):
    client.get("/products/999")
    second = client.get("/products/999")
    assert second.status_code == 404
    assert "X-Cache" not in second.headers


def test_health_is_not_cached(client):
    assert "X-Cache" not in client.get("/health").headers


# ---------- Rate limiting ----------

def test_eleventh_request_is_rate_limited(client):
    for _ in range(10):
        assert client.get("/products").status_code == 200

    response = client.get("/products")
    assert response.status_code == 429
    body = response.json()
    assert body["detail"] == "Rate limit exceeded. Try again later."
    assert body["limit"] == 10
    assert body["window_seconds"] == 60
    assert body["retry_after"] == 60
    assert response.headers["Retry-After"] == "60"


def test_retry_after_is_rounded_up(client, clock):
    clock.advance(15.5)
    for _ in range(10):
        client.get("/products")
    assert client.get("/products").json()["retry_after"] == 45


def test_rate_limit_resets_in_next_window(client, clock):
    for _ in range(11):
        client.get("/products")
    clock.advance(60)
    assert client.get("/products").status_code == 200


def test_rate_limit_is_shared_across_endpoints(client):
    for _ in range(10):
        client.get("/products")
    assert client.get("/products/3").status_code == 429


def test_health_is_not_rate_limited(client):
    for _ in range(10):
        client.get("/products")
    assert client.get("/health").status_code == 200


def test_health_requests_do_not_count_towards_limit(client):
    for _ in range(20):
        client.get("/health")
    assert client.get("/products").status_code == 200