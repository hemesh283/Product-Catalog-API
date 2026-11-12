# Notes

Key decisions, and anything that broke and how it was fixed.

## Step 1: Project setup

**Decisions**
- Plain `venv` in `.venv`; four top-level pinned dependencies (`fastapi`, `uvicorn[standard]`, `httpx`, `pytest`).
- `httpx` is needed by FastAPI's `TestClient`; it is not related to caching.
- `uvicorn[standard]` adds `watchfiles`, which makes `--reload` work.
- Python 3.13+ creates its own `.gitignore` inside `.venv`. I kept `.venv/` in the root `.gitignore` anyway, for people on older Python.
- `.env` is ignored even though there are no secrets yet: `.gitignore` rules are preventive.

**Broke / fixed**
- `.gitignore` rule `pytest_cache/` didn't match the real folder `.pytest_cache/`. Fixed by adding the dot.

## Step 2: Basic endpoints

**Decisions**
- Added `app/models.py` (not in the original plan) to keep the `Product` schema separate from the data.
- Money is stored as `price_paise: int`, because floats can't represent money exactly (0.1 + 0.2 != 0.3).
- `PRODUCTS` is built from a list with `{product.id: product ...}`, so a key can never mismatch its id.
- Products are stored as `Product` instances, so bad data fails at startup (fail fast).

**Broke / fixed**
- Duplicate ids silently overwrite each other in the dict (count dropped from 7 to 6). Added a startup guard that raises `ValueError`.
- Corrected understanding: a non-integer id returns 422 (validation), not 401 (authentication).
- Swagger UI validates on the client side and blocks bad requests before they're sent. To test server validation, bypass it with the browser address bar or curl.

## Step 3: Caching

**Decisions**
- Boundary rule: an entry is expired only when `now > expires_at`, so it's a HIT at exactly 30 seconds.
- Cache key = path + query string, without the host, so `localhost` and `127.0.0.1` don't split the cache.
- 404s aren't cached, and no `X-Cache` header is sent on them. This falls out of the compute -> set -> header order.
- The cache lives in the Uvicorn process's RAM: it's lost on restart and not shared between workers.

**Broke / fixed**
- Manual cache test: a typo in the key (`/prodcuts`) made every `get` miss silently, and the expired entry stayed in memory because lazy expiry never ran on it. Lesson: cache keys must come from the code, never be typed by hand.

## Step 4: Rate limiting

**Decisions**
- Window id = `int(now // 60)` (floor division).
- Storage = `client -> (window_id, count)`: one entry per client, overwritten when a new window starts.
- `check()` returns a frozen dataclass `RateLimitResult(allowed, retry_after)`.
- `retry_after` is rounded up with `math.ceil`.
- Exempt paths: `/health` (required, for load balancers) and `/docs`, `/openapi.json`, `/redoc` (convenience).
- The rate limit is per client IP across all routes, not per endpoint.
- Middleware returns `JSONResponse(429)` directly, because an `HTTPException` raised in middleware isn't handled by FastAPI and becomes a 500.
- Considered `X-RateLimit-*` headers; skipped them to stay within the assignment's scope.

**Broke / fixed**
- My first window formula (divide, subtract 1, round up) gave wrong windows at exact multiples of 60. Replaced with floor division.
- The VS Code terminal is Command Prompt, so use `cmd` syntax (`for /L`), not PowerShell's `1..11`.
- Windows started at `:07` past the minute: `time.monotonic()` counts from an arbitrary origin. Every window is still exactly 60 s, so behaviour is correct.
- Known leak: an entry for a client who never returns stays in `_clients` forever (seen in the manual test).

## Step 5: Tests

**Decisions**
- Inject the fake clock with `monkeypatch` (swap whole objects) rather than refactoring into an app factory.
- `FakeClock` class with `advance()`, shared through `tests/conftest.py`.
- `pytest.ini` sets `pythonpath = .` to fix `ModuleNotFoundError` for `app`.
- Test isolation: `monkeypatch` swaps `main.cache` and `main.rate_limiter` for fresh instances per test and restores them afterwards. Import `main` as a module, not the names inside it, or the patch won't reach them.

**Broke / fixed**
- All tests ERRORed with "fixture 'clock' not found": `FakeClock` and the `clock` fixture were lost through a placeholder comment in a partial snippet. Fixed by replacing the whole `conftest.py`. ERROR means setup failed; FAILED means an assertion failed.
- Mutation testing: `<=` -> `<` makes the limit effectively 9. Only the test asserting all of requests 1-10 return 200 caught it.
- pytest warns that Starlette's `TestClient` is moving from `httpx` to `httpx2`. It's harmless with pinned versions; revisit later.

## To do before the review

- Rewrite `TTLCache` and `FixedWindowRateLimiter` from scratch myself and run the tests against them.