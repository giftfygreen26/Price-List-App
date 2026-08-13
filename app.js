/* ============================================================================
   Digital Stainless Steel Price List — App Logic
   ============================================================================ */

const LS_KEY = "ssteel_overlay_v1";
const LS_SELECTION = "ssteel_selection_v1";

const TYPE_KEYWORDS = {
  "Sheet": ["แผ่น", "sheet", "plate", "แผ่นสแตนเลส", "แผ่นเหล็ก"],
  "Round Pipe": ["ท่อ", "pipe", "ท่อกลม", "round pipe", "round"],
  "Square Tube": ["ท่อ", "pipe", "tube", "ท่อสี่เหลี่ยม", "square tube", "square"],
  "Rectangular Tube": ["ท่อ", "pipe", "tube", "กล่อง", "ท่อสี่เหลี่ยมกล่อง", "rectangular", "box tube"],
  "Schedule Pipe": ["ท่อ", "pipe", "sch", "schedule", "ท่ออุตสาหกรรม", "industrial pipe"],
  "Round Bar": ["เพลา", "bar", "shaft", "round bar", "เพลากลม", "rod"],
  "Square Bar": ["เพลา", "bar", "เพลาสี่เหลี่ยม", "square bar"],
  "Hex Bar": ["เพลา", "bar", "เพลาหกเหลี่ยม", "hex bar", "hexagon"],
  "Flat Bar": ["เส้นแบน", "flat", "flat bar", "แบน"],
  "Angle Bar": ["ฉาก", "angle", "ฉากรีด", "angle bar", "l-bar"],
  "Channel": ["ราง", "channel", "track", "รางพับ", "รางรีด"],
  "Accessory": ["pvc", "เคลือบ", "coating", "accessory", "บริการ"],
  "Aluminum Sheet": ["อลูมิเนียม", "อลูมิเนี่ยม", "aluminum", "aluminium", "แผ่นอลูมิเนียม", "อลู"],
  "Aluminum Checker Plate": ["อลูมิเนียม", "อลูมิเนี่ยม", "aluminum", "aluminium", "ลายกันลื่น", "ตีนเป็ด", "ตีนไก่", "checker", "checker plate", "tread plate", "diamond plate", "อลู"],
};

const TYPE_LABEL_EN = {
  "Sheet": "Sheet", "Round Pipe": "Round Pipe", "Square Tube": "Square Tube",
  "Rectangular Tube": "Rectangular Tube", "Schedule Pipe": "Schedule Pipe (SCH)",
  "Round Bar": "Round Bar / Shaft", "Square Bar": "Square Bar", "Hex Bar": "Hex Bar",
  "Flat Bar": "Flat Bar", "Angle Bar": "Angle Bar", "Channel": "Channel / Track",
  "Accessory": "Accessory / Service", "Aluminum Sheet": "Aluminum Sheet",
  "Aluminum Checker Plate": "Aluminum Checker Plate",
};

/* ---------------------------------------------------------------------------
   State
--------------------------------------------------------------------------- */
let overlay = loadOverlay();
let selection = new Set(loadSelection());
let currentDetailProductId = null;
let currentQuoteLang = "th";

function loadOverlay() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (!parsed.priceOverrides) parsed.priceOverrides = {}; // back-compat for overlays saved before this field existed
      return parsed;
    }
  } catch (e) {}
  return { addedProducts: [], addedPrices: [], editedProducts: {}, priceOverrides: {} };
}
function saveOverlay() {
  localStorage.setItem(LS_KEY, JSON.stringify(overlay));
}
function loadSelection() {
  try {
    const raw = localStorage.getItem(LS_SELECTION);
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return [];
}
function saveSelection() {
  localStorage.setItem(LS_SELECTION, JSON.stringify(Array.from(selection)));
}

/* ---------------------------------------------------------------------------
   Data access layer (merges base DB + localStorage overlay)
--------------------------------------------------------------------------- */
function getAllProducts() {
  const base = DB.products.map(p => {
    const edits = overlay.editedProducts[p.id];
    return edits ? Object.assign({}, p, edits) : p;
  });
  return base.concat(overlay.addedProducts);
}
function getAllPrices() {
  const base = DB.priceHistory.map(h => {
    const ov = overlay.priceOverrides[h.id];
    return ov ? Object.assign({}, h, ov) : h;
  });
  return base.concat(overlay.addedPrices);
}
let _productIndex = null;
function productIndex() {
  if (_productIndex && _productIndex._v === overlay) return _productIndex.map;
  const map = {};
  getAllProducts().forEach(p => map[p.id] = p);
  _productIndex = { _v: overlay, map };
  return map;
}
function invalidateCache() { _productIndex = null; _priceByProduct = null; _blobCache = null; }

let _priceByProduct = null;
function pricesByProduct() {
  if (_priceByProduct) return _priceByProduct;
  const map = {};
  getAllPrices().forEach(pr => {
    if (!map[pr.productId]) map[pr.productId] = [];
    map[pr.productId].push(pr);
  });
  Object.values(map).forEach(arr => arr.sort((a, b) => b.effectiveDate.localeCompare(a.effectiveDate)));
  _priceByProduct = map;
  return map;
}
function getHistory(productId) {
  return (pricesByProduct()[productId] || []);
}
function getCurrentPrice(productId) {
  const h = getHistory(productId);
  return h.length ? h[0] : null;
}

/* ---------------------------------------------------------------------------
   Search
--------------------------------------------------------------------------- */
let _blobCache = null;
function blobCache() {
  if (_blobCache) return _blobCache;
  const map = {};
  getAllProducts().forEach(p => { map[p.id] = buildBlob(p); });
  _blobCache = map;
  return map;
}
function normText(s) {
  return (s || "").toString().toLowerCase()
    .replace(/['"]/g, "")
    .replace(/×/g, "x")
    .replace(/\s*x\s*/g, "x")
    .replace(/\s+/g, " ")
    .trim();
}
function buildBlob(p) {
  const kw = (TYPE_KEYWORDS[p.productType] || []).join(" ");
  const dims = p.dimensions ? Object.values(p.dimensions).join(" ") : "";
  const raw = [p.productType, p.productTypeTh, kw, p.grade, p.surface, p.dimensionLabel, p.unit, dims].join(" ");
  let blob = normText(raw);
  // Also index "3mm" style shorthand for "3.0mm" printed sizes, and vice versa,
  // so a Sales person typing "3mm" still finds "3.0mm" labelled products.
  const stripped = blob.replace(/(\d+)\.0mm/g, "$1mm");
  if (stripped !== blob) blob = blob + " " + stripped;
  return blob;
}
function tokenizeQuery(q) {
  const norm = normText(q);
  return norm.split(" ").filter(Boolean);
}
function searchProducts(query, filters) {
  filters = filters || {};
  const tokens = tokenizeQuery(query);
  const blobs = blobCache();
  const all = getAllProducts();
  let results = all.filter(p => {
    if (filters.type && p.productType !== filters.type) return false;
    if (filters.grade && p.grade !== filters.grade) return false;
    if (filters.surface && p.surface !== filters.surface) return false;
    if (filters.review === "hide" && p.needsReview) return false;
    if (filters.review === "only" && !p.needsReview) return false;
    if (!p.active) return false;
    if (!tokens.length) return true;
    const blob = blobs[p.id];
    return tokens.every(t => blob.includes(t));
  });
  results = results.map(p => ({ product: p, current: getCurrentPrice(p.id) }));
  if (!filters.includeUnpriced) {
    results = results.filter(r => r.current); // Sales search: only show products that actually have a price on record
  }
  // Sort: exact-ish matches first (shorter dimension label = more likely a direct hit), then by type/grade/size
  results.sort((a, b) => {
    if (tokens.length) {
      const la = a.product.dimensionLabel.length, lb = b.product.dimensionLabel.length;
      if (la !== lb) return la - lb;
    }
    if (a.product.productType !== b.product.productType) return a.product.productType.localeCompare(b.product.productType);
    if (a.product.grade !== b.product.grade) return a.product.grade.localeCompare(b.product.grade);
    return a.product.dimensionLabel.localeCompare(b.product.dimensionLabel, undefined, { numeric: true });
  });
  return results;
}

/* ---------------------------------------------------------------------------
   Formatting helpers
--------------------------------------------------------------------------- */
function fmtBaht(n) {
  if (n === null || n === undefined) return "—";
  return "฿" + Number(n).toLocaleString("en-US", { maximumFractionDigits: 2 });
}
function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}
function fmtDateShort(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}
function gradeHeader(p) {
  const g = p.grade || "";
  const surfacePart = (p.surface && p.surface !== "-" ? " " + p.surface : "");
  if (/^\d/.test(g)) return "SUS " + g + surfacePart; // stainless grades: 304, 316, 430, 201...
  if (/^A-/i.test(g)) return "อลูมิเนียม " + g + surfacePart; // aluminum alloys: A-1100 H14, A-5052 H32...
  if (g && g !== "-") return g + surfacePart;
  return (p.productTypeTh || p.productType) + surfacePart;
}
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast._tm);
  toast._tm = setTimeout(() => t.classList.remove("show"), 2200);
}

/* ---------------------------------------------------------------------------
   Tabs / Views
--------------------------------------------------------------------------- */
document.querySelectorAll("nav.tabs button").forEach(btn => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});
function switchView(view) {
  document.querySelectorAll("nav.tabs button").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === "view-" + view));
  if (view === "products") renderProductsView();
  if (view === "admin") renderAdminView();
  if (view === "quote") renderQuoteView();
  if (view === "import") renderImportView();
}

/* ---------------------------------------------------------------------------
   SEARCH VIEW
--------------------------------------------------------------------------- */
const searchInput = document.getElementById("searchInput");
const resultsBody = document.getElementById("resultsBody");
const resultsCount = document.getElementById("resultsCount");
const emptyState = document.getElementById("emptyState");
const selectedCountEl = document.getElementById("selectedCount");
const goQuoteBtn = document.getElementById("goQuoteBtn");

function currentFilters() {
  return {
    type: document.getElementById("fType").value,
    grade: document.getElementById("fGrade").value,
    surface: document.getElementById("fSurface").value,
    review: document.getElementById("fReview").value,
  };
}

function renderSearch() {
  const q = searchInput.value.trim();
  const filters = currentFilters();
  let results;
  if (!q && !filters.type && !filters.grade && !filters.surface && !filters.review) {
    results = [];
  } else {
    results = searchProducts(q, filters).slice(0, 300);
  }
  resultsBody.innerHTML = "";
  if (!results.length) {
    emptyState.style.display = "block";
    emptyState.querySelector("b") && null;
    resultsCount.textContent = "";
  } else {
    emptyState.style.display = "none";
    resultsCount.textContent = results.length + (results.length === 300 ? "+ " : " ") + "product(s) found";
  }
  const frag = document.createDocumentFragment();
  results.forEach(({ product, current }) => {
    const tr = document.createElement("tr");
    tr.dataset.id = product.id;
    if (selection.has(product.id)) tr.classList.add("selected");
    tr.innerHTML = `
      <td><input type="checkbox" class="chk" ${selection.has(product.id) ? "checked" : ""}></td>
      <td><b>${escapeHtml(TYPE_LABEL_EN[product.productType] || product.productType)}</b><br><span class="subtle">${escapeHtml(product.productTypeTh)}</span></td>
      <td><span class="badge badge-grade">${escapeHtml(product.grade)}</span></td>
      <td>${escapeHtml(product.surface)}</td>
      <td>${escapeHtml(product.dimensionLabel)}</td>
      <td class="price-cell">${fmtBaht(current.price)} <small>${current.pricePerKg ? fmtBaht(current.pricePerKg) + "/kg" : ""}</small>
        ${(product.needsReview || current.needsReview) ? '<span class="badge badge-review">⚠️ REVIEW</span>' : ""}</td>
      <td class="updated-cell">${fmtDateShort(current.effectiveDate)}</td>
    `;
    tr.querySelector(".chk").addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSelection(product.id);
    });
    tr.addEventListener("click", () => openDetail(product.id));
    frag.appendChild(tr);
  });
  resultsBody.appendChild(frag);
  updateSelectedBar();
}

function toggleSelection(id) {
  if (selection.has(id)) selection.delete(id); else selection.add(id);
  saveSelection();
  updateSelectedBar();
  renderSearch();
}
function updateSelectedBar() {
  selectedCountEl.textContent = selection.size + " selected";
  goQuoteBtn.disabled = selection.size === 0;
}
goQuoteBtn.addEventListener("click", () => switchView("quote"));

searchInput.addEventListener("input", debounce(renderSearch, 80));
document.querySelectorAll(".quick-chips button").forEach(b => {
  b.addEventListener("click", () => { searchInput.value = b.dataset.q; renderSearch(); searchInput.focus(); });
});
document.getElementById("filtersToggle").addEventListener("click", () => {
  document.getElementById("filtersPanel").classList.toggle("open");
});
["fType", "fGrade", "fSurface", "fReview"].forEach(id => {
  document.getElementById(id).addEventListener("change", renderSearch);
});

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}
function escapeHtml(s) {
  return (s === null || s === undefined) ? "" : String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function populateFilterOptions() {
  const products = getAllProducts();
  const types = Array.from(new Set(products.map(p => p.productType))).sort();
  const grades = Array.from(new Set(products.map(p => p.grade))).sort();
  const surfaces = Array.from(new Set(products.map(p => p.surface))).sort();
  fillSelect("fType", types, TYPE_LABEL_EN);
  fillSelect("fGrade", grades);
  fillSelect("fSurface", surfaces);
  fillSelect("prodTypeFilter", types, TYPE_LABEL_EN);
  fillSelect("prodGradeFilter", grades);
}
function fillSelect(id, values, labelMap) {
  const el = document.getElementById(id);
  const current = el.value;
  const keep = el.firstElementChild;
  el.innerHTML = "";
  el.appendChild(keep);
  values.forEach(v => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = (labelMap && labelMap[v]) || v;
    el.appendChild(opt);
  });
  el.value = current;
}

/* ---------------------------------------------------------------------------
   PRODUCT DETAIL PANEL
--------------------------------------------------------------------------- */
const overlayEl = document.getElementById("overlay");
const detailPanel = document.getElementById("detailPanel");
overlayEl.addEventListener("click", closeDetail);

function openDetail(productId) {
  currentDetailProductId = productId;
  const product = productIndex()[productId];
  const current = getCurrentPrice(productId);
  const history = getHistory(productId);
  const isSelected = selection.has(productId);

  let reviewHtml = "";
  if (product.needsReview) {
    reviewHtml = `<div class="review-flag">⚠️ NEEDS REVIEW — ${escapeHtml(product.reviewNote || "This item was flagged during PDF extraction; verify before quoting.")}</div>`;
  } else if (current && current.needsReview) {
    reviewHtml = `<div class="review-flag">⚠️ NEEDS REVIEW — ${escapeHtml(current.notes || "This price record needs manual verification.")}</div>`;
  }

  let historyRows = history.map((h, i) => `
    <tr>
      <td>${fmtDate(h.effectiveDate)}</td>
      <td>${fmtBaht(h.price)}</td>
      <td>${h.pricePerKg ? fmtBaht(h.pricePerKg) : "—"}${h.pricePerKgCalculated ? " <span class='subtle'>(calc)</span>" : ""}</td>
      <td class="subtle">${escapeHtml(h.source || "PDF")}</td>
      <td class="subtle">${h.needsReview ? "⚠️" : ""}</td>
    </tr>`).join("");

  detailPanel.innerHTML = `
    <div class="detail-header">
      <div>
        <h3>${escapeHtml(gradeHeader(product))}</h3>
        <span class="subtle">${escapeHtml(TYPE_LABEL_EN[product.productType] || product.productType)} · ${escapeHtml(product.dimensionLabel)}</span>
      </div>
      <button class="close" id="detailCloseBtn">✕</button>
    </div>
    <div class="detail-body">
      ${reviewHtml}
      <div class="big-price">${current ? fmtBaht(current.price) : "—"}<small>per ${escapeHtml(product.unit)}${current && current.pricePerKg ? " · " + fmtBaht(current.pricePerKg) + " / kg" : ""}</small></div>
      <div class="meta-row"><span class="k">Last Updated</span><span>${current ? fmtDate(current.effectiveDate) : "—"}</span></div>
      <div class="meta-row"><span class="k">Grade</span><span>${escapeHtml(product.grade)}</span></div>
      <div class="meta-row"><span class="k">Surface</span><span>${escapeHtml(product.surface)}</span></div>
      <div class="meta-row"><span class="k">Size</span><span>${escapeHtml(product.dimensionLabel)}</span></div>
      <div class="meta-row"><span class="k">Unit</span><span>${escapeHtml(product.unit)}</span></div>
      <h3 style="margin-top:18px;">Price History (${history.length})</h3>
      <table class="history-table">
        <thead><tr><th>Date</th><th>Price</th><th>Price/kg</th><th>Source</th><th></th></tr></thead>
        <tbody>${historyRows || "<tr><td colspan=5 class='subtle'>No history</td></tr>"}</tbody>
      </table>
    </div>
    <div class="detail-actions">
      <button class="btn ${isSelected ? "btn-secondary" : "btn-primary"}" id="detailSelectBtn">${isSelected ? "✓ Selected" : "+ Add to Quotation"}</button>
      <button class="btn btn-green" id="detailQuickCopyBtn">📋 Copy Quotation</button>
      <button class="btn btn-secondary" id="detailEditBtn">✏️ Edit</button>
    </div>
  `;
  document.getElementById("detailCloseBtn").addEventListener("click", closeDetail);
  document.getElementById("detailSelectBtn").addEventListener("click", () => {
    toggleSelection(productId);
    openDetail(productId);
  });
  document.getElementById("detailQuickCopyBtn").addEventListener("click", () => {
    const text = buildQuoteText([{ product, current }], "th", "");
    copyToClipboard(text);
  });
  document.getElementById("detailEditBtn").addEventListener("click", () => {
    closeDetail();
    startEditProduct(productId);
  });
  overlayEl.classList.add("open");
  detailPanel.classList.add("open");
}
function closeDetail() {
  overlayEl.classList.remove("open");
  detailPanel.classList.remove("open");
}

/* ---------------------------------------------------------------------------
   PRODUCTS VIEW
--------------------------------------------------------------------------- */
function renderProductsView() {
  const products = getAllProducts();
  const withPrice = products.map(p => ({ product: p, current: getCurrentPrice(p.id) }));
  const stats = document.getElementById("productStats");
  const totalHist = getAllPrices().length;
  const reviewCount = products.filter(p => p.needsReview).length;
  const types = new Set(products.map(p => p.productType)).size;
  stats.innerHTML = `
    <div class="stat-card"><div class="num">${products.length}</div><div class="lbl">Unique Products</div></div>
    <div class="stat-card"><div class="num">${totalHist}</div><div class="lbl">Price Records</div></div>
    <div class="stat-card"><div class="num">${types}</div><div class="lbl">Product Types</div></div>
    <div class="stat-card"><div class="num">${reviewCount}</div><div class="lbl">⚠️ Needs Review</div></div>
  `;

  function draw() {
    const q = normText(document.getElementById("prodSearch").value);
    const tf = document.getElementById("prodTypeFilter").value;
    const gf = document.getElementById("prodGradeFilter").value;
    const rows = withPrice.filter(({ product }) => {
      if (tf && product.productType !== tf) return false;
      if (gf && product.grade !== gf) return false;
      if (q && !blobCache()[product.id].includes(q)) return false;
      return true;
    }).slice(0, 400);
    const body = document.getElementById("productsBody");
    body.innerHTML = rows.map(({ product, current }) => `
      <tr>
        <td class="subtle">${product.id}</td>
        <td>${escapeHtml(TYPE_LABEL_EN[product.productType] || product.productType)}</td>
        <td>${escapeHtml(product.grade)}</td>
        <td>${escapeHtml(product.surface)}</td>
        <td>${escapeHtml(product.dimensionLabel)}</td>
        <td class="subtle">${escapeHtml(product.unit)}</td>
        <td><b>${current ? fmtBaht(current.price) : "—"}</b></td>
        <td>${product.needsReview ? '<span class="pill pill-warn">⚠️ Review</span>' : '<span class="pill pill-ok">OK</span>'}</td>
        <td style="white-space:nowrap;">
          <button class="btn btn-ghost btn-sm view-detail-btn" data-id="${product.id}">View</button>
          <button class="btn btn-ghost btn-sm edit-product-btn" data-id="${product.id}">✏️ Edit</button>
        </td>
      </tr>
    `).join("") || `<tr><td colspan=9 class="subtle" style="padding:20px;text-align:center;">No products match.</td></tr>`;
    body.querySelectorAll(".view-detail-btn").forEach(b => b.addEventListener("click", () => openDetail(b.dataset.id)));
    body.querySelectorAll(".edit-product-btn").forEach(b => b.addEventListener("click", () => startEditProduct(b.dataset.id)));
  }
  document.getElementById("prodSearch").oninput = debounce(draw, 80);
  document.getElementById("prodTypeFilter").onchange = draw;
  document.getElementById("prodGradeFilter").onchange = draw;
  draw();
}

/* ---------------------------------------------------------------------------
   PRICE HISTORY VIEW
--------------------------------------------------------------------------- */
function renderHistoryView() {
  const input = document.getElementById("histSearch");
  const list = document.getElementById("histResultsList");
  function draw() {
    const q = input.value.trim();
    if (!q) { list.innerHTML = ""; return; }
    const results = searchProducts(q, {}).slice(0, 40);
    list.innerHTML = results.map(({ product, current }) => `
      <div class="meta-row" style="cursor:pointer;" data-id="${product.id}">
        <span class="k">${escapeHtml(gradeHeader(product))} — ${escapeHtml(product.dimensionLabel)}</span>
        <span><b>${fmtBaht(current.price)}</b></span>
      </div>
    `).join("") || `<p class="subtle">No matches.</p>`;
    list.querySelectorAll("[data-id]").forEach(el => el.addEventListener("click", () => showHistoryDetail(el.dataset.id)));
  }
  input.oninput = debounce(draw, 80);
}
function showHistoryDetail(productId) {
  const product = productIndex()[productId];
  const history = getHistory(productId);
  document.getElementById("histDetailCard").style.display = "block";
  document.getElementById("histDetailTitle").textContent = gradeHeader(product) + " — " + product.dimensionLabel;
  const table = document.getElementById("histDetailTable");
  table.innerHTML = `
    <thead><tr><th>Effective Date</th><th>Price</th><th>Price / KG</th><th>Source</th><th>Notes</th></tr></thead>
    <tbody>
      ${history.map((h, i) => `
        <tr style="${i === 0 ? "font-weight:700;color:var(--green);" : ""}">
          <td>${fmtDate(h.effectiveDate)} ${i === 0 ? "★ Current" : ""}</td>
          <td>${fmtBaht(h.price)}</td>
          <td>${h.pricePerKg ? fmtBaht(h.pricePerKg) : "—"}</td>
          <td>${escapeHtml(h.source || "")}</td>
          <td>${escapeHtml(h.notes || "")}${h.needsReview ? " ⚠️" : ""}</td>
        </tr>`).join("")}
    </tbody>
  `;
}

/* ---------------------------------------------------------------------------
   PRICE MANAGEMENT (ADMIN) VIEW
--------------------------------------------------------------------------- */
let selectedPriceProductId = null;
let editingProductId = null;

function productFormFields() {
  return {
    type: document.getElementById("npType"), typeTh: document.getElementById("npTypeTh"),
    grade: document.getElementById("npGrade"), surface: document.getElementById("npSurface"),
    dimLabel: document.getElementById("npDimLabel"), unit: document.getElementById("npUnit"),
    needsReview: document.getElementById("npNeedsReview"), reviewNote: document.getElementById("npReviewNote"),
  };
}
function clearProductForm() {
  const f = productFormFields();
  f.type.value = ""; f.typeTh.value = ""; f.grade.value = ""; f.surface.value = "";
  f.dimLabel.value = ""; f.unit.value = ""; f.needsReview.checked = false; f.reviewNote.value = "";
}
function startEditProduct(id) {
  const p = productIndex()[id];
  if (!p) return;
  editingProductId = id;
  const f = productFormFields();
  f.type.value = p.productType; f.typeTh.value = p.productTypeTh; f.grade.value = p.grade;
  f.surface.value = p.surface === "-" ? "" : p.surface; f.dimLabel.value = p.dimensionLabel; f.unit.value = p.unit;
  f.needsReview.checked = !!p.needsReview; f.reviewNote.value = p.reviewNote || "";
  document.getElementById("productFormTitle").textContent = "✏️ Editing Product";
  document.getElementById("productFormHint").textContent = "Editing: " + gradeHeader(p) + " — " + p.dimensionLabel + ". Changes save instantly to this browser.";
  document.getElementById("addProductBtn").textContent = "Save Changes";
  document.getElementById("cancelEditBtn").style.display = "inline-block";
  switchView("admin");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
function exitEditMode() {
  editingProductId = null;
  clearProductForm();
  document.getElementById("productFormTitle").textContent = "➕ Add New Product";
  document.getElementById("productFormHint").textContent = "Fill in the details for a brand-new product.";
  document.getElementById("addProductBtn").textContent = "Add Product";
  document.getElementById("cancelEditBtn").style.display = "none";
}

function renderAdminView() {
  document.getElementById("npDate").value = new Date().toISOString().slice(0, 10);
  document.getElementById("cancelEditBtn").onclick = exitEditMode;

  document.getElementById("addProductBtn").onclick = () => {
    const f = productFormFields();
    const ptype = f.type.value.trim();
    const ptypeTh = f.typeTh.value.trim();
    const grade = f.grade.value.trim();
    const surface = f.surface.value.trim() || "-";
    const dimLabel = f.dimLabel.value.trim();
    const unit = f.unit.value.trim() || "pc";
    const needsReview = f.needsReview.checked;
    const reviewNote = f.reviewNote.value.trim();
    if (!ptype || !grade || !dimLabel) { toast("Please fill Product Type, Grade, and Size."); return; }

    if (editingProductId) {
      overlay.editedProducts[editingProductId] = {
        productType: ptype, productTypeTh: ptypeTh || ptype, grade, surface, dimensionLabel: dimLabel,
        unit, needsReview, reviewNote,
      };
      saveOverlay(); invalidateCache();
      // If the admin just cleared the review flag, also clear it on the CURRENT
      // price record (the one shown on the main search page) — older historical
      // price records stay flagged as-is, preserving the extraction audit trail.
      if (!needsReview) {
        const cur = getCurrentPrice(editingProductId);
        if (cur && cur.needsReview) {
          overlay.priceOverrides[cur.id] = { needsReview: false };
          saveOverlay(); invalidateCache();
        }
      }
      populateFilterOptions();
      toast("Product updated ✓");
      exitEditMode();
      renderAdminView();
      return;
    }

    const id = "NP" + Date.now();
    overlay.addedProducts.push({
      id, productType: ptype, productTypeTh: ptypeTh || ptype, grade, surface, dimensionLabel: dimLabel,
      dimensions: {}, unit, active: true, searchTokens: [], needsReview, reviewNote,
    });
    saveOverlay(); invalidateCache(); populateFilterOptions();
    toast("Product added. Now add a price for it below.");
    clearProductForm();
    document.getElementById("priceProductSearch").value = dimLabel;
    document.getElementById("priceProductSearch").dispatchEvent(new Event("input"));
    renderAdminView();
  };

  const pSearch = document.getElementById("priceProductSearch");
  const pResults = document.getElementById("priceProductResults");
  pSearch.oninput = debounce(() => {
    const q = pSearch.value.trim();
    if (!q) { pResults.innerHTML = ""; return; }
    const results = searchProducts(q, { includeUnpriced: true }).slice(0, 15);
    pResults.innerHTML = results.map(({ product, current }) => `
      <div class="meta-row" style="cursor:pointer;" data-id="${product.id}">
        <span>${escapeHtml(gradeHeader(product))} — ${escapeHtml(product.dimensionLabel)}</span>
        <span class="subtle">${current ? fmtBaht(current.price) : "no price yet"}</span>
      </div>`).join("");
    pResults.querySelectorAll("[data-id]").forEach(el => el.addEventListener("click", () => {
      selectedPriceProductId = el.dataset.id;
      const p = productIndex()[selectedPriceProductId];
      document.getElementById("selectedPriceProduct").innerHTML = `Selected: <b>${escapeHtml(gradeHeader(p))} — ${escapeHtml(p.dimensionLabel)}</b>`;
      document.getElementById("addPriceBtn").disabled = false;
    }));
  }, 100);

  document.getElementById("addPriceBtn").onclick = () => {
    if (!selectedPriceProductId) return;
    const price = parseFloat(document.getElementById("npPrice").value);
    const priceKg = parseFloat(document.getElementById("npPriceKg").value);
    const date = document.getElementById("npDate").value;
    const notes = document.getElementById("npNotes").value.trim();
    if (!price || !date) { toast("Price and effective date are required."); return; }
    overlay.addedPrices.push({
      id: "NH" + Date.now(), productId: selectedPriceProductId, price, pricePerKg: isNaN(priceKg) ? null : priceKg,
      pricePerKgCalculated: false, currency: "THB", effectiveDate: date, source: "Manual entry (Price Management)",
      notes, needsReview: false,
    });
    saveOverlay(); invalidateCache();
    toast("New price saved — this is now the Current Price if it's the latest date.");
    document.getElementById("npPrice").value = "";
    document.getElementById("npPriceKg").value = "";
    document.getElementById("npNotes").value = "";
    renderAdminView();
  };

  function draw() {
    const q = normText(document.getElementById("adminSearch").value);
    const products = getAllProducts().filter(p => !q || blobCache()[p.id].includes(q)).slice(0, 300);
    document.getElementById("adminBody").innerHTML = products.map(p => {
      const cur = getCurrentPrice(p.id);
      return `<tr>
        <td>${escapeHtml(TYPE_LABEL_EN[p.productType] || p.productType)}</td>
        <td>${escapeHtml(p.grade)}</td>
        <td>${escapeHtml(p.surface)}</td>
        <td>${escapeHtml(p.dimensionLabel)}</td>
        <td><b>${cur ? fmtBaht(cur.price) : "—"}</b></td>
        <td>${p.needsReview ? '<span class="pill pill-warn">⚠️ Review</span>' : '<span class="pill pill-ok">OK</span>'}</td>
        <td class="subtle">${cur ? fmtDate(cur.effectiveDate) : "—"}</td>
        <td style="white-space:nowrap;">
          <button class="btn btn-ghost btn-sm edit-product-btn" data-id="${p.id}">✏️ Edit</button>
          <button class="btn btn-ghost btn-sm quick-price-btn" data-id="${p.id}">+ Price</button>
        </td>
      </tr>`;
    }).join("") || `<tr><td colspan=8 class="subtle" style="padding:16px;text-align:center;">No products.</td></tr>`;
    document.getElementById("adminBody").querySelectorAll(".quick-price-btn").forEach(b => b.addEventListener("click", () => {
      selectedPriceProductId = b.dataset.id;
      const p = productIndex()[selectedPriceProductId];
      document.getElementById("selectedPriceProduct").innerHTML = `Selected: <b>${escapeHtml(gradeHeader(p))} — ${escapeHtml(p.dimensionLabel)}</b>`;
      document.getElementById("addPriceBtn").disabled = false;
      window.scrollTo({ top: 0, behavior: "smooth" });
    }));
    document.getElementById("adminBody").querySelectorAll(".edit-product-btn").forEach(b => b.addEventListener("click", () => startEditProduct(b.dataset.id)));
  }
  document.getElementById("adminSearch").oninput = debounce(draw, 80);
  draw();

  document.getElementById("exportJsonBtn").onclick = () => {
    const data = { products: getAllProducts(), priceHistory: getAllPrices() };
    downloadFile("stainless_price_export.json", JSON.stringify(data, null, 2), "application/json");
  };
  document.getElementById("exportCsvBtn").onclick = () => {
    const rows = [["productId", "productType", "grade", "surface", "dimensionLabel", "unit", "currentPrice", "pricePerKg", "effectiveDate", "needsReview"]];
    getAllProducts().forEach(p => {
      const cur = getCurrentPrice(p.id);
      rows.push([p.id, p.productType, p.grade, p.surface, p.dimensionLabel, p.unit,
        cur ? cur.price : "", cur && cur.pricePerKg ? cur.pricePerKg : "", cur ? cur.effectiveDate : "", p.needsReview ? "YES" : ""]);
    });
    downloadFile("stainless_price_export.csv", toCsv(rows), "text/csv");
  };
}

function downloadFile(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
  toast("Downloaded " + filename);
}
function toCsv(rows) {
  return rows.map(r => r.map(c => {
    const s = (c === null || c === undefined) ? "" : String(c);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }).join(",")).join("\r\n");
}

/* ---------------------------------------------------------------------------
   QUOTATION VIEW
--------------------------------------------------------------------------- */
function renderQuoteView() {
  const list = document.getElementById("quoteSelectedList");
  const items = Array.from(selection).map(id => ({ product: productIndex()[id], current: getCurrentPrice(id) })).filter(x => x.product && x.current);
  document.getElementById("quoteEmptyHint").style.display = items.length ? "none" : "block";
  list.innerHTML = items.map(({ product, current }) => `
    <li data-id="${product.id}">
      <div class="info"><b>${escapeHtml(gradeHeader(product))}</b><span>${escapeHtml(product.dimensionLabel)}</span></div>
      <div class="price">${fmtBaht(current.price)}</div>
      <button title="Remove" data-id="${product.id}">✕</button>
    </li>
  `).join("");
  list.querySelectorAll("button[data-id]").forEach(b => b.addEventListener("click", () => {
    selection.delete(b.dataset.id); saveSelection(); renderQuoteView(); renderSearch();
  }));
  updateQuoteText();
}
document.querySelectorAll(".quote-tabs button").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".quote-tabs button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    currentQuoteLang = b.dataset.lang;
    updateQuoteText();
  });
});
document.getElementById("customerName").addEventListener("input", updateQuoteText);
document.getElementById("clearQuoteBtn").addEventListener("click", () => {
  selection.clear(); saveSelection(); renderQuoteView(); renderSearch();
});
document.getElementById("copyQuoteBtn").addEventListener("click", () => {
  copyToClipboard(document.getElementById("quoteOutput").value);
});

function updateQuoteText() {
  const items = Array.from(selection).map(id => ({ product: productIndex()[id], current: getCurrentPrice(id) })).filter(x => x.product && x.current);
  const name = document.getElementById("customerName").value.trim();
  document.getElementById("quoteOutput").value = buildQuoteText(items, currentQuoteLang, name);
}

function buildQuoteText(items, lang, customerName) {
  if (!items.length) return "";
  // group by grade+surface+productType header
  const groups = {};
  const order = [];
  items.forEach(({ product, current }) => {
    const key = product.productType + "|" + product.grade + "|" + product.surface;
    if (!groups[key]) { groups[key] = { product, lines: [] }; order.push(key); }
    groups[key].lines.push({ product, current });
  });
  if (lang === "th") {
    let out = `สวัสดีค่ะคุณลูกค้า${customerName ? " คุณ" + customerName : ""}\n`;
    order.forEach(key => {
      const g = groups[key];
      out += `ขอเสนอราคา ${gradeHeader(g.product)}\n`;
      g.lines.forEach(({ product, current }) => {
        out += `* ${product.dimensionLabel} ราคา ${Number(current.price).toLocaleString("en-US")} บาท/${product.unit}\n`;
      });
    });
    out += `\nหากสนใจสามารถแจ้งจำนวนและสอบถามเพิ่มเติมได้เลยค่ะ\nขอบคุณค่ะ`;
    return out;
  } else {
    let out = `Dear ${customerName || "Customer"},\n\nThank you for your inquiry. Please find our quotation below:\n\n`;
    order.forEach(key => {
      const g = groups[key];
      out += `${gradeHeader(g.product)}:\n`;
      g.lines.forEach(({ product, current }) => {
        out += `  - ${product.dimensionLabel}: THB ${Number(current.price).toLocaleString("en-US")} / ${product.unit}\n`;
      });
      out += "\n";
    });
    out += `Prices are current as of the latest update and are subject to change without prior notice. Please let us know the quantity required, and feel free to reach out with any questions.\n\nBest regards,`;
    return out;
  }
}
function copyToClipboard(text) {
  if (!text) { toast("Nothing to copy — select a product first."); return; }
  navigator.clipboard && navigator.clipboard.writeText(text).then(() => toast("Quotation copied ✓")).catch(() => fallbackCopy(text));
  if (!navigator.clipboard) fallbackCopy(text);
}
function fallbackCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text; document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); toast("Quotation copied ✓"); } catch (e) { toast("Copy failed — please select text manually."); }
  document.body.removeChild(ta);
}

/* ---------------------------------------------------------------------------
   IMPORT / REVIEW VIEW
--------------------------------------------------------------------------- */
let lastImportRows = [];
function renderImportView() {
  document.getElementById("importSummary").innerHTML = "";
  document.getElementById("importPreviewWrap").style.display = "none";

  const dz = document.getElementById("dropzone");
  const fileInput = document.getElementById("csvFile");
  dz.onclick = () => fileInput.click();
  dz.ondragover = (e) => { e.preventDefault(); dz.classList.add("drag"); };
  dz.ondragleave = () => dz.classList.remove("drag");
  dz.ondrop = (e) => { e.preventDefault(); dz.classList.remove("drag"); if (e.dataTransfer.files[0]) handleCsvFile(e.dataTransfer.files[0]); };
  fileInput.onchange = () => { if (fileInput.files[0]) handleCsvFile(fileInput.files[0]); };

  document.getElementById("confirmImportBtn").onclick = confirmImport;

  renderReviewTable();
}

function handleCsvFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const rows = parseCsv(e.target.result);
      lastImportRows = matchImportRows(rows);
      showImportPreview(lastImportRows);
    } catch (err) {
      toast("Could not parse CSV: " + err.message);
    }
  };
  reader.readAsText(file);
}
function parseCsv(text) {
  const lines = text.split(/\r\n|\n|\r/).filter(l => l.trim().length);
  if (!lines.length) return [];
  const headers = splitCsvLine(lines[0]).map(h => h.trim());
  return lines.slice(1).map(line => {
    const cells = splitCsvLine(line);
    const obj = {};
    headers.forEach((h, i) => obj[h] = (cells[i] || "").trim());
    return obj;
  });
}
function splitCsvLine(line) {
  const out = []; let cur = ""; let inQ = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQ) {
      if (c === '"' && line[i + 1] === '"') { cur += '"'; i++; }
      else if (c === '"') { inQ = false; }
      else cur += c;
    } else {
      if (c === '"') inQ = true;
      else if (c === ",") { out.push(cur); cur = ""; }
      else cur += c;
    }
  }
  out.push(cur);
  return out;
}
function matchImportRows(rows) {
  const products = getAllProducts();
  return rows.map((r, idx) => {
    let matched = null;
    if (r.productId) matched = products.find(p => p.id === r.productId);
    if (!matched) {
      matched = products.find(p =>
        p.productType.toLowerCase() === (r.productType || "").toLowerCase() &&
        p.grade.toLowerCase() === (r.grade || "").toLowerCase() &&
        (p.surface || "").toLowerCase() === (r.surface || "").toLowerCase() &&
        normText(p.dimensionLabel) === normText(r.dimensionLabel || "")
      );
    }
    const price = parseFloat(r.price);
    const status = matched ? "matched" : (r.productType && r.grade && r.dimensionLabel ? "new" : "error");
    return { row: idx + 1, raw: r, matched, status, price };
  });
}
function showImportPreview(rows) {
  document.getElementById("importPreviewWrap").style.display = "block";
  const matched = rows.filter(r => r.status === "matched").length;
  const news = rows.filter(r => r.status === "new").length;
  const errors = rows.filter(r => r.status === "error").length;
  document.getElementById("importSummary").innerHTML = `
    <div class="stat-cards">
      <div class="stat-card"><div class="num">${rows.length}</div><div class="lbl">Rows Read</div></div>
      <div class="stat-card"><div class="num">${matched}</div><div class="lbl">Matched Existing</div></div>
      <div class="stat-card"><div class="num">${news}</div><div class="lbl">New Products</div></div>
      <div class="stat-card"><div class="num">${errors}</div><div class="lbl">⚠️ Errors / Incomplete</div></div>
    </div>`;
  document.getElementById("importBody").innerHTML = rows.map(r => `
    <tr>
      <td>${r.row}</td>
      <td>${r.status === "matched" ? '<span class="pill pill-ok">✓ Matched</span>' : r.status === "new" ? '<span class="pill">＋ New Product</span>' : '<span class="pill pill-warn">⚠️ Error</span>'}</td>
      <td>${r.matched ? escapeHtml(gradeHeader(r.matched) + " — " + r.matched.dimensionLabel) : escapeHtml((r.raw.productType || "") + " " + (r.raw.grade || "") + " " + (r.raw.dimensionLabel || ""))}</td>
      <td>${isNaN(r.price) ? "—" : fmtBaht(r.price)}</td>
      <td>${escapeHtml(r.raw.effectiveDate || "")}</td>
      <td class="subtle">${escapeHtml(r.raw.notes || "")}</td>
    </tr>
  `).join("");
}
function confirmImport() {
  if (!lastImportRows.length) return;
  let added = 0, createdProducts = 0, skipped = 0;
  lastImportRows.forEach(r => {
    if (r.status === "error" || isNaN(r.price)) { skipped++; return; }
    let productId;
    if (r.matched) {
      productId = r.matched.id;
    } else {
      productId = "IMP" + Date.now() + Math.floor(Math.random() * 1000);
      overlay.addedProducts.push({
        id: productId, productType: r.raw.productType, productTypeTh: r.raw.productType,
        grade: r.raw.grade, surface: r.raw.surface || "-", dimensionLabel: r.raw.dimensionLabel,
        dimensions: {}, unit: r.raw.unit || "pc", active: true, searchTokens: [], needsReview: false, reviewNote: "",
      });
      createdProducts++;
    }
    overlay.addedPrices.push({
      id: "IMPH" + Date.now() + Math.floor(Math.random() * 1000), productId,
      price: r.price, pricePerKg: r.raw.pricePerKg ? parseFloat(r.raw.pricePerKg) : null,
      pricePerKgCalculated: false, currency: "THB",
      effectiveDate: r.raw.effectiveDate || new Date().toISOString().slice(0, 10),
      source: r.raw.source || "CSV Import", notes: r.raw.notes || "", needsReview: false,
    });
    added++;
  });
  saveOverlay(); invalidateCache(); populateFilterOptions();
  toast(`Imported ${added} price record(s), created ${createdProducts} new product(s). Skipped ${skipped}.`);
  lastImportRows = [];
  document.getElementById("importPreviewWrap").style.display = "none";
  document.getElementById("csvFile").value = "";
}

function renderReviewTable() {
  const products = getAllProducts();
  const rows = [];
  products.forEach(p => {
    if (p.needsReview) {
      const cur = getCurrentPrice(p.id);
      rows.push({ p, date: cur ? cur.effectiveDate : "", issue: p.reviewNote || "Flagged during extraction" });
    }
  });
  getAllPrices().forEach(h => {
    if (h.needsReview) {
      const p = productIndex()[h.productId];
      if (p) rows.push({ p, date: h.effectiveDate, issue: h.notes || "Price record flagged during extraction" });
    }
  });
  document.getElementById("reviewBody").innerHTML = rows.map(r => `
    <tr>
      <td>${escapeHtml(gradeHeader(r.p))}</td>
      <td>${escapeHtml(r.p.dimensionLabel)}</td>
      <td class="subtle">${fmtDate(r.date)}</td>
      <td>${escapeHtml(r.issue)}</td>
      <td><button class="btn btn-ghost btn-sm review-edit-btn" data-id="${r.p.id}">✏️ Fix</button></td>
    </tr>
  `).join("") || `<tr><td colspan=5 class="subtle" style="padding:16px;text-align:center;">No flagged items 🎉</td></tr>`;
  document.getElementById("reviewBody").querySelectorAll(".review-edit-btn").forEach(b => b.addEventListener("click", () => startEditProduct(b.dataset.id)));

  document.getElementById("reviewNotesList").innerHTML = (DB.reviewNotes || []).map(n => `
    <div class="review-flag"><b>${escapeHtml(n.area)}:</b> ${escapeHtml(n.note)}</div>
  `).join("");
}

/* ---------------------------------------------------------------------------
   Init
--------------------------------------------------------------------------- */
function init() {
  populateFilterOptions();
  document.getElementById("headerMeta").textContent =
    getAllProducts().length + " products · " + getAllPrices().length + " price records · updated through " +
    fmtDate((DB.priceHistory.map(p => p.effectiveDate).sort().pop()));
  renderSearch();
  renderHistoryView();
}
init();
