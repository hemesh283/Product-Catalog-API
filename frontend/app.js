const statusEl = document.getElementById("status");
const gridEl = document.getElementById("grid");

const priceFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

function formatPrice(paise) {
  return priceFormatter.format(paise / 100);
}

function renderProducts(products) {
  gridEl.innerHTML = "";
  for (const product of products) {
    const card = document.createElement("article");
    card.className = "card";

    const img = document.createElement("img");
    img.src = product.image_url;
    img.alt = product.name;
    img.loading = "lazy";

    const body = document.createElement("div");
    body.className = "card-body";

    const name = document.createElement("h2");
    name.textContent = product.name;

    const price = document.createElement("p");
    price.className = "price";
    price.textContent = formatPrice(product.price_paise);

    body.append(name, price);
    card.append(img, body);
    gridEl.append(card);
  }
}

async function loadProducts() {
  try {
    const response = await fetch("/api/products");
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const products = await response.json();
    renderProducts(products);
    statusEl.textContent = "";
  } catch (error) {
    statusEl.textContent = `Could not load products: ${error.message}`;
  }
}

loadProducts();