/**
 * RetailIQ — AI Retail Intelligence Command Center
 * Frontend Controller & Visualization Engine
 * 
 * Features:
 * - Ultra-lightweight particle constellation canvas & mouse parallax
 * - Synchronized futuristic command sidebar & tab navigation
 * - Neon-styled Chart.js daily revenue line chart & category donut
 * - Real-time deterministic alert feeds, inventory coverage meters, and store rankings
 * - Interactive AI Copilot with structured evidence formatting & raw JSON auditing
 */

let currentStoreId = "ALL";
let salesChartInstance = null;
let categoryChartInstance = null;
let allAlertsData = [];
let allInventoryData = [];
let allProductMgmtData = [];

document.addEventListener("DOMContentLoaded", () => {
  initParticleSystem();
  initMouseParallax();
  initEventListeners();
  loadDashboardData();
  loadAlerts();
  loadInventory();
  loadRules();
  loadProductManagement();

  if (window.lucide) {
    window.lucide.createIcons();
  }
});

/* ==========================================================
   1. PARTICLE CONSTELLATION & PARALLAX BACKGROUND
   ========================================================== */
function initParticleSystem() {
  const canvas = document.getElementById("particleCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const numParticles = 45;
  const particles = [];

  for (let i = 0; i < numParticles; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
      radius: Math.random() * 1.8 + 0.8,
      color: Math.random() > 0.4 ? "rgba(56, 189, 248, " : "rgba(139, 92, 246, ",
      alpha: Math.random() * 0.5 + 0.2
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < numParticles; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      // Draw node
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color + p.alpha + ")";
      ctx.fill();

      // Connect near neighbors
      for (let j = i + 1; j < numParticles; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 110) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          const edgeAlpha = (1 - dist / 110) * 0.18;
          ctx.strokeStyle = "rgba(56, 189, 248, " + edgeAlpha + ")";
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(render);
  }
  render();
}

function initMouseParallax() {
  const iconNodes = document.querySelectorAll(".floating-icon-node");
  if (!iconNodes.length) return;

  let targetX = 0;
  let targetY = 0;
  let currentX = 0;
  let currentY = 0;

  window.addEventListener("mousemove", (e) => {
    targetX = (e.clientX / window.innerWidth - 0.5) * 40;
    targetY = (e.clientY / window.innerHeight - 0.5) * 40;
  });

  function updateParallax() {
    currentX += (targetX - currentX) * 0.05;
    currentY += (targetY - currentY) * 0.05;

    iconNodes.forEach((node) => {
      const speed = parseFloat(node.getAttribute("data-speed")) || 0.05;
      const offsetX = currentX * speed * 25;
      const offsetY = currentY * speed * 25;
      node.style.transform = `translate3d(${offsetX}px, ${offsetY}px, 0)`;
    });

    requestAnimationFrame(updateParallax);
  }
  updateParallax();
}

/* ==========================================================
   2. EVENT LISTENERS & NAVIGATION
   ========================================================= */
function initEventListeners() {
  // Synchronized navigation tabs (Top tabs & Sidebar buttons)
  document.querySelectorAll(".nav-tab").forEach((tabBtn) => {
    tabBtn.addEventListener("click", () => {
      const targetTab = tabBtn.getAttribute("data-tab");
      if (targetTab) {
        switchTab(targetTab);
      }
    });
  });

  // Store selector dropdown
  const storeFilter = document.getElementById("storeFilter");
  if (storeFilter) {
    storeFilter.addEventListener("change", (e) => {
      currentStoreId = e.target.value;
      loadDashboardData();
      loadAlerts();
      loadInventory();
    });
  }

  // Copilot drawer toggle
  const openChatBtn = document.getElementById("openChatBtn");
  const closeChatBtn = document.getElementById("closeChatBtn");
  const copilotDrawer = document.getElementById("copilotDrawer");
  const dashboardPane = document.querySelector(".dashboard-pane");

  if (openChatBtn && copilotDrawer) {
    openChatBtn.addEventListener("click", () => {
      copilotDrawer.classList.toggle("collapsed");
      if (dashboardPane) {
        dashboardPane.classList.toggle("drawer-open", !copilotDrawer.classList.contains("collapsed"));
      }
    });
  }

  if (closeChatBtn && copilotDrawer) {
    closeChatBtn.addEventListener("click", () => {
      copilotDrawer.classList.add("collapsed");
      if (dashboardPane) {
        dashboardPane.classList.remove("drawer-open");
      }
    });
  }

  // Chat Form submission
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");

  if (chatForm && chatInput) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = chatInput.value.trim();
      if (!query) return;
      chatInput.value = "";
      sendChatMessage(query);
    });
  }

  // Alert category filter pills
  document.querySelectorAll("#ruleTypeFilters .pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      document.querySelectorAll("#ruleTypeFilters .pill").forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      const ruleType = pill.getAttribute("data-rule");
      renderAlertsFeed(ruleType);
    });
  });

  // Inventory search filter
  const invSearch = document.getElementById("inventorySearch");
  if (invSearch) {
    invSearch.addEventListener("input", (e) => {
      const term = e.target.value.toLowerCase();
      filterInventoryTable(term);
    });
  }

  // Open Add Product Modal button
  const openAddProdBtn = document.getElementById("openAddProductModalBtn");
  if (openAddProdBtn) {
    openAddProdBtn.addEventListener("click", openAddProductModal);
  }

  // Product Management search & filters
  const mgmtSearch = document.getElementById("mgmtSearchInput");
  if (mgmtSearch) {
    mgmtSearch.addEventListener("input", filterProductMgmtTable);
  }
  const mgmtCat = document.getElementById("mgmtCategoryFilter");
  if (mgmtCat) {
    mgmtCat.addEventListener("change", filterProductMgmtTable);
  }
  const mgmtStore = document.getElementById("mgmtStoreFilter");
  if (mgmtStore) {
    mgmtStore.addEventListener("change", filterProductMgmtTable);
  }
}

function switchTab(tabId) {
  // Sync all top nav tabs and sidebar buttons
  document.querySelectorAll(".nav-tab").forEach((t) => {
    if (t.getAttribute("data-tab") === tabId) {
      t.classList.add("active");
    } else {
      t.classList.remove("active");
    }
  });

  // Switch tab pane
  document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
  const targetPane = document.getElementById(tabId);
  if (targetPane) {
    targetPane.classList.add("active");
  }
}

function scrollToSection(sectionId) {
  switchTab("overviewTab");
  setTimeout(() => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, 100);
}

/* ==========================================================
   3. EXECUTIVE OVERVIEW & KPI METRICS
   ========================================================== */
async function loadDashboardData() {
  try {
    const url = currentStoreId === "ALL" ? "/api/dashboard" : `/api/dashboard?store_id=${currentStoreId}`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status !== "success") return;

    // Update KPI Cards
    const k = data.kpis;
    document.getElementById("kpiTotalRevenue").textContent = `$${k.total_revenue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("kpiRevenue30d").textContent = `Trailing 30d: $${k.revenue_30d.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("kpiUnitsSold").textContent = k.total_units_sold.toLocaleString();
    document.getElementById("kpiUnits30d").textContent = `Trailing 30d: ${k.units_30d.toLocaleString()} units`;
    document.getElementById("kpiInventoryUnits").textContent = `${k.total_inventory_units.toLocaleString()} units`;
    document.getElementById("kpiInventoryValuation").textContent = `Valuation: $${k.inventory_valuation.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("kpiAlertCount").textContent = data.alert_summary.total;
    document.getElementById("kpiAlertSubtext").textContent = `${data.alert_summary.critical} Critical Stock-outs (${data.alert_summary.warning} Warnings)`;

    // Update alert badges
    const tabAlertPill = document.getElementById("tabAlertPill");
    const tabAlertPillTop = document.getElementById("tabAlertPillTop");
    const chatAlertCounter = document.getElementById("chatAlertCounter");

    if (tabAlertPill) tabAlertPill.textContent = data.alert_summary.total;
    if (tabAlertPillTop) tabAlertPillTop.textContent = data.alert_summary.total;
    if (chatAlertCounter) chatAlertCounter.textContent = data.alert_summary.critical;

    // Populate Store Dropdown if not already populated
    populateStoreDropdown(data.store_list);

    // Update system telemetry status
    const statusText = document.getElementById("engineStatusText");
    const sysInfo = data.system_info;
    if (sysInfo && sysInfo.gemini_api_connected) {
      if (statusText) statusText.textContent = "System Status: Healthy (Gemini 1.5 Flash)";
      const cap = document.getElementById("copilotModelCaption");
      if (cap) cap.textContent = "Google Gemini 1.5 Flash Grounded";
    } else {
      if (statusText) statusText.textContent = "System Status: Healthy (Deterministic Grounded)";
      const cap = document.getElementById("copilotModelCaption");
      if (cap) cap.textContent = "Authoritative Grounded Synthesizer";
    }

    // Render Neon Charts
    renderSalesTrendChart(data.sales_trend);
    renderCategoryChart(data.categories, k.total_revenue);

    // Render Store Rankings & Urgent Priority Alerts
    renderStoreTable(data.stores, k.total_revenue);
    renderPriorityAlerts(data.top_alerts);

  } catch (err) {
    console.error("Failed to load dashboard data:", err);
  }
}

function populateStoreDropdown(stores) {
  if (!stores || !stores.length) return;

  // 1. Header active store filter
  const dropdown = document.getElementById("storeFilter");
  if (dropdown && dropdown.options.length <= 1) {
    stores.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.store_id;
      opt.textContent = `${s.store_name} (${s.location})`;
      dropdown.appendChild(opt);
    });
  }

  // 2. Product Management store filter
  const mgmtStoreFilter = document.getElementById("mgmtStoreFilter");
  if (mgmtStoreFilter && mgmtStoreFilter.options.length <= 1) {
    stores.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.store_id;
      opt.textContent = s.store_name;
      mgmtStoreFilter.appendChild(opt);
    });
  }

  // 3. Add Product Modal destination store dropdown
  const newProductStore = document.getElementById("newProductStore");
  if (newProductStore && newProductStore.options.length <= 1) {
    stores.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.store_id;
      opt.textContent = `${s.store_name} (${s.location})`;
      newProductStore.appendChild(opt);
    });
  }
}

function renderSalesTrendChart(trendData) {
  const canvas = document.getElementById("salesTrendChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (salesChartInstance) salesChartInstance.destroy();

  const labels = trendData.map((d) => d.date.slice(5)); // MM-DD
  const revenues = trendData.map((d) => d.total_revenue);

  // Create subtle neon gradient fill
  const gradient = ctx.createLinearGradient(0, 0, 0, 260);
  gradient.addColorStop(0, "rgba(6, 182, 212, 0.35)");
  gradient.addColorStop(0.6, "rgba(59, 130, 246, 0.12)");
  gradient.addColorStop(1, "rgba(2, 6, 23, 0.0)");

  salesChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Daily Revenue ($)",
          data: revenues,
          borderColor: "#06b6d4",
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointBackgroundColor: "#38bdf8",
          pointBorderColor: "#020617",
          pointBorderWidth: 1.5,
          pointRadius: 2.5,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: "#ffffff",
          pointHoverBorderColor: "#06b6d4",
          pointHoverBorderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(10, 16, 32, 0.92)",
          titleColor: "#38bdf8",
          bodyColor: "#f1f5f9",
          borderColor: "rgba(56, 189, 248, 0.35)",
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          callbacks: {
            title: (items) => `Date: 2026-${items[0].label}`,
            label: (ctx) => `Daily Revenue: $${ctx.parsed.y.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { color: "#64748b", font: { family: "'Plus Jakarta Sans', sans-serif", size: 10 } }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: {
            color: "#64748b",
            font: { family: "'JetBrains Mono', monospace", size: 10 },
            callback: (val) => `$${val >= 1000 ? (val / 1000).toFixed(0) + "k" : val}`
          }
        }
      }
    }
  });
}

function renderCategoryChart(categories, totalRev) {
  const canvas = document.getElementById("categoryChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (categoryChartInstance) categoryChartInstance.destroy();

  const labels = categories.map((c) => c.category);
  const data = categories.map((c) => c.total_revenue);
  const neonPalette = ["#06b6d4", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"];

  // Update center label
  const totalDisplay = totalRev >= 1000000 ? `$${(totalRev / 1000000).toFixed(2)}M` : `$${(totalRev / 1000).toFixed(0)}k`;
  const donutTotalElem = document.getElementById("donutTotalRevenue");
  if (donutTotalElem) {
    donutTotalElem.textContent = totalDisplay;
  }

  categoryChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: neonPalette,
          borderWidth: 2,
          borderColor: "#0a1020",
          hoverOffset: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: {
            color: "#94a3b8",
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: "500" },
            boxWidth: 12,
            padding: 10
          }
        },
        tooltip: {
          backgroundColor: "rgba(10, 16, 32, 0.92)",
          titleColor: "#ffffff",
          bodyColor: "#38bdf8",
          borderColor: "rgba(56, 189, 248, 0.35)",
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (ctx) => ` ${ctx.label}: $${ctx.parsed.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
          }
        }
      },
      cutout: "72%"
    }
  });
}

function renderStoreTable(stores, totalRev) {
  const tbody = document.querySelector("#storeTable tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  stores.forEach((s, idx) => {
    const row = document.createElement("tr");
    const sharePct = totalRev > 0 ? ((s.total_revenue / totalRev) * 100).toFixed(1) : 0;
    const rankClass = `rank-${idx + 1}`;

    row.innerHTML = `
      <td>
        <div style="display: flex; align-items: center;">
          <span class="rank-badge ${rankClass}">#${idx + 1}</span>
          <div>
            <strong style="color: #ffffff;">${escapeHtml(s.store_name)}</strong>
            <div style="font-size: 11px; color: #64748b;">${escapeHtml(s.location)}</div>
          </div>
        </div>
      </td>
      <td>
        <div style="font-family: var(--font-mono); color: #38bdf8; font-weight: 700;">
          $${s.total_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </div>
        <div style="font-size: 10px; color: #64748b;">${sharePct}% share</div>
      </td>
      <td style="font-family: var(--font-mono);">${s.total_units_sold.toLocaleString()}</td>
      <td style="font-family: var(--font-mono); color: #c084fc;">$${s.inventory_valuation.toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
    `;
    tbody.appendChild(row);
  });
}

function renderPriorityAlerts(alerts) {
  const container = document.getElementById("priorityAlertList");
  if (!container) return;
  container.innerHTML = "";

  alerts.forEach((a) => {
    const item = document.createElement("div");
    let sevClass = "critical";
    if (a.severity === "WARNING") sevClass = "warning";
    if (a.severity === "OPPORTUNITY") sevClass = "opportunity";
    if (a.severity === "ATTENTION") sevClass = "attention";

    item.className = `priority-item ${sevClass}`;
    item.innerHTML = `
      <div class="priority-left">
        <div class="priority-title">
          <span>${escapeHtml(a.product_name)}</span>
          <span style="font-size: 11px; color: #64748b; font-weight: 500;">@ ${escapeHtml(a.store_name)}</span>
        </div>
        <div class="priority-details">${escapeHtml(a.rule_triggered)} — ${escapeHtml(a.reason.slice(0, 85))}...</div>
      </div>
      <button class="card-action-btn" onclick="askPrompt('Why is ${escapeHtml(a.product_name)} flagged?')">
        <span>Inspect</span>
        <span>→</span>
      </button>
    `;
    container.appendChild(item);
  });
}

/* ==========================================================
   4. ACTIONABLE ALERTS & RULE FEED
   ========================================================== */
async function loadAlerts() {
  try {
    const url = currentStoreId === "ALL" ? "/api/alerts" : `/api/alerts?store_id=${currentStoreId}`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status !== "success") return;
    allAlertsData = data.alerts;

    // Update filter counts
    const countAll = document.getElementById("countAll");
    const countR1 = document.getElementById("countR1");
    const countR2 = document.getElementById("countR2");
    const countR3 = document.getElementById("countR3");
    const countR4 = document.getElementById("countR4");
    const countR5 = document.getElementById("countR5");

    if (countAll) countAll.textContent = allAlertsData.length;
    if (countR1) countR1.textContent = allAlertsData.filter((a) => a.rule_id === "RULE_1_STOCKOUT").length;
    if (countR2) countR2.textContent = allAlertsData.filter((a) => a.rule_id === "RULE_2_OVERSTOCK").length;
    if (countR3) countR3.textContent = allAlertsData.filter((a) => a.rule_id === "RULE_3_SLOW_MOVING").length;
    if (countR4) countR4.textContent = allAlertsData.filter((a) => a.rule_id === "RULE_4_SALES_SPIKE").length;
    if (countR5) countR5.textContent = allAlertsData.filter((a) => a.rule_id === "RULE_5_SALES_DROP").length;

    renderAlertsFeed("ALL");
  } catch (err) {
    console.error("Failed to load alerts:", err);
  }
}

function renderAlertsFeed(ruleType) {
  const container = document.getElementById("alertsFeed");
  if (!container) return;
  container.innerHTML = "";

  let filtered = allAlertsData;
  if (ruleType && ruleType !== "ALL") {
    filtered = allAlertsData.filter((a) => a.rule_id === ruleType);
  }

  if (filtered.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: #64748b; padding: 40px; font-weight: 500;">No active operational alerts matching this filter.</div>`;
    return;
  }

  filtered.forEach((a) => {
    const card = document.createElement("div");
    card.className = `alert-card severity-${a.severity}`;
    card.innerHTML = `
      <div class="alert-top">
        <div class="alert-headline">
          <span class="alert-badge ${a.severity}">${a.severity}</span>
          <span class="alert-product-name">${escapeHtml(a.product_name)}</span>
          <span class="alert-store-tag">@ ${escapeHtml(a.store_name)}</span>
        </div>
        <span style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: #94a3b8;">${escapeHtml(a.rule_triggered)}</span>
      </div>
      <div class="alert-body">
        <p class="alert-reason">${escapeHtml(a.reason)}</p>
        <div class="alert-evidence-box">📊 EVIDENCE: ${escapeHtml(a.evidence)}</div>
        <p class="alert-recommendation">💡 <strong>Recommendation:</strong> ${escapeHtml(a.recommendation)}</p>
      </div>
      <div class="alert-actions">
        <button class="btn-ask-copilot" onclick="askPrompt('Why is ${escapeHtml(a.product_name)} flagged?')">
          <span>🤖 Ask Copilot Why Flagged</span>
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

/* ==========================================================
   5. INVENTORY & FORWARD STOCK COVERAGE TABLE
   ========================================================== */
async function loadInventory() {
  try {
    const url = currentStoreId === "ALL" ? "/api/inventory" : `/api/inventory?store_id=${currentStoreId}`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status !== "success") return;
    allInventoryData = data.data;
    renderInventoryTable(allInventoryData);
  } catch (err) {
    console.error("Failed to load inventory:", err);
  }
}

function renderInventoryTable(items) {
  const tbody = document.getElementById("inventoryTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  items.forEach((item) => {
    const tr = document.createElement("tr");

    // Coverage meter calculation
    const coverage = item.days_of_stock;
    let fillClass = "healthy";
    let pct = Math.min(100, Math.max(8, (coverage / 30) * 100));

    if (coverage < 5) {
      fillClass = "critical";
    } else if (coverage < 10) {
      fillClass = "warning";
    } else if (coverage > 60) {
      fillClass = "overstock";
      pct = 100;
    }

    tr.innerHTML = `
      <td>
        <strong style="color: #ffffff;">${escapeHtml(item.product_name)}</strong>
        <div style="font-family: var(--font-mono); font-size: 10px; color: #64748b;">${escapeHtml(item.product_id)}</div>
      </td>
      <td><span style="font-size: 11px; color: #94a3b8;">${escapeHtml(item.category)}</span></td>
      <td>${escapeHtml(item.store_name)}</td>
      <td style="font-family: var(--font-mono);">$${item.selling_price.toFixed(2)}</td>
      <td style="font-family: var(--font-mono); font-weight: 700; color: #38bdf8;">${item.current_stock}</td>
      <td style="font-family: var(--font-mono);">${item.ads_7d}</td>
      <td style="font-family: var(--font-mono);">${item.ads_30d}</td>
      <td>
        <div class="coverage-meter">
          <span style="font-family: var(--font-mono); font-size: 11px; width: 38px;">${coverage > 900 ? "∞" : coverage.toFixed(1) + "d"}</span>
          <div class="meter-bar">
            <div class="meter-fill ${fillClass}" style="width: ${pct}%"></div>
          </div>
        </div>
      </td>
      <td style="font-family: var(--font-mono);">${item.reorder_level}</td>
      <td><span class="status-tag ${item.status_tag}">${item.status_tag.replace("_", " ")}</span></td>
      <td>
        <button class="card-action-btn" onclick="askPrompt('How did ${escapeHtml(item.product_name)} perform this month?')">
          Triage
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterInventoryTable(query) {
  if (!query) {
    renderInventoryTable(allInventoryData);
    return;
  }
  const filtered = allInventoryData.filter(
    (i) =>
      i.product_name.toLowerCase().includes(query) ||
      i.product_id.toLowerCase().includes(query) ||
      i.store_name.toLowerCase().includes(query) ||
      i.category.toLowerCase().includes(query)
  );
  renderInventoryTable(filtered);
}

/* ==========================================================
   6. POLICY & RULE ENGINE RAG
   ========================================================== */
async function loadRules() {
  try {
    const res = await fetch("/api/rules");
    const data = await res.json();
    if (data.status !== "success") return;

    const container = document.getElementById("rulesContainer");
    if (!container) return;
    container.innerHTML = "";

    data.sections.forEach((sec) => {
      const card = document.createElement("div");
      card.className = "rule-section-card";
      card.innerHTML = `
        <h4>${escapeHtml(sec.title)}</h4>
        <span class="rule-citation-tag">${escapeHtml(sec.citation)}</span>
        <div class="rule-body-text">${escapeHtml(sec.body)}</div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load rules:", err);
  }
}

/* ==========================================================
   7. AI COPILOT INTERACTIVE CHAT ENGINE
   ========================================================== */
function askPrompt(question) {
  const copilotDrawer = document.getElementById("copilotDrawer");
  if (copilotDrawer) {
    copilotDrawer.classList.remove("collapsed");
  }
  sendChatMessage(question);
}

async function sendChatMessage(message) {
  const container = document.getElementById("chatMessages");
  if (!container) return;

  // Append User message card
  const userMsgDiv = document.createElement("div");
  userMsgDiv.className = "chat-message user-message";
  userMsgDiv.innerHTML = `
    <div class="msg-header">
      <span class="sender-name">Store Manager</span>
      <span class="msg-time">${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
    </div>
    <div class="msg-body">${escapeHtml(message)}</div>
  `;
  container.appendChild(userMsgDiv);

  // Append Thinking Indicator
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "chat-message assistant-message";
  loadingDiv.id = "loadingIndicator";
  loadingDiv.innerHTML = `
    <div class="msg-header">
      <div class="sender-info">
        <span class="sender-avatar-mini">🤖</span>
        <span class="sender-name">RetailIQ Copilot</span>
      </div>
      <span class="msg-time">Grounding Decision...</span>
    </div>
    <div class="msg-body">
      <div class="loading-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  container.appendChild(loadingDiv);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, store_id: currentStoreId })
    });
    const data = await res.json();

    // Remove loading indicator
    const loadingElem = document.getElementById("loadingIndicator");
    if (loadingElem) loadingElem.remove();

    if (data.status !== "success") {
      appendAssistantMessage(`⚠️ Error: ${data.message || "Unable to process query."}`);
      return;
    }

    appendAssistantMessage(data.answer, data.evidence, data.citations);

  } catch (err) {
    const loadingElem = document.getElementById("loadingIndicator");
    if (loadingElem) loadingElem.remove();
    appendAssistantMessage(`⚠️ Network or server error: ${err.message}`);
  }
}

function appendAssistantMessage(rawAnswer, evidence = null, citations = null) {
  const container = document.getElementById("chatMessages");
  if (!container) return;
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-message assistant-message";

  const formattedHtml = formatStructuredResponse(rawAnswer);
  const evidenceId = "ev_" + Math.random().toString(36).substring(2, 9);

  let evidenceBtn = "";
  let evidenceBox = "";
  if (evidence && Object.keys(evidence).length > 0) {
    evidenceBtn = `<button class="evidence-drawer-toggle" onclick="toggleEvidence('${evidenceId}')">
      <span>🔍</span>
      <span>Inspect Authoritative Evidence JSON</span>
    </button>`;
    evidenceBox = `<pre class="evidence-raw" id="${evidenceId}">${escapeHtml(JSON.stringify(evidence, null, 2))}</pre>`;
  }

  msgDiv.innerHTML = `
    <div class="msg-header">
      <div class="sender-info">
        <span class="sender-avatar-mini">🤖</span>
        <span class="sender-name">RetailIQ Copilot</span>
      </div>
      <span class="msg-time">${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
    </div>
    <div class="msg-body">
      <div class="structured-output">${formattedHtml}</div>
      ${evidenceBtn}
      ${evidenceBox}
    </div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function toggleEvidence(id) {
  const elem = document.getElementById(id);
  if (elem) {
    elem.style.display = elem.style.display === "block" ? "none" : "block";
  }
}

function formatStructuredResponse(text) {
  if (!text) return "";

  // Replace Markdown headers with styled HTML sections
  let formatted = text
    .replace(/### SUMMARY/g, '<h3 class="section-summary">📌 SUMMARY</h3>')
    .replace(/### EVIDENCE/g, '<h3 class="section-evidence">📊 VERIFIED EVIDENCE</h3>')
    .replace(/### RULE CITED/g, '<h3 class="section-rule">📜 RULE / POLICY CITED</h3>')
    .replace(/### ANALYSIS/g, '<h3 class="section-analysis">🔍 ANALYSIS</h3>')
    .replace(/### RECOMMENDATION/g, '<h3 class="section-recommendation">🎯 RECOMMENDATION</h3>')
    .replace(/### ASSUMPTIONS & DATA SOURCES/g, '<h3 class="section-assumptions">⚙️ ASSUMPTIONS & DATA SOURCES</h3>');

  // Convert markdown bold **text** to <strong>text</strong>
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #ffffff;">$1</strong>');

  // Convert markdown bullet points
  formatted = formatted.replace(/^- (.*$)/gim, "<li>$1</li>");
  formatted = formatted.replace(/(<li>.*<\/li>)/gim, "<ul>$1</ul>");
  formatted = formatted.replace(/<\/ul>\s*<ul>/g, "");

  // Convert linebreaks
  formatted = formatted.replace(/\n\n/g, "<br><br>");

  return formatted;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* ==========================================================
   10. PRODUCT MANAGEMENT & INVENTORY CONTROLS
   ========================================================== */

async function loadProductManagement() {
  try {
    const res = await fetch("/api/inventory");
    const data = await res.json();
    if (data.status !== "success") return;
    allProductMgmtData = data.data;

    // Populate category filter if needed
    const catSelect = document.getElementById("mgmtCategoryFilter");
    if (catSelect && catSelect.options.length <= 1) {
      const categories = [...new Set(allProductMgmtData.map((d) => d.category))].sort();
      categories.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        catSelect.appendChild(opt);
      });
    }

    filterProductMgmtTable();
  } catch (err) {
    console.error("Failed to load product management data:", err);
  }
}

function filterProductMgmtTable() {
  const search = (document.getElementById("mgmtSearchInput")?.value || "").toLowerCase().trim();
  const category = document.getElementById("mgmtCategoryFilter")?.value || "ALL";
  const store = document.getElementById("mgmtStoreFilter")?.value || "ALL";

  let filtered = allProductMgmtData;

  if (category !== "ALL") {
    filtered = filtered.filter((i) => i.category === category);
  }

  if (store !== "ALL") {
    filtered = filtered.filter((i) => i.store_id === store);
  }

  if (search) {
    filtered = filtered.filter(
      (i) =>
        i.product_name.toLowerCase().includes(search) ||
        i.product_id.toLowerCase().includes(search) ||
        i.store_name.toLowerCase().includes(search) ||
        i.category.toLowerCase().includes(search)
    );
  }

  renderProductMgmtTable(filtered);
}

function renderProductMgmtTable(items) {
  const tbody = document.getElementById("productMgmtTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="12" style="text-align:center; padding:30px; color:#64748b;">No products match current filters.</td></tr>`;
    return;
  }

  items.forEach((item) => {
    const tr = document.createElement("tr");

    // Coverage calculation
    const coverage = item.days_of_stock;
    let fillClass = "healthy";
    let pct = Math.min(100, Math.max(8, (coverage / 30) * 100));

    if (coverage < 5) {
      fillClass = "critical";
    } else if (coverage < 10) {
      fillClass = "warning";
    } else if (coverage > 60) {
      fillClass = "overstock";
      pct = 100;
    }

    const coverageDisplay = coverage > 900 ? "∞" : coverage <= 0 ? "0.0d" : coverage.toFixed(1) + "d";
    const statusText = (item.status_tag || "HEALTHY").replace(/_/g, " ");

    tr.innerHTML = `
      <td><span style="font-family: var(--font-mono); font-size: 11px; color: #38bdf8; font-weight: 700;">${escapeHtml(item.product_id)}</span></td>
      <td><strong style="color: #ffffff;">${escapeHtml(item.product_name)}</strong></td>
      <td><span style="font-size: 11px; color: #94a3b8;">${escapeHtml(item.category)}</span></td>
      <td><span style="font-size: 12px;">${escapeHtml(item.store_name)}</span></td>
      <td style="font-family: var(--font-mono);">$${Number(item.selling_price).toFixed(2)}</td>
      <td style="font-family: var(--font-mono); font-weight: 700; color: #38bdf8; font-size: 13px;">${item.current_stock}</td>
      <td style="font-family: var(--font-mono);">${item.reorder_level}</td>
      <td style="font-family: var(--font-mono);">${item.safety_stock}</td>
      <td style="font-family: var(--font-mono);">${item.lead_time_days}d</td>
      <td>
        <div class="coverage-meter">
          <span style="font-family: var(--font-mono); font-size: 11px; width: 38px;">${coverageDisplay}</span>
          <div class="meter-bar">
            <div class="meter-fill ${fillClass}" style="width: ${pct}%"></div>
          </div>
        </div>
      </td>
      <td><span class="status-tag ${item.status_tag}">${statusText}</span></td>
      <td>
        <div class="actions-cell-group">
          <button class="btn-table-action" title="Quick Stock Update" onclick="openUpdateStockModal('${escapeHtml(item.product_id)}', '${escapeHtml(item.store_id)}', '${escapeHtml(item.product_name.replace(/'/g, "\\'"))}', '${escapeHtml(item.store_name.replace(/'/g, "\\'"))}', ${item.current_stock})">
            ⚡ Stock
          </button>
          <button class="btn-table-action edit" title="Edit Catalog Properties" onclick="openEditProductModal('${escapeHtml(item.product_id)}')">
            ✏️ Edit
          </button>
          <button class="btn-table-action delete" title="Delete Product from Catalog" onclick="deleteProduct('${escapeHtml(item.product_id)}', '${escapeHtml(item.product_name.replace(/'/g, "\\'"))}')">
            🗑️
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

/* ==========================================================
   11. MODAL CONTROLLERS & FORM HANDLERS
   ========================================================== */

async function openAddProductModal() {
  const modal = document.getElementById("addProductModal");
  if (!modal) return;

  try {
    const res = await fetch("/api/next-product-id");
    const data = await res.json();
    if (data.status === "success") {
      document.getElementById("newProductId").value = data.next_product_id;
    }
  } catch (err) {
    console.error("Failed to fetch next product ID:", err);
  }

  // Set default values
  document.getElementById("newProductName").value = "";
  document.getElementById("newProductCategory").selectedIndex = 0;
  document.getElementById("newProductPrice").value = "";
  document.getElementById("newProductStore").selectedIndex = 0;
  document.getElementById("newProductStock").value = "50";
  document.getElementById("newProductReorder").value = "20";
  document.getElementById("newProductSafety").value = "10";
  document.getElementById("newProductLeadTime").value = "7";
  document.getElementById("newProductSupplier").value = "";

  modal.style.display = "flex";
  setTimeout(() => document.getElementById("newProductName")?.focus(), 50);
}

function closeAddProductModal() {
  const modal = document.getElementById("addProductModal");
  if (modal) modal.style.display = "none";
}

async function handleProductSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("newProductName").value.trim();
  const category = document.getElementById("newProductCategory").value;
  const price = parseFloat(document.getElementById("newProductPrice").value);
  const store = document.getElementById("newProductStore").value;
  const stock = parseInt(document.getElementById("newProductStock").value, 10);
  const reorder = parseInt(document.getElementById("newProductReorder").value, 10);
  const safety = parseInt(document.getElementById("newProductSafety").value, 10);
  const lead = parseInt(document.getElementById("newProductLeadTime").value, 10);
  const supplier = document.getElementById("newProductSupplier").value.trim();

  // Frontend validation
  if (!name) {
    showToast("Validation Error", "Product name is required.", "error");
    return;
  }
  if (!category) {
    showToast("Validation Error", "Please select a product category.", "error");
    return;
  }
  if (isNaN(price) || price <= 0) {
    showToast("Validation Error", "Selling price must be greater than 0.", "error");
    return;
  }
  if (!store) {
    showToast("Validation Error", "Please select an initial destination store.", "error");
    return;
  }
  if (isNaN(stock) || stock < 0) {
    showToast("Validation Error", "Initial stock cannot be negative.", "error");
    return;
  }
  if (isNaN(reorder) || reorder < 0) {
    showToast("Validation Error", "Reorder level cannot be negative.", "error");
    return;
  }
  if (isNaN(safety) || safety < 0) {
    showToast("Validation Error", "Safety stock cannot be negative.", "error");
    return;
  }
  if (isNaN(lead) || lead < 1) {
    showToast("Validation Error", "Lead time must be at least 1 day.", "error");
    return;
  }

  const payload = {
    product_name: name,
    category: category,
    selling_price: price,
    store: store,
    current_stock: stock,
    reorder_level: reorder,
    safety_stock: safety,
    lead_time_days: lead,
    supplier: supplier || "Direct Wholesaler"
  };

  const saveBtn = document.getElementById("saveProductBtn");
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = "<span>Saving...</span>";
  }

  try {
    const res = await fetch("/api/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      closeAddProductModal();
      showToast(
        "Product Created",
        `SKU ${result.product_id} (${name}) added to catalog and store inventory!`,
        "success"
      );
      // Synchronously refresh all views
      await Promise.all([
        loadDashboardData(),
        loadAlerts(),
        loadInventory(),
        loadProductManagement()
      ]);
    } else {
      showToast("Creation Failed", result.message || "Could not add product.", "error");
    }
  } catch (err) {
    showToast("Network Error", err.message, "error");
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `<span class="btn-icon">💾</span><span>Save Product</span>`;
    }
  }
}

function openUpdateStockModal(productId, storeId, productName, storeName, currentStock) {
  const modal = document.getElementById("updateStockModal");
  if (!modal) return;

  document.getElementById("updateStockProductId").value = productId;
  document.getElementById("updateStockStoreId").value = storeId;
  document.getElementById("updateStockProductNameDisplay").textContent = productName;
  document.getElementById("updateStockStoreNameDisplay").textContent = storeName;
  document.getElementById("updateStockCurrentDisplay").textContent = `${currentStock} units`;
  document.getElementById("updateStockNewVal").value = currentStock;

  modal.style.display = "flex";
  setTimeout(() => {
    const input = document.getElementById("updateStockNewVal");
    if (input) {
      input.focus();
      input.select();
    }
  }, 50);
}

function closeUpdateStockModal() {
  const modal = document.getElementById("updateStockModal");
  if (modal) modal.style.display = "none";
}

async function handleStockUpdateSubmit(e) {
  e.preventDefault();
  const productId = document.getElementById("updateStockProductId").value;
  const storeId = document.getElementById("updateStockStoreId").value;
  const newStockVal = document.getElementById("updateStockNewVal").value;
  const newStock = parseInt(newStockVal, 10);
  const reason = document.getElementById("updateStockReason").value;

  if (isNaN(newStock) || newStock < 0) {
    showToast("Validation Error", "Stock quantity cannot be negative.", "error");
    return;
  }

  const saveBtn = document.getElementById("saveStockBtn");
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = "<span>Updating...</span>";
  }

  try {
    const res = await fetch("/api/inventory", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: productId,
        store_id: storeId,
        stock: newStock,
        reason: reason
      })
    });
    const result = await res.json();

    if (result.success) {
      closeUpdateStockModal();
      showToast(
        "Stock Updated",
        `Stock for ${document.getElementById("updateStockProductNameDisplay").textContent} set to ${newStock} units.`,
        "success"
      );
      // Synchronously refresh all views
      await Promise.all([
        loadDashboardData(),
        loadAlerts(),
        loadInventory(),
        loadProductManagement()
      ]);
    } else {
      showToast("Update Failed", result.message || "Could not update stock.", "error");
    }
  } catch (err) {
    showToast("Network Error", err.message, "error");
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `<span class="btn-icon">⚡</span><span>Update Stock</span>`;
    }
  }
}

/* ==========================================================
   12. TOAST NOTIFICATIONS & GLOBAL BINDINGS
   ========================================================== */

function showToast(title, message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast-notification ${type}`;

  const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";

  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-msg">${escapeHtml(message)}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function openEditProductModal(productId) {
  const modal = document.getElementById("editProductModal");
  if (!modal) return;

  const item = allProductMgmtData.find((p) => p.product_id === productId);
  if (!item) return;

  document.getElementById("editProductId").value = item.product_id;
  document.getElementById("editProductIdDisplay").value = item.product_id;
  document.getElementById("editProductName").value = item.product_name;
  document.getElementById("editProductCategory").value = item.category || "Electronics";
  document.getElementById("editProductPrice").value = item.selling_price;
  document.getElementById("editProductReorder").value = item.reorder_level;
  document.getElementById("editProductSafety").value = item.safety_stock;
  document.getElementById("editProductLeadTime").value = item.lead_time_days;

  modal.style.display = "flex";
  setTimeout(() => document.getElementById("editProductName")?.focus(), 50);
}

function closeEditProductModal() {
  const modal = document.getElementById("editProductModal");
  if (modal) modal.style.display = "none";
}

async function handleProductEditSubmit(e) {
  e.preventDefault();
  const productId = document.getElementById("editProductId").value;
  const name = document.getElementById("editProductName").value.trim();
  const category = document.getElementById("editProductCategory").value;
  const price = parseFloat(document.getElementById("editProductPrice").value);
  const reorder = parseInt(document.getElementById("editProductReorder").value, 10);
  const safety = parseInt(document.getElementById("editProductSafety").value, 10);
  const lead = parseInt(document.getElementById("editProductLeadTime").value, 10);

  if (!name) {
    showToast("Validation Error", "Product name is required.", "error");
    return;
  }
  if (isNaN(price) || price <= 0) {
    showToast("Validation Error", "Price must be greater than 0.", "error");
    return;
  }

  const payload = {
    product_name: name,
    category: category,
    selling_price: price,
    reorder_level: reorder,
    safety_stock: safety,
    lead_time_days: lead
  };

  const saveBtn = document.getElementById("saveEditProductBtn");
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = "<span>Saving...</span>";
  }

  try {
    const res = await fetch(`/api/products/${encodeURIComponent(productId)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      closeEditProductModal();
      showToast(
        "Product Updated",
        `Catalog properties for ${name} (${productId}) have been updated.`,
        "success"
      );
      await Promise.all([
        loadDashboardData(),
        loadAlerts(),
        loadInventory(),
        loadProductManagement()
      ]);
    } else {
      showToast("Update Failed", result.message || "Could not update product.", "error");
    }
  } catch (err) {
    showToast("Network Error", err.message, "error");
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `<span class="btn-icon">💾</span><span>Save Changes</span>`;
    }
  }
}

async function deleteProduct(productId, productName) {
  const confirmed = window.confirm(
    `Are you sure you want to permanently DELETE "${productName}" (${productId})?\n\nThis will remove it from the catalog and delete all inventory balances across all stores.`
  );
  if (!confirmed) return;

  try {
    const res = await fetch(`/api/products/${encodeURIComponent(productId)}`, {
      method: "DELETE"
    });
    const result = await res.json();

    if (result.success) {
      showToast(
        "Product Deleted",
        `Product "${productName}" (${productId}) was removed from the catalog.`,
        "info"
      );
      await Promise.all([
        loadDashboardData(),
        loadAlerts(),
        loadInventory(),
        loadProductManagement()
      ]);
    } else {
      showToast("Delete Failed", result.message || "Could not delete product.", "error");
    }
  } catch (err) {
    showToast("Network Error", err.message, "error");
  }
}

// Window attachments for inline event handlers
window.openAddProductModal = openAddProductModal;
window.closeAddProductModal = closeAddProductModal;
window.handleProductSubmit = handleProductSubmit;
window.openUpdateStockModal = openUpdateStockModal;
window.closeUpdateStockModal = closeUpdateStockModal;
window.handleStockUpdateSubmit = handleStockUpdateSubmit;
window.openEditProductModal = openEditProductModal;
window.closeEditProductModal = closeEditProductModal;
window.handleProductEditSubmit = handleProductEditSubmit;
window.deleteProduct = deleteProduct;
window.showToast = showToast;
window.filterProductMgmtTable = filterProductMgmtTable;
