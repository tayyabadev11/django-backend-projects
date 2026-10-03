(function () {
  "use strict";

  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const $ = (id) => document.getElementById(id);
  const money = (n) => "Rs. " + Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });
  const amount = (n) => String(Number(Number(n).toFixed(3)));

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
    if (res.status === 403) { window.location.reload(); }
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  let lowStockText = "";
  function flash(text) {
    const shown = text || lowStockText;
    const box = $("alert");
    box.textContent = shown;
    box.hidden = !shown;
  }

  /* ---------------- tabs ---------------- */
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("is-active", t === tab));
      document.querySelectorAll(".panel").forEach((p) =>
        p.classList.toggle("is-active", p.id === "tab-" + tab.dataset.tab));
    });
  });

  function emptyRow(cols, text) {
    return el("tr", {}, el("td", { colspan: String(cols), class: "empty" }, text));
  }

  /* ---------------- sales report ---------------- */
  const today = new Date();
  $("report-date").value = today.getFullYear() + "-" +
    String(today.getMonth() + 1).padStart(2, "0") + "-" + String(today.getDate()).padStart(2, "0");

  async function loadReport() {
    const date = $("report-date").value;
    $("report-csv").href = "/api/reports/sales.csv?date=" + encodeURIComponent(date);
    try {
      const r = await api("/api/reports/sales/?date=" + encodeURIComponent(date));
      $("stats").replaceChildren(
        ...[["Orders", String(r.orders)], ["Revenue", money(r.revenue)], ["Average order", money(r.average)]]
          .map(([label, value]) => el("div", { class: "stat" }, el("span", {}, label), el("strong", {}, value)))
      );
      const body = $("top-table").tBodies[0];
      body.replaceChildren(...(r.top_items.length
        ? r.top_items.map((t) => el("tr", {},
            el("td", {}, t.name), el("td", { class: "num" }, String(t.quantity)), el("td", { class: "num" }, money(t.revenue))))
        : [emptyRow(3, "No orders on this date.")]));
    } catch (err) { flash(err.message); }
  }
  $("report-load").addEventListener("click", loadReport);
  $("report-date").addEventListener("change", loadReport);

  /* ---------------- orders ---------------- */
  let statusesLoaded = false;

  async function loadOrders() {
    try {
      const filter = $("order-filter").value;
      const data = await api("/api/orders/" + (filter ? "?status=" + filter : ""));
      if (!statusesLoaded) {
        data.statuses.forEach((s) => $("order-filter").append(el("option", { value: s.key }, s.label)));
        statusesLoaded = true;
      }
      const body = $("orders-table").tBodies[0];
      body.replaceChildren(...(data.orders.length ? data.orders.map((o) => orderRow(o, data.statuses))
        : [emptyRow(7, "No orders yet.")]));
    } catch (err) { flash(err.message); }
  }

  function orderRow(order, statuses) {
    const select = el("select", { "aria-label": "Status of order " + order.id },
      statuses.map((s) => el("option", { value: s.key }, s.label)));
    select.value = order.status;
    select.addEventListener("change", async () => {
      try {
        await api("/api/orders/" + order.id + "/status/", { method: "POST", body: { status: select.value } });
        order.status = select.value;
        flash("");
      } catch (err) {
        select.value = order.status;
        flash(err.message);
      }
    });
    return el("tr", {},
      el("td", {}, "#" + order.id), el("td", {}, order.time), el("td", {}, order.customer_name),
      el("td", {}, order.table_number ? String(order.table_number) : "-"),
      el("td", {}, order.items), el("td", { class: "num" }, money(order.total)), el("td", {}, select));
  }
  $("orders-refresh").addEventListener("click", loadOrders);
  $("order-filter").addEventListener("change", loadOrders);

  /* ---------------- inventory ---------------- */
  async function loadInventory() {
    try {
      const data = await api("/api/inventory/");
      if (data.low_stock.length) {
        lowStockText = "Low stock: " + data.low_stock.map((i) => i.name + " (" + amount(i.quantity) + " " + i.unit + " left)").join(", ") + ".";
      } else {
        lowStockText = "";
      }
      flash("");
      $("inventory-grid").replaceChildren(...data.items.map(inventoryCard));
    } catch (err) { flash(err.message); }
  }

  function inventoryCard(item) {
    const input = el("input", { type: "number", min: "0", step: "any", placeholder: "Add " + item.unit, "aria-label": "Restock " + item.name });
    const form = el("form", {}, input, el("button", { class: "btn btn-small", type: "submit" }, "Restock"));
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await api("/api/inventory/" + item.id + "/restock/", { method: "POST", body: { amount: input.value } });
        loadInventory();
      } catch (err) { flash(err.message); }
    });
    const level = Math.min(100, (item.quantity / Math.max(item.reorder_level * 4, 0.001)) * 100);
    return el("div", { class: "inv" + (item.is_low ? " is-low" : "") },
      el("h3", {}, item.name),
      el("div", { class: "amount" }, amount(item.quantity) + " " + item.unit),
      el("div", { class: "meter" }, el("i", { style: "width:" + level + "%" })),
      el("small", {}, "Reorder at " + amount(item.reorder_level) + " " + item.unit + " "),
      item.is_low ? el("span", { class: "tag" }, "Low stock") : null,
      form
    );
  }

  /* ---------------- reservations ---------------- */
  async function loadBookings() {
    try {
      const data = await api("/api/reservations/");
      const body = $("bookings-table").tBodies[0];
      body.replaceChildren(...(data.reservations.length ? data.reservations.map(bookingRow)
        : [emptyRow(8, "No upcoming reservations.")]));
    } catch (err) { flash(err.message); }
  }

  function bookingRow(r) {
    const cancel = r.status === "confirmed"
      ? el("button", { class: "btn btn-quiet btn-small", type: "button", onclick: async () => {
          try { await api("/api/reservations/" + r.id + "/cancel/", { method: "POST" }); loadBookings(); }
          catch (err) { flash(err.message); }
        } }, "Cancel")
      : null;
    return el("tr", {},
      el("td", {}, r.start), el("td", {}, r.end), el("td", {}, r.customer_name), el("td", {}, r.phone || "-"),
      el("td", { class: "num" }, String(r.guests)), el("td", {}, "Table " + r.table),
      el("td", {}, el("span", { class: "pill " + r.status }, r.status)), el("td", {}, cancel));
  }
  $("bookings-refresh").addEventListener("click", loadBookings);

  loadReport();
  loadOrders();
  loadInventory();
  loadBookings();
  setInterval(() => { loadOrders(); loadInventory(); }, 30000);
})();
