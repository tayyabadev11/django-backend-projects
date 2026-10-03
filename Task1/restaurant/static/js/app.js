(function () {
  "use strict";

  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const $ = (id) => document.getElementById(id);
  const money = (n) => "Rs. " + Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });

  function el(tag, attrs, ...kids) {
    const node = document.createElement(tag);
    for (const [key, val] of Object.entries(attrs || {})) {
      if (key === "class") node.className = val;
      else if (key.startsWith("on")) node.addEventListener(key.slice(2), val);
      else node.setAttribute(key, val);
    }
    for (const kid of kids.flat()) {
      if (kid === null || kid === undefined) continue;
      node.append(kid.nodeType ? kid : document.createTextNode(kid));
    }
    return node;
  }

  async function api(url, options = {}) {
    const res = await fetch(url, {
      method: options.method || "GET",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: options.body ? JSON.stringify(options.body) : undefined,
      credentials: "same-origin",
    });
    let data = {};
    try { data = await res.json(); } catch (e) { /* empty body */ }
    if (!res.ok) throw new Error(data.error || "Something went wrong. Please try again.");
    return data;
  }

  function say(node, text, kind) {
    node.textContent = text;
    node.className = "msg" + (kind ? " is-" + kind : "");
  }

  /* ---------------- tabs ---------------- */
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("is-active", t === tab));
      document.querySelectorAll(".panel").forEach((p) =>
        p.classList.toggle("is-active", p.id === "tab-" + tab.dataset.tab));
    });
  });

  /* links elsewhere on the page that open a tab (hero button, footer links) */
  function openTab(name) {
    const tab = document.querySelector('.tab[data-tab="' + name + '"]');
    if (!tab) return false;
    tab.click();
    window.scrollTo({ top: 0, behavior: "smooth" });
    return true;
  }
  document.querySelectorAll("[data-goto]").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (openTab(el.dataset.goto)) e.preventDefault();
    });
  });
  if (location.hash === "#reserve") openTab("reserve");

  /* ---------------- menu ---------------- */
  let categories = [];
  let activeCategory = "all";
  const cart = new Map(); // dish id -> { dish, qty }

  async function loadMenu() {
    try {
      const data = await api("/api/menu/");
      categories = data.categories;
      renderFilters();
      renderMenu();
    } catch (err) {
      $("menu-grid").replaceChildren(el("p", { class: "msg is-error" }, err.message));
    }
  }

  function renderFilters() {
    const make = (key, label) =>
      el("button", {
        type: "button",
        class: "chip" + (activeCategory === key ? " is-active" : ""),
        onclick: () => { activeCategory = key; renderFilters(); renderMenu(); },
      }, label);
    $("filters").replaceChildren(
      make("all", "All dishes"),
      ...categories.map((c) => make(c.key, c.label))
    );
  }

  function renderMenu() {
    const dishes = categories
      .filter((c) => activeCategory === "all" || c.key === activeCategory)
      .flatMap((c) => c.items);
    $("menu-grid").replaceChildren(...dishes.map(dishCard));
  }

  function dishCard(dish) {
    const action = dish.in_stock
      ? el("button", { type: "button", class: "btn btn-small", onclick: () => addToCart(dish) }, "Add")
      : el("span", { class: "sold-out" }, "sold out today");
    return el("article", { class: "dish" + (dish.in_stock ? "" : " is-out") },
      dish.image ? el("img", { src: dish.image, alt: dish.name, loading: "lazy" }) : null,
      el("div", { class: "dish-body" },
        el("h3", {}, dish.name),
        el("p", {}, dish.description),
        el("div", { class: "dish-foot" }, el("span", { class: "price" }, money(dish.price)), action)
      )
    );
  }

  /* ---------------- cart ---------------- */
  function addToCart(dish) {
    const line = cart.get(dish.id) || { dish, qty: 0 };
    line.qty = Math.min(line.qty + 1, 20);
    cart.set(dish.id, line);
    renderCart();
  }

  function changeQty(id, delta) {
    const line = cart.get(id);
    if (!line) return;
    line.qty += delta;
    if (line.qty <= 0) cart.delete(id);
    else line.qty = Math.min(line.qty, 20);
    renderCart();
  }

  function renderCart() {
    const box = $("cart-lines");
    if (cart.size === 0) {
      box.replaceChildren(el("p", { class: "muted" }, "Nothing here yet. Add a dish from the menu."));
    } else {
      box.replaceChildren(...[...cart.values()].map(({ dish, qty }) =>
        el("div", { class: "cart-line" },
          el("strong", {}, dish.name),
          el("span", { class: "line-price" }, money(dish.price * qty)),
          el("span", { class: "qty" },
            el("button", { type: "button", "aria-label": "Remove one " + dish.name, onclick: () => changeQty(dish.id, -1) }, "-"),
            el("span", {}, String(qty)),
            el("button", { type: "button", "aria-label": "Add one " + dish.name, onclick: () => changeQty(dish.id, 1) }, "+")
          )
        )));
    }
    const total = [...cart.values()].reduce((sum, l) => sum + l.dish.price * l.qty, 0);
    $("cart-total").textContent = money(total);
  }

  $("place-order").addEventListener("click", async () => {
    const msg = $("order-msg");
    if (cart.size === 0) return say(msg, "Add at least one dish before ordering.", "error");
    const button = $("place-order");
    button.disabled = true;
    try {
      const order = await api("/api/orders/", {
        method: "POST",
        body: {
          customer_name: $("cust-name").value,
          table_number: $("cust-table").value,
          items: [...cart.values()].map((l) => ({ id: l.dish.id, quantity: l.qty })),
        },
      });
      cart.clear();
      renderCart();
      say(msg, "Order #" + order.id + " is in the kitchen. Total " + money(order.total) + ".", "ok");
      loadMenu(); // stock changed, refresh sold-out marks
    } catch (err) {
      say(msg, err.message, "error");
    } finally {
      button.disabled = false;
    }
  });

  /* ---------------- reservations ---------------- */
  let chosenTable = null;

  function pad(n) { return String(n).padStart(2, "0"); }
  function localInput(d) {
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) +
      "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
  }
  const suggested = new Date();
  suggested.setDate(suggested.getDate() + 1);
  suggested.setHours(19, 0, 0, 0);
  $("r-start").value = localInput(suggested);
  $("r-start").min = localInput(new Date());

  function resetChoice() {
    chosenTable = null;
    $("table-choices").replaceChildren();
  }
  $("r-guests").addEventListener("input", resetChoice);
  $("r-start").addEventListener("input", resetChoice);

  $("check-tables").addEventListener("click", async () => {
    const msg = $("reserve-msg");
    say(msg, "");
    chosenTable = null;
    try {
      const q = new URLSearchParams({ guests: $("r-guests").value, start: $("r-start").value });
      const data = await api("/api/reservations/availability/?" + q);
      const box = $("table-choices");
      if (data.tables.length === 0) {
        box.replaceChildren();
        return say(msg, "No table is free at that time for your party. Try another time.", "error");
      }
      const chips = data.tables.map((t) => {
        const chip = el("button", {
          type: "button", class: "chip",
          onclick: () => {
            chosenTable = t.id;
            chips.forEach((c) => c.classList.toggle("is-active", c === chip));
          },
        }, "Table " + t.number + " ", el("small", {}, "seats " + t.capacity));
        return chip;
      });
      box.replaceChildren(...chips);
      say(msg, data.tables.length + " table(s) free. Pick one, or confirm and we will choose the best fit.", "ok");
    } catch (err) {
      say(msg, err.message, "error");
    }
  });

  $("reserve-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const msg = $("reserve-msg");
    const button = $("reserve-btn");
    button.disabled = true;
    try {
      const r = await api("/api/reservations/", {
        method: "POST",
        body: {
          customer_name: $("r-name").value,
          phone: $("r-phone").value,
          guests: $("r-guests").value,
          start: $("r-start").value,
          table_id: chosenTable,
        },
      });
      say(msg, "");
      resetChoice();
      showTicket(r);
    } catch (err) {
      say(msg, err.message, "error");
    } finally {
      button.disabled = false;
    }
  });

  function showTicket(r) {
    const rows = [
      ["Name", r.customer_name],
      ["Table", "Table " + r.table],
      ["Guests", String(r.guests)],
      ["Arrive", r.start],
      ["Table held until", r.end],
    ];
    $("ticket-body").replaceChildren(...rows.flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));
    $("ticket").hidden = false;
    $("ticket").scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  loadMenu();
})();
