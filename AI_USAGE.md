# AI Usage

This project was built as a learning exercise with AI assistance, as the assignment requires. My approach: I asked the AI to act as a mentor that explains concepts and lays out options, while I made every design decision, ran every command, and verified every behaviour myself.

## Tools used

| Tool | How it was used |
| --- | --- |
| Claude (Anthropic) | Mentor: explained concepts, compared options for each decision, wrote code with line-by-line explanations, reviewed my code, test output and terminal logs |
| GitHub Copilot | Research while investigating why rate-limit windows started at `:07` past the minute |
| ChatGPT | Generated the seven product images |
| YouTube tutorial | Background on nginx and Docker Compose, compared against my own configuration |

## Ground rules I set

- One small step at a time; no files created or commands run until I said so.
- For each step: explain the concept, ask me how I would design it, correct me, then build.
- I run all git and Docker commands myself; no AI attribution in commits.
- After each step: check questions I had to answer before moving on.
- When something felt too complex, I stopped and asked for simpler explanations and analogies before continuing.

## Assignment steps

### Step 1: Project setup

I asked Claude to explain environment setup options instead of choosing for me. It explained venv vs other tools, explicit vs bundled dependencies, three ways to pin versions, and two ways to create the GitHub repo. I chose explicit packages, top-level pinning and an empty remote connected locally. I wrote `requirements.txt` and `.gitignore` myself. Claude's review caught a missing dot in `.pytest_cache/`, and I verified with `git status` that `.venv` was ignored.

### Step 2: Basic endpoints

I asked Claude to explain FastAPI routing using Spring Boot comparisons and to give options for each design decision. I chose a separate `models.py`, prices as integer paise, and `Product` instances in a dict for fail-fast validation. Claude wrote the endpoint and model code with line-by-line explanations. I tested validation by breaking the data on purpose, found the silent duplicate-id overwrite through my own experiment, and wrote the duplicate-id guard myself.

### Step 3: Caching

I designed the cache behaviour with Claude: `expires_at` storage, a monotonic injectable clock, lazy expiration, HIT at exactly 30 seconds, no negative caching, and keys built from path + query. I had never implemented a cache, so I asked Claude to write `TTLCache` and explain it line by line, then verified it by hand with a fake clock. That test caught a key typo of mine that caused silent misses. Claude wrote the cache-aside wiring, and I verified MISS -> HIT -> MISS with curl and browser DevTools.

### Step 4: Rate limiting

I designed the limiter with Claude: floor division for window ids, `client -> (window, count)` storage so old windows overwrite themselves, a result class carrying `retry_after`, rounding `retry_after` up, and exempting `/health` and the docs routes. I asked Claude to write `FixedWindowRateLimiter` and the middleware with explanations. I verified the limiter by hand with a fake clock, then confirmed ten 200s and a 429 with curl and Swagger, and that `/health` stays available. I used GitHub Copilot to research why windows started at `:07` past the minute.

### Step 5: Tests

I chose to inject the fake clock with `monkeypatch` instead of refactoring into an app factory, after Claude compared the two. Claude wrote the fixtures and tests with explanations. A missing-fixture error taught me the difference between ERROR and FAILED. I used mutation testing (`>` to `>=`, `ceil` to `int`, `<=` to `<`) to prove each boundary test catches the bug it targets.

### Documentation

I chose a Mermaid diagram, detailed caching and rate-limiting explanations, and a known-limitations section. Claude drafted the README, AI_USAGE.md and NOTES.md from my saved step notes; I reviewed each section and merged in my own notes.

## Phase 1: Docker

- **Design:** I chose a slim base image, cache-friendly layer order, split requirements, an allow-list `COPY` of `app/`, a non-root user, tests in a container, and a Python-based healthcheck. Claude corrected two of my predictions: `127.0.0.1` inside a container isn't reachable through `-p`, and multiple workers would *loosen* the rate limit because each process keeps its own counters. Claude proposed the multi-stage build to reconcile "tests out of the image" with "tests run in a container."
- **Dockerfile:** Claude wrote it with explanations. I built and ran both targets. My tag typo taught me how image names and tags work. I verified 31 tests pass on Linux, the container reports healthy, runs as `appuser`, and contains only `app/`. The logs showed every outside request arriving from `172.17.0.1`.
- **Publishing:** Claude explained registries, image naming, access tokens, semantic versioning and version tags vs `latest`. I created the Docker Hub account and token myself, pushed `1.0.0` and `latest`, verified the published image with `--pull always` (same digest as my local image), merged through a pull request, and tagged `v1.0.0`.

## Phase 2: Frontend, nginx and Compose

- **API changes:** I chose an `/api` prefix in FastAPI (a breaking change, so version 2.0.0), keeping `/health` at the root and unpublished. Claude wrote the router change and pointed out the `X-Forwarded-For` spoofing trap (overwrite, never append, at the edge). I updated the tests and added one proving the old path returns 404.
- **nginx and Compose:** Claude wrote `default.conf`, the nginx Dockerfile, `compose.yaml` and `compose.override.yaml` with explanations. I ran `nginx -t` alone first and saw why startup order matters, then verified the whole stack: health-based startup, MISS/HIT through nginx, `/health` hidden, the API unreachable on 8000, and the API logging the forwarded gateway IP rather than nginx's own. When the setup felt too complex for a first attempt, I asked Claude to strip it back to the core and explain bind mounts, the two Compose files and the nginx defaults with analogies, and I proved each with experiments.
- **Images:** I generated them with ChatGPT. Following Claude's guidance I renamed them (catching a hidden `.png.png`), and converted them to WebP inside a throwaway Docker container (15 MB to 160 KB) after my WSL password blocked installing ImageMagick.
- **Frontend:** Claude wrote `index.html`, `styles.css` and `app.js` step by step (grid, hash-routed detail view, cache badge, rate-limit countdown, demo button). I tested each step in the browser and DevTools, checked `ETag`/`304` behaviour with curl, investigated why MISS looked slower than HIT, and why the badge time differs from DevTools. I plan to study `app.js` line by line separately.

## What the AI wrote vs what I wrote

| Written by me | Written by Claude at my request, then reviewed and tested by me |
| --- | --- |
| `requirements.txt` and `.gitignore`, the duplicate-id guard in `data.py`, `image_url` updates in `data.py`, image renaming and conversion | `models.py`, `data.py`, `main.py`, `cache.py`, `rate_limiter.py`, `pytest.ini`, all test files, `Dockerfile`, `nginx/`, Compose files, `frontend/` code |

Product images were generated with ChatGPT.


## How I verified everything

- Ran every endpoint manually through Swagger, curl and the browser, both directly and through nginx.
- Tested `TTLCache` and the limiter by hand with a fake clock before wiring them in.
- Broke code on purpose (negative price, duplicate id, boundary mutations, standalone `nginx -t`) to confirm guards and tests catch problems.
- Ran the full suite locally and inside a Linux container: 32 passed.
- Checked container users, contents, health status, logs and published-image digests.