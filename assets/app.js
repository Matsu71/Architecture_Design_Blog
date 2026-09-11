const ERA_LABELS = {
  traditional: "江戸以前",
  "early-modern": "明治",
  modern: "大正〜昭和前期",
  postwar: "戦後",
  contemporary: "現代"
};

const VISIT_LABELS = {
  public: "見学しやすい",
  limited: "条件あり",
  reservation: "予約制",
  "exterior-only": "外観のみ",
  private: "非公開",
  closed: "閉館",
  demolished: "現存せず",
  unknown: "要確認"
};

let allBuildings = [];
let filteredBuildings = [];
let activeBuildingId = null;
let map;
let markers = new Map();

const els = {
  list: document.getElementById("building-list"),
  resultSummary: document.getElementById("result-summary"),
  search: document.getElementById("search-input"),
  prefecture: document.getElementById("prefecture-filter"),
  era: document.getElementById("era-filter"),
  visit: document.getElementById("visit-filter"),
  sort: document.getElementById("sort-filter"),
  reset: document.getElementById("reset-filters"),
  showKanto: document.getElementById("show-kanto"),
  showJapan: document.getElementById("show-japan"),
  dialog: document.getElementById("building-dialog"),
  dialogContent: document.getElementById("dialog-content"),
  dialogClose: document.getElementById("dialog-close")
};

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function initMap() {
  map = L.map("map", {
    zoomControl: true,
    minZoom: 4,
    maxZoom: 18,
    scrollWheelZoom: true
  }).setView([36.0, 139.4], 8);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);
}

function makeMarkerIcon(building, isActive = false) {
  const year = building.completionYear ? String(building.completionYear).slice(-2) : "建";
  return L.divIcon({
    className: `arch-marker${isActive ? " marker-active" : ""}`,
    html: `<span>${escapeHtml(year)}</span>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });
}

function renderMarkers(buildings) {
  for (const marker of markers.values()) marker.remove();
  markers.clear();

  buildings.forEach((building) => {
    if (!Number.isFinite(building.lat) || !Number.isFinite(building.lng)) return;

    const marker = L.marker([building.lat, building.lng], {
      icon: makeMarkerIcon(building, building.id === activeBuildingId),
      title: building.nameJa
    }).addTo(map);

    marker.bindPopup(`
      <div class="map-popup">
        <strong>${escapeHtml(building.nameJa)}</strong>
        <span>${escapeHtml(building.area)} · ${escapeHtml(building.completionYear || "年代不明")} · ${escapeHtml(building.architects?.join(" / ") || "設計者不明")}</span>
      </div>
    `);

    marker.on("click", () => {
      setActive(building.id, false);
      scrollCardIntoView(building.id);
    });

    markers.set(building.id, marker);
  });
}

function renderPrefectures() {
  const current = els.prefecture.value || "all";
  const prefectures = [...new Set(allBuildings.map((building) => building.prefecture))].sort((a, b) => a.localeCompare(b, "ja"));

  els.prefecture.innerHTML = '<option value="all">すべて</option>' + prefectures
    .map((prefecture) => `<option value="${escapeHtml(prefecture)}">${escapeHtml(prefecture)}</option>`)
    .join("");

  if (["all", ...prefectures].includes(current)) els.prefecture.value = current;
}

function cardTemplate(building) {
  const era = ERA_LABELS[building.era] || building.era || "年代未分類";
  const visit = VISIT_LABELS[building.visit?.status] || "要確認";
  const activeClass = building.id === activeBuildingId ? " is-active" : "";

  return `
    <button class="building-card${activeClass}" type="button" data-building-id="${escapeHtml(building.id)}">
      <div class="card-year">${escapeHtml(building.completionYear || "—")}</div>
      <div>
        <div class="card-meta">
          <span>${escapeHtml(building.prefecture)} ${escapeHtml(building.area)}</span>
          <span>${escapeHtml(era)}</span>
          <span>${escapeHtml(visit)}</span>
        </div>
        <h3>${escapeHtml(building.nameJa)}</h3>
        <p class="card-one-liner">${escapeHtml(building.oneLiner)}</p>
        <p class="card-architect">${escapeHtml(building.architects?.join(" / ") || "設計者未登録")}</p>
      </div>
      <span class="card-arrow" aria-hidden="true">↗</span>
    </button>
  `;
}

function renderList(buildings) {
  if (!buildings.length) {
    els.list.innerHTML = '<div class="empty-state">条件に一致する建築がありません。フィルターを変更してください。</div>';
    return;
  }

  els.list.innerHTML = buildings.map(cardTemplate).join("");

  els.list.querySelectorAll("[data-building-id]").forEach((card) => {
    card.addEventListener("mouseenter", () => setActive(card.dataset.buildingId, false));
    card.addEventListener("focus", () => setActive(card.dataset.buildingId, false));
    card.addEventListener("click", () => openBuilding(card.dataset.buildingId));
  });
}

function normalize(value) {
  return String(value || "").toLocaleLowerCase("ja").normalize("NFKC");
}

function matchesSearch(building, query) {
  if (!query) return true;
  const haystack = [
    building.nameJa,
    building.nameEn,
    building.prefecture,
    building.municipality,
    building.area,
    building.address,
    ...(building.architects || []),
    ...(building.buildingTypes || []),
    ...(building.styles || []),
    building.oneLiner,
    building.summary
  ].map(normalize).join(" ");

  return haystack.includes(query);
}

function applyFilters({ fitMap = false } = {}) {
  const query = normalize(els.search.value.trim());
  const prefecture = els.prefecture.value;
  const era = els.era.value;
  const visit = els.visit.value;
  const sort = els.sort.value;

  filteredBuildings = allBuildings.filter((building) => {
    if (!matchesSearch(building, query)) return false;
    if (prefecture !== "all" && building.prefecture !== prefecture) return false;
    if (era !== "all" && building.era !== era) return false;
    if (visit !== "all" && building.visit?.status !== visit) return false;
    return true;
  });

  filteredBuildings.sort((a, b) => {
    if (sort === "oldest") return (a.completionYear ?? 9999) - (b.completionYear ?? 9999);
    if (sort === "newest") return (b.completionYear ?? 0) - (a.completionYear ?? 0);
    return (b.visitPriority ?? 0) - (a.visitPriority ?? 0) || (b.importance ?? 0) - (a.importance ?? 0) || (a.completionYear ?? 9999) - (b.completionYear ?? 9999);
  });

  if (activeBuildingId && !filteredBuildings.some((building) => building.id === activeBuildingId)) {
    activeBuildingId = filteredBuildings[0]?.id || null;
  }

  renderList(filteredBuildings);
  renderMarkers(filteredBuildings);
  els.resultSummary.textContent = `${filteredBuildings.length}件表示 / 現在は関東シードデータを整備中`;

  if (fitMap && filteredBuildings.length) fitMapToBuildings(filteredBuildings);
}

function fitMapToBuildings(buildings, fallbackZoom = 9) {
  const points = buildings
    .filter((building) => Number.isFinite(building.lat) && Number.isFinite(building.lng))
    .map((building) => [building.lat, building.lng]);

  if (!points.length) return;
  if (points.length === 1) {
    map.setView(points[0], fallbackZoom);
    return;
  }

  map.fitBounds(L.latLngBounds(points), { padding: [50, 50], maxZoom: 11 });
}

function setActive(id, pan = true) {
  if (activeBuildingId === id) return;
  const previous = activeBuildingId;
  activeBuildingId = id;

  if (previous && markers.has(previous)) {
    const building = allBuildings.find((item) => item.id === previous);
    if (building) markers.get(previous).setIcon(makeMarkerIcon(building, false));
  }

  if (id && markers.has(id)) {
    const building = allBuildings.find((item) => item.id === id);
    if (building) {
      markers.get(id).setIcon(makeMarkerIcon(building, true));
      if (pan) map.panTo([building.lat, building.lng]);
    }
  }

  document.querySelectorAll(".building-card").forEach((card) => {
    card.classList.toggle("is-active", card.dataset.buildingId === id);
  });
}

function scrollCardIntoView(id) {
  const card = document.querySelector(`[data-building-id="${CSS.escape(id)}"]`);
  card?.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function detailTemplate(building) {
  const visit = building.visit || {};
  const sources = (building.sources || []).map((source) => `
    <li>
      <a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)}</a>
      — ${escapeHtml(source.publisher || "")}
    </li>
  `).join("");

  return `
    <article class="dialog-inner">
      <p class="dialog-kicker">${escapeHtml(building.prefecture)} / ${escapeHtml(building.area)} / ${escapeHtml(building.completionYear || "年代不明")}</p>
      <h2>${escapeHtml(building.nameJa)}</h2>
      <p class="dialog-sub">${escapeHtml(building.nameEn || "")} ${building.architects?.length ? ` · ${escapeHtml(building.architects.join(" / "))}` : ""}</p>
      <p class="dialog-lead">${escapeHtml(building.summary)}</p>

      <section class="dialog-section">
        <h3>なぜ見に行く？</h3>
        <p>${escapeHtml(building.whyVisit)}</p>
      </section>

      <section class="dialog-section">
        <h3>現地で見るポイント</h3>
        <ol class="highlight-list">
          ${(building.highlights || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ol>
      </section>

      <section class="dialog-section">
        <h3>基本情報</h3>
        <div class="detail-grid">
          <div><small>竣工</small><strong>${escapeHtml(building.completionYear || "未登録")}</strong></div>
          <div><small>設計</small><strong>${escapeHtml(building.architects?.join(" / ") || "未登録")}</strong></div>
          <div><small>用途</small><strong>${escapeHtml(building.buildingTypes?.join(" / ") || "未登録")}</strong></div>
          <div><small>様式・分類</small><strong>${escapeHtml(building.styles?.join(" / ") || ERA_LABELS[building.era] || "未登録")}</strong></div>
          <div><small>所在地</small><strong>${escapeHtml(building.address || "未登録")}</strong></div>
          <div><small>見学</small><strong>${escapeHtml(VISIT_LABELS[visit.status] || "要確認")}</strong></div>
          <div><small>目安時間</small><strong>${escapeHtml(visit.estimatedVisitMinutes ? `${visit.estimatedVisitMinutes}分` : "未登録")}</strong></div>
          <div><small>最終確認</small><strong>${escapeHtml(visit.lastChecked || building.verification?.lastVerified || "未確認")}</strong></div>
        </div>
        ${visit.officialUrl ? `<a class="official-link" href="${escapeHtml(visit.officialUrl)}" target="_blank" rel="noopener noreferrer">公式サイトで最新情報を確認 →</a>` : ""}
      </section>

      <section class="dialog-section">
        <h3>出典</h3>
        <ul class="source-list">${sources || "<li>出典を整備中</li>"}</ul>
      </section>
    </article>
  `;
}

function openBuilding(id) {
  const building = allBuildings.find((item) => item.id === id);
  if (!building) return;

  setActive(id, true);
  els.dialogContent.innerHTML = detailTemplate(building);

  if (typeof els.dialog.showModal === "function") {
    els.dialog.showModal();
  } else {
    els.dialog.setAttribute("open", "");
  }
}

function closeDialog() {
  if (typeof els.dialog.close === "function") els.dialog.close();
  else els.dialog.removeAttribute("open");
}

function wireEvents() {
  [els.search, els.prefecture, els.era, els.visit, els.sort].forEach((element) => {
    element.addEventListener(element === els.search ? "input" : "change", () => applyFilters({ fitMap: false }));
  });

  els.reset.addEventListener("click", () => {
    els.search.value = "";
    els.prefecture.value = "all";
    els.era.value = "all";
    els.visit.value = "all";
    els.sort.value = "recommended";
    activeBuildingId = null;
    applyFilters({ fitMap: true });
  });

  els.showKanto.addEventListener("click", () => map.setView([36.0, 139.4], 8));
  els.showJapan.addEventListener("click", () => map.setView([37.2, 137.2], 5));
  els.dialogClose.addEventListener("click", closeDialog);
  els.dialog.addEventListener("click", (event) => {
    if (event.target === els.dialog) closeDialog();
  });
}

async function loadBuildings() {
  const response = await fetch("data/buildings.json");
  if (!response.ok) throw new Error(`Failed to load building data: ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data)) throw new Error("Building data must be an array");
  return data;
}

async function boot() {
  initMap();
  wireEvents();

  try {
    allBuildings = await loadBuildings();
    renderPrefectures();
    applyFilters({ fitMap: true });
  } catch (error) {
    console.error(error);
    els.resultSummary.textContent = "データの読み込みに失敗しました";
    els.list.innerHTML = `
      <div class="empty-state">
        建築データを読み込めませんでした。<br />
        <small>ローカルではファイルを直接開かず、README記載の簡易HTTPサーバーを使用してください。</small>
      </div>
    `;
  }
}

boot();
