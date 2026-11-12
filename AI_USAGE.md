# AI Usage

This project was built as a learning exercise with AI assistance, as the assignment requires. My approach: I asked the AI to act as a mentor that explains concepts and lays out options, while I made every design decision, ran every command, and verified every behaviour myself.

## Tools used

| Tool | How it was used |
| --- | --- |
| Claude (Anthropic) | Mentor: explained concepts, compared options for each decision, wrote code with line-by-line explanations, reviewed my code and test output |


## Ground rules I set

- One small step at a time; no files created or commands run until I said so.
- For each step: explain the concept, ask me how I would design it, correct me, then build.
- I run all git commands myself; no AI attribution in commits.
- After each step: check questions I had to answer before moving on.

## Step by step

### Step 1: Project setup

I asked Claude to explain environment setup options instead of choosing for me. It explained venv vs other tools, explicit vs bundled dependencies, three ways to pin versions, and two ways to create the GitHub repo. I chose explicit packages, top-level pinning and an empty remote connected locally (Path A). I wrote `requirements.txt` and `.gitignore` myself. Claude's review caught a missing dot in `.pytest_cache/`, and I verified with `git status` that `.venv` was ignored.

### Step 2: Basic endpoints

I asked Claude to explain FastAPI routing using Spring Boot comparisons and to give options for each design decision. I chose a separate `models.py`, prices as integer paise, and `Product` instances in a dict for fail-fast validation. Claude wrote the endpoint and model code with line-by-line explanations. I tested validation by breaking the data on purpose, found the silent duplicate-id overwrite through my own experiment, and wrote the duplicate-id guard myself.

### Step 3: Caching

I designed the cache behaviour with Claude: `expires_at` storage, a monotonic injectable clock, lazy expiration, HIT at exactly 30 seconds, no negative caching, and keys built from path + query. I had never implemented a cache, so I asked Claude to write `TTLCache` and explain it line by line, then verified it by hand with a fake clock. That test caught a key typo of mine that caused silent misses. Claude wrote the cache-aside wiring, and I verified MISS -> HIT -> MISS with curl and browser DevTools.

### Step 4: Rate limiting

I designed the limiter with Claude: floor division for window ids, `client -> (window, count)` storage so old windows overwrite themselves, a result class carrying `retry_after`, rounding `retry_after` up, and exempting `/health` and the docs routes. I asked Claude to write `FixedWindowRateLimiter` and the middleware with explanations. I verified the limiter by hand with a fake clock, then confirmed ten 200s and a 429 with curl and Swagger, and that `/health` stays available. I used GitHub Copilot to research why windows started at `:07` past the minute (the monotonic clock's arbitrary origin).

### Step 5: Tests

I chose to inject the fake clock with `monkeypatch` instead of refactoring into an app factory, after Claude compared the two. Claude wrote the fixtures and tests with explanations. A missing-fixture error taught me the difference between ERROR (setup failed) and FAILED (assertion failed). I used mutation testing (`>` to `>=`, `ceil` to `int`, `<=` to `<`) to prove each boundary test catches the bug it targets. That showed me an off-by-one limiter blocks too early, and only a test asserting requests 1-10 succeed catches it.

## What the AI wrote vs what I wrote

| Written by me | Written by Claude at my request, then reviewed and tested by me |
| --- | --- |
| `requirements.txt`, `.gitignore`, the duplicate-id guard in `data.py` | `models.py`, `data.py`, `main.py`, `cache.py`, `rate_limiter.py`, `pytest.ini`, all test files |


## How I verified everything

- Ran every endpoint manually in Swagger, the browser and curl.
- Tested `TTLCache` and the limiter by hand in the Python REPL with a fake clock before wiring them in.
- Broke code on purpose (negative price, duplicate id, boundary mutations) to confirm guards and tests catch it.
- Ran the full test suite: 31 passed.