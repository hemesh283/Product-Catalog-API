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
- Exempt paths: `/health` (required, for load balancers) and the docs routes (convenience).
- The rate limit is per client IP across all routes, not per endpoint.
- Middleware returns `JSONResponse(429)` directly, because an `HTTPException` raised in middleware isn't handled by FastAPI and becomes a 500.
- Considered `X-RateLimit-*` headers; skipped them to stay within the assignment's scope.

**Broke / fixed**
- My first window formula (divide, subtract 1, round up) gave wrong windows at exact multiples of 60. Replaced with floor division.
- The Windows VS Code terminal is Command Prompt, so use `cmd` syntax (`for /L`), not PowerShell's `1..11`.
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
- pytest warns that Starlette's `TestClient` is moving from `httpx` to `httpx2`. Harmless with pinned versions; revisit later.

## Parked

- Step 6 (evidence), Step 8 (mock review), and rewriting `TTLCache` and `FixedWindowRateLimiter` myself. Containerization was started first.

## Phase 1: Docker

**Decisions**
- `python:3.14-slim` base: smaller pulls and a smaller attack surface than the full image.
- Dependencies installed before code is copied, so code changes reuse the cached dependency layer.
- Split requirements: `requirements.txt` (runtime) and `requirements-dev.txt` (`-r requirements.txt` + `httpx`, `pytest`).
- Multi-stage Dockerfile: `base`, `test` (runs pytest), `runtime` (ships). Tests never enter the runtime image.
- Runtime copies only `app/` (allow-list), runs as non-root `appuser`, and has a Python-based `HEALTHCHECK` (slim has no `curl`).
- `--host 0.0.0.0`: `127.0.0.1` inside a container is unreachable through `-p`.
- One Uvicorn worker: each worker would have its own counters, loosening the limit to up to 40 per minute.
- `.dockerignore` keeps `.git`, `.venv`, `.env` out of the build context. `**/` is needed to match `__pycache__` in subfolders.
- Published `hemesh283/product-catalog-api:1.0.0` and `latest`; git tags `v1.0-assignment` (submission) and `v1.0.0` (release), merged through a pull request.

**Broke / fixed**
- Tag typo (`cataog-api-test`) made `docker run catalog-api:test` try to pull from Docker Hub ("pull access denied"). Image names must match exactly; fixed with `docker tag` and `docker rmi` (which only untags).
- `python:3.14-slim` floats to the latest patch (3.14.10 in the image vs 3.14.7 locally). Pin a full tag or a digest for exact reproducibility.
- Behind Docker's port mapping, every outside client appeared as `172.17.0.1`, so the rate limiter treated all users as one client.

## Phase 2: Frontend, nginx and Compose

**Decisions**
- Product routes moved under `/api` with an `APIRouter` (breaking change, so the release is 2.0.0). Swagger moved to `/api/docs`. A test checks that the old `/products` path returns 404.
- `/health` stays at the root as an infrastructure endpoint and is not routed through nginx.
- The API port is not published; nginx is the only entry point.
- nginx overwrites `X-Forwarded-For` with `$remote_addr` (edge proxy). Uvicorn trusts forwarded headers from any IP (`*`), which is safe only because the API is unreachable except through nginx.
- `proxy_pass http://api:8000;` has no trailing slash, so the `/api` prefix is passed through unchanged.
- `server_tokens off` hides the nginx version.
- Compose: `web` waits for `api` to be healthy; images named `...:${TAG:-dev}` for release builds.
- `compose.override.yaml` adds read-only bind mounts of `frontend/` and `default.conf` for development; `-f compose.yaml` runs production mode with only the copied files.
- nginx pinned to `1.30.6-alpine`.
- Images AI-generated, renamed to lowercase without spaces, converted to 600 px WebP inside a throwaway Alpine container (15 MB -> 160 KB). Originals kept outside the repo.
- Frontend: plain HTML/CSS/JS, `textContent` for API data (XSS safety), hash routing with real links (Back button works), `X-Cache` badge (readable because same origin), `RateLimitError` with a `Retry-After` countdown, sequential 11-request demo.

**Broke / fixed / learned**
- `nginx -t` in a standalone container failed with `host not found in upstream "api"`: nginx resolves `proxy_pass` hosts at startup. This is why `depends_on: service_healthy` matters.
- Proxy headers verified: the API logs the gateway IP `172.18.0.1`, not nginx's container IP `172.18.0.3`. The `:0` port appears because `X-Forwarded-For` carries no port.
- Only requests that reach the API count toward the rate limit; static files and nginx 404s don't.
- `earbuds.png.png`: Windows Explorer hides extensions. Turned on "File name extensions".
- `nginx -v` in WSL said "not found": nginx lives inside the image, not on the laptop. Use `docker compose exec web nginx -v`.
- `docker compose config` without `-f` always shows the merged files, even while production mode is running.
- The API has no bind mount, so Python changes need `docker compose up -d --build`.
- MISS was 15-20 ms slower than HIT mostly because MISSes follow idle pauses (cold CPU and network), not because of the cache work, which is a microsecond dict lookup.
- The badge's time stops when headers arrive; DevTools' "Time" includes the body download, so they differ slightly.
- 11 requests passed before a 429 once while clicking slowly: a window boundary passed mid-sequence (the fixed-window edge effect).
