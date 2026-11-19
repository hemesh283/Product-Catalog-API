const statusEl = document.getElementById("status");
const viewEl = document.getElementById("view");

const priceFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

function formatPrice(paise) {
  return priceFormatter.format(paise / 100);
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
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
  const match = location.hash.match(/^#\/products\/(\d+)$/);
  statusEl.textContent = "Loading…";
  viewEl.replaceChildren();

  try {
    if (match) {
      const product = await fetchJson(`/api/products/${match[1]}`);
      renderDetail(product);
    } else {
      const products = await fetchJson("/api/products");
      renderGrid(products);
    }
    statusEl.textContent = "";
  } catch (error) {
    statusEl.textContent = `Could not load: ${error.message}`;
  }
}

window.addEventListener("hashchange", router);
router();