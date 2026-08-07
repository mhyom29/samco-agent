/* ======================================================================
   EDIT PRODUCTS HERE. Every product below has a real image — either an
   actual SAMCO store photo or a stock photo, never an icon placeholder.
   If you add a product, add a real `photo` too or it won't render well.
   ====================================================================== */

// ⚠️ SET THIS to your bot's @username (from BotFather) before shipping —
// this is what "Checkout on Telegram" opens.
const TELEGRAM_BOT_USERNAME = "samcobot";

const PRODUCTS = [
  // Furniture
  { name: "Plastic Chairs (set of 4)", unit: "set of 4", price: 18000, category: "furniture",
    photo: "https://images.unsplash.com/photo-1613906800797-d5d4fb2f7bbb?w=500&q=70&fit=crop&auto=format" },
  { name: "Executive Office Chair", unit: "1 unit, leather", price: 45000, category: "furniture",
    photo: "https://images.unsplash.com/photo-1580087433295-ab2600c1030e?w=500&q=70&fit=crop&auto=format" },
  { name: "Dining Set (4-seater)", unit: "table + 4 chairs", price: 150000, category: "furniture",
    photo: "https://images.unsplash.com/photo-1613906800797-d5d4fb2f7bbb?w=500&q=70&fit=crop&auto=format" },
  { name: "Round Sofa Set", unit: "3-piece lounge set", price: 320000, category: "furniture",
    photo: "assets/sofa.jpg" },

  // Electronics
  { name: "LED Smart TV", unit: "32-inch", price: 95000, category: "electronics",
    photo: "https://images.unsplash.com/photo-1601944177325-f8867652837f?w=500&q=70&fit=crop&auto=format" },
  { name: "BARDEFU Commercial Blender", unit: "1 unit, heavy duty", price: 42000, category: "electronics",
    photo: "assets/blender.jpg" },
  { name: "SUPER Rechargeable Fan", unit: "1 unit, foldable", price: 15500, category: "electronics",
    photo: "assets/fan.jpg" },
  { name: "Electric Scooter", unit: "1 unit, rechargeable", price: 420000, category: "electronics",
    photo: "assets/scooter.jpg" },

  // Groceries
  { name: "Wala Rice Pro", unit: "50kg bag", price: 78000, category: "groceries",
    photo: "https://images.unsplash.com/photo-1644377949116-c4a6b529241c?w=500&q=70&fit=crop&auto=format" },
  { name: "Stallion Rice", unit: "25kg bag", price: 42000, category: "groceries",
    photo: "https://images.unsplash.com/photo-1644377949116-c4a6b529241c?w=500&q=70&fit=crop&auto=format" },
  { name: "Optimum Rice", unit: "10kg bag", price: 18500, category: "groceries",
    photo: "https://images.unsplash.com/photo-1644377949116-c4a6b529241c?w=500&q=70&fit=crop&auto=format" },
  { name: "Vegetable Oil", unit: "5 litres", price: 12500, category: "groceries",
    photo: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500&q=70&fit=crop&auto=format" },
  { name: "Spaghetti (carton)", unit: "20 packs", price: 15800, category: "groceries",
    photo: "https://images.unsplash.com/photo-1737718952107-be42ec98a028?w=500&q=70&fit=crop&auto=format" },

  // Beauty & Personal Care
  { name: "Body Lotion", unit: "400ml", price: 4200, category: "beauty",
    photo: "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&q=70&fit=crop&auto=format" },
  { name: "Roll-on Deodorant", unit: "50ml", price: 2200, category: "beauty",
    photo: "https://images.unsplash.com/photo-1580870069867-74c57ee1bb07?w=500&q=70&fit=crop&auto=format" },
  { name: "Toothpaste", unit: "1 tube", price: 2100, category: "beauty",
    photo: "https://images.unsplash.com/photo-1711779187508-a8fac1c18be9?w=500&q=70&fit=crop&auto=format" },
  { name: "Bathing Soap", unit: "1 bar", price: 1500, category: "beauty",
    photo: "https://images.unsplash.com/photo-1572527226808-051d3c05e7a1?w=500&q=70&fit=crop&auto=format" },

  // Baby & Household
  { name: "Huggies Diapers", unit: "size 4, jumbo pack", price: 9800, category: "baby",
    photo: "assets/huggies.jpg" },
  { name: "Baby Wipes", unit: "pack of 3", price: 3400, category: "baby",
    photo: "assets/wipes.jpg" },
  { name: "Toilet Tissue", unit: "pack of 12 rolls", price: 4300, category: "baby",
    photo: "https://images.unsplash.com/photo-1674656801311-2442717f7968?w=500&q=70&fit=crop&auto=format" },
  { name: "Vacuum Flask (Thermal Jug)", unit: "1 litre", price: 8500, category: "baby",
    photo: "assets/flask.jpg" },
];

const CATEGORY_META = {
  furniture:   { label: "Furniture",              page: "furniture.html",   tag: "Chairs · tables · sofas" },
  electronics: { label: "Electronics",             page: "electronics.html", tag: "TVs · fans · appliances" },
  groceries:   { label: "Groceries",               page: "groceries.html",   tag: "Rice · oil · pasta" },
  beauty:      { label: "Beauty & Personal Care",  page: "beauty.html",      tag: "Skincare · daily care" },
  baby:        { label: "Baby & Household",        page: "baby.html",        tag: "Diapers · wipes · home" },
};
const CATEGORY_ORDER = ["furniture", "electronics", "groceries", "beauty", "baby"];

function nairaFmt(n){ return "₦" + n.toLocaleString("en-NG"); }

/* ---------------- CART (persists across pages via localStorage) ---------------- */
const CART_KEY = "samco_cart_v1";

function getCart(){
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || {};
  } catch(e) { return {}; }
}
function saveCart(cart){
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
}
function addToCart(name, qty){
  const cart = getCart();
  cart[name] = (cart[name] || 0) + qty;
  saveCart(cart);
}
function setCartQty(name, qty){
  const cart = getCart();
  if (qty <= 0) delete cart[name];
  else cart[name] = qty;
  saveCart(cart);
  renderCartDrawer();
}
function cartCount(){
  return Object.values(getCart()).reduce((a,b) => a+b, 0);
}
function cartTotal(){
  const cart = getCart();
  let total = 0;
  for (const name in cart){
    const p = PRODUCTS.find(p => p.name === name);
    if (p) total += p.price * cart[name];
  }
  return total;
}
function updateCartBadge(){
  const badge = document.getElementById("cartBadge");
  if (!badge) return;
  const count = cartCount();
  badge.textContent = count;
  badge.style.display = count > 0 ? "flex" : "none";
}

function renderCartDrawer(){
  const list = document.getElementById("cartItemsList");
  const totalEl = document.getElementById("cartTotalAmount");
  const emptyEl = document.getElementById("cartEmptyMsg");
  if (!list) return;

  const cart = getCart();
  const entries = Object.entries(cart);

  if (entries.length === 0){
    list.innerHTML = "";
    if (emptyEl) emptyEl.style.display = "block";
    if (totalEl) totalEl.textContent = nairaFmt(0);
    return;
  }
  if (emptyEl) emptyEl.style.display = "none";

  list.innerHTML = entries.map(([name, qty]) => {
    const p = PRODUCTS.find(p => p.name === name);
    if (!p) return "";
    return `
      <div class="cart-row">
        <img src="${p.photo}" alt="${p.name}" class="cart-row-thumb">
        <div class="cart-row-info">
          <div class="cart-row-name">${p.name}</div>
          <div class="cart-row-price">${nairaFmt(p.price)} each</div>
        </div>
        <div class="cart-row-qty">
          <button onclick="setCartQty('${name.replace(/'/g,"\\'")}', ${qty - 1})">−</button>
          <span>${qty}</span>
          <button onclick="setCartQty('${name.replace(/'/g,"\\'")}', ${qty + 1})">+</button>
        </div>
      </div>`;
  }).join("");

  if (totalEl) totalEl.textContent = nairaFmt(cartTotal());
}

function buildOrderText(){
  const cart = getCart();
  const lines = ["Hi SAMCO Superstore! I'd like to order:", ""];
  for (const name in cart){
    const p = PRODUCTS.find(p => p.name === name);
    if (!p) continue;
    lines.push(`• ${p.name} (${p.unit}) x${cart[name]} — ${nairaFmt(p.price * cart[name])}`);
  }
  lines.push("", `Total: ${nairaFmt(cartTotal())}`, "", "Is everything available?");
  return lines.join("\n");
}

function telegramLink(){
  return `https://t.me/${TELEGRAM_BOT_USERNAME}`;
}

async function checkoutOnTelegram(){
  const text = buildOrderText();
  try {
    await navigator.clipboard.writeText(text);
    alert("Order copied! Paste it into the Telegram chat that's about to open.");
  } catch(e) {
    alert("Couldn't auto-copy — here's your order, copy it manually:\n\n" + text);
  }
  window.open(telegramLink(), "_blank");
}

function openCartDrawer(){
  renderCartDrawer();
  document.getElementById("cartDrawer").classList.add("open");
  document.getElementById("cartOverlay").classList.add("open");
}
function closeCartDrawer(){
  document.getElementById("cartDrawer").classList.remove("open");
  document.getElementById("cartOverlay").classList.remove("open");
}

/* ---------------- PRODUCT CARDS ---------------- */
function productCardHTML(p, showCategoryPill){
  const pill = showCategoryPill && CATEGORY_META[p.category]
    ? `<span class="cat-pill">${CATEGORY_META[p.category].label}</span>`
    : "";
  const safeName = p.name.replace(/'/g, "\\'");
  return `
    <div class="prod-card">
      ${pill}
      <div class="prod-thumb"><img src="${p.photo}" alt="${p.name}" loading="lazy"></div>
      <div class="prod-name">${p.name}</div>
      <div class="prod-unit">${p.unit}</div>
      <div class="prod-bottom">
        <div class="prod-price"><span class="naira">${nairaFmt(p.price)}</span></div>
      </div>
      <div class="qty-row">
        <div class="qty-stepper" data-product="${safeName}">
          <button class="qty-btn" data-action="dec">−</button>
          <span class="qty-val">1</span>
          <button class="qty-btn" data-action="inc">+</button>
        </div>
        <button class="add-btn" data-product="${safeName}">Add to cart</button>
      </div>
    </div>`;
}

function wireProductCardControls(container){
  container.querySelectorAll(".qty-stepper").forEach(stepper => {
    const valEl = stepper.querySelector(".qty-val");
    stepper.querySelectorAll(".qty-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        let v = parseInt(valEl.textContent, 10);
        v = btn.dataset.action === "inc" ? v + 1 : Math.max(1, v - 1);
        valEl.textContent = v;
      });
    });
  });
  container.querySelectorAll(".add-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.product;
      const stepper = container.querySelector(`.qty-stepper[data-product="${CSS.escape(name)}"]`);
      const qty = stepper ? parseInt(stepper.querySelector(".qty-val").textContent, 10) : 1;
      addToCart(name, qty);
      const original = btn.textContent;
      btn.textContent = "Added ✓";
      setTimeout(() => { btn.textContent = original; }, 1200);
    });
  });
}

function renderGrid(gridEl, noResultsEl, countEl, products, showCategoryPill){
  gridEl.innerHTML = products.map(p => productCardHTML(p, showCategoryPill)).join("");
  wireProductCardControls(gridEl);
  if (noResultsEl) noResultsEl.style.display = products.length === 0 ? "block" : "none";
  if (countEl) countEl.textContent = `${products.length} product${products.length === 1 ? "" : "s"}`;
}

function renderCategoryStrip(el){
  el.innerHTML = CATEGORY_ORDER.map(key => {
    const meta = CATEGORY_META[key];
    const sample = PRODUCTS.find(p => p.category === key);
    return `<a class="cat-chip" href="${meta.page}"><img class="thumb" src="${sample.photo}" alt="${meta.label}"><span>${meta.label}</span></a>`;
  }).join("");
}

function wireGenericTelegram(){
  document.querySelectorAll(".tg-generic, #navTgBtn").forEach(el => { el.href = telegramLink(); });
}

function wireMobileNav(){
  const burger = document.querySelector(".burger");
  const navLinksEl = document.getElementById("navLinks");
  if (!burger || !navLinksEl) return;
  burger.addEventListener("click", () => navLinksEl.classList.toggle("open"));
  navLinksEl.querySelectorAll("a").forEach(a => a.addEventListener("click", () => navLinksEl.classList.remove("open")));
}

function wireHeroSearch(){
  const form = document.getElementById("heroSearchForm");
  if (!form) return;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = document.getElementById("heroSearchInput").value.trim();
    window.location.href = `index.html?q=${encodeURIComponent(q)}`;
  });
}

function wireCartUI(){
  const cartBtn = document.getElementById("cartFloatBtn");
  const closeBtn = document.getElementById("cartCloseBtn");
  const overlay = document.getElementById("cartOverlay");
  const checkoutBtn = document.getElementById("cartCheckoutBtn");
  if (cartBtn) cartBtn.addEventListener("click", openCartDrawer);
  if (closeBtn) closeBtn.addEventListener("click", closeCartDrawer);
  if (overlay) overlay.addEventListener("click", closeCartDrawer);
  if (checkoutBtn) checkoutBtn.addEventListener("click", checkoutOnTelegram);
  updateCartBadge();
}

document.addEventListener("DOMContentLoaded", () => {
  wireGenericTelegram();
  wireMobileNav();
  wireHeroSearch();
  wireCartUI();
  document.getElementById("year") && (document.getElementById("year").textContent = new Date().getFullYear());
});
