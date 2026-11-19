const statusEl = document.getElementById("status");
const metaEl = document.getElementById("meta");
const viewEl = document.getElementById("view");

const priceFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

let countdownTimer = null;

class RateLimitError extends Error {
  constructor(retryAfter, limit, windowSeconds) {
    super("Too many requests");
    this.retryAfter = retryAfter;
    this.limit = limit;
    this.windowSeconds = windowSeconds;
  }
}

function formatPrice(paise) {
  return priceFormatter.format(paise / 100);
}

async function fetchJson(url) {
  const started = performance.now();
  const response = await fetch(url);
  const elapsedMs = Math.round(performance.now() - started);

  if (response.status === 429) {
    const body = await response.json().catch(() => ({}));
    const retryAfter = Number(response.headers.get("Retry-After")) || 60;
    throw new RateLimitError(retryAfter, body.limit, body.window_seconds);
  }

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const data = await response.json();
  return { data, cache: response.headers.get("X-Cache"), elapsedMs };
}

function renderMeta({ cache, elapsedMs }) {
  metaEl.replaceChildren();
  if (!cache) {
    return;
  }
  const badge = document.createElement("span");
  badge.className = cache === "HIT" ? "badge hit" : "badge miss";
  badge.textContent = `Cache ${cache}`;
  metaEl.append(badge, `${elapsedMs} ms`);
}

function showRateLimit(error) {
  let remaining = error.retryAfter;

  const box = document.createElement("div");
  box.className = "notice";

  const title = document.createElement("strong");
  title.textContent = "You're browsing a little too fast.";

  const text = document.createElement("p");

  box.append(title, text);
  viewEl.replaceChildren(box);
  statusEl.textContent = "";

  const limitText = error.limit
    ? `This catalog allows ${error.limit} requests every ${error.windowSeconds} seconds. `
    : "";

  function update() {
    text.textContent = `${limitText}Loading again in ${remaining} s…`;
  }

  update();
  countdownTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(countdownTimer);
      countdownTimer = null;
      router();
      return;
    }
    update();
  }, 1000);
}

function createImage(product) {
  const img = document.createElement("img");
  img.src = product.image_url;
  img.alt = product.name;
  img.loading = "lazy";
  return img;
}

function renderGrid(products) {
  const grid = document.createElement("div");
  grid.className = "grid";

  for (const product of products) {
    const card = document.createElement("a");
    card.className = "card";
    card.href = `#/products/${product.id}`;

    const body = document.createElement("div");
    body.className = "card-body";

    const name = document.createElement("h2");
    name.textContent = product.name;

    const price = document.createElement("p");
    price.className = "price";
    price.textContent = formatPrice(product.price_paise);

    body.append(name, price);
    card.append(createImage(product), body);
    grid.append(card);
  }

  viewEl.replaceChildren(grid);
}

function renderDetail(product) {
  const back = document.createElement("a");
  back.href = "#/";
  back.className = "back";
  back.textContent = "← All products";

  const detail = document.createElement("article");
  detail.className = "detail";

  const info = document.createElement("div");
  info.className = "detail-info";

  const name = document.createElement("h2");
  name.textContent = product.name;

  const price = document.createElement("p");
  price.className = "price";
  price.textContent = formatPrice(product.price_paise);

  const description = document.createElement("p");
  description.textContent = product.description;

  info.append(name, price, description);
  detail.append(createImage(product), info);
  viewEl.replaceChildren(back, detail);
}

async function router() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }

  const match = location.hash.match(/^#\/products\/(\d+)$/);
  statusEl.textContent = "Loading…";
  metaEl.replaceChildren();
  viewEl.replaceChildren();

  try {
    if (match) {
      const result = await fetchJson(`/api/products/${match[1]}`);
      renderDetail(result.data);
      renderMeta(result);
    } else {
      const result = await fetchJson("/api/products");
      renderGrid(result.data);
      renderMeta(result);
    }
    statusEl.textContent = "";
  } catch (error) {
    if (error instanceof RateLimitError) {
      showRateLimit(error);
    } else {
      statusEl.textContent = `Could not load: ${error.message}`;
    }
  }
}

window.addEventListener("hashchange", router);
router();

const demoButton = document.getElementById("demo-button");
const demoResults = document.getElementById("demo-results");

async function runRateLimitDemo() {
  demoButton.disabled = true;
  demoResults.replaceChildren();

  for (let i = 1; i <= 11; i++) {
    const item = document.createElement("li");
    try {
      const response = await fetch("/api/products");
      if (response.ok) {
        item.className = "ok";
        item.textContent = `${i}: ${response.status}`;
      } else {
        const retryAfter = response.headers.get("Retry-After");
        item.className = "blocked";
        item.textContent = retryAfter
          ? `${i}: ${response.status} (retry in ${retryAfter} s)`
          : `${i}: ${response.status}`;
      }
    } catch (error) {
      item.className = "blocked";
      item.textContent = `${i}: network error`;
    }
    demoResults.append(item);
  }

  demoButton.disabled = false;
}

demoButton.addEventListener("click", runRateLimitDemo);