/**
 * StackRecon — Application Entry Point
 */

"use strict";

window.stackrecon = window.stackrecon || {
  programs: [],
  indices: {},
  activeFilters: { tech: "", platform: "", reward: "", severity: "", name: "" },
};

var DATA_URL     = "./data/data.json";
var PROGRESS_URL = "./data/progress.json";

var resultsContainer, statsBar, techSelect, platformSelect, rewardSelect, severitySelect, nameInput, clearBtn;
var copyAllBannerEl;
var insightsPanelEl;

function C(name) { return window.stackrecon.components[name]; }
function F(name) { return window.stackrecon.filters[name]; }
function S(name) { return window.stackrecon.search[name]; }

// ─────────────────────────────────────────────────────────────
// Live scan progress overlay
// ─────────────────────────────────────────────────────────────

var scanOverlay      = null;
var scanProgressBar  = null;
var scanPhaseLabel   = null;
var scanPhaseCounter = null;
var scanElapsed      = null;
var scanStatsRow     = null;
var lastProgressStatus = "idle";
var PROGRESS_POLL_MS   = 15000; // poll every 15s

var PHASE_PCTS = { starting: 2, chaos: 10, httpx: 40, nuclei_vuln: 75, nuclei_info: 92, done: 100 };

function initScanOverlay() {
  scanOverlay      = document.getElementById("scan-overlay");
  scanProgressBar  = document.getElementById("scan-progress-bar");
  scanPhaseLabel   = document.getElementById("scan-phase-label");
  scanPhaseCounter = document.getElementById("scan-phase-counter");
  scanElapsed      = document.getElementById("scan-elapsed");
  scanStatsRow     = document.getElementById("scan-stats-row");
}

function updateScanOverlay(p) {
  if (!scanOverlay) return;

  var isScanning = p.status === "scanning";

  if (isScanning) {
    scanOverlay.classList.remove("hidden");
  } else {
    scanOverlay.classList.add("hidden");
    return;
  }

  // Phase label
  if (scanPhaseLabel) scanPhaseLabel.textContent = p.phase_label || "Running…";

  // Progress bar
  var pct = PHASE_PCTS[p.phase] || Math.round((p.phase_number / p.total_phases) * 100);
  if (scanProgressBar) scanProgressBar.style.width = pct + "%";

  // Phase counter
  if (scanPhaseCounter) {
    scanPhaseCounter.textContent = "Phase " + (p.phase_number || 0) + " / " + (p.total_phases || 4);
  }

  // Elapsed time
  if (scanElapsed && p.started_at) {
    var elapsed = Math.round((Date.now() - new Date(p.started_at).getTime()) / 1000);
    var mins = Math.floor(elapsed / 60);
    var secs = elapsed % 60;
    scanElapsed.textContent = mins + "m " + (secs < 10 ? "0" : "") + secs + "s elapsed";
  }

  // Stats row
  if (scanStatsRow) {
    var parts = [];
    if (p.programs_loaded)    parts.push("<span>" + p.programs_loaded.toLocaleString() + " programs</span>");
    if (p.hostnames_total)    parts.push("<span>" + p.hostnames_total.toLocaleString() + " subdomains</span>");
    if (p.detections_so_far)  parts.push("<span>" + p.detections_so_far.toLocaleString() + " live hosts</span>");
    if (p.vuln_findings)      parts.push('<span class="sev-stat-critical">' + p.vuln_findings + " vulns found</span>");
    scanStatsRow.innerHTML = parts.join("");
  }
}

function pollProgress() {
  fetch(PROGRESS_URL + "?t=" + Date.now(), { cache: "no-store" })
    .then(function(resp) { if (!resp.ok) throw new Error("no progress"); return resp.json(); })
    .then(function(p) {
      updateScanOverlay(p);
      // If scan just finished, reload data
      if (lastProgressStatus === "scanning" && p.status === "idle") {
        fetchData();
      }
      lastProgressStatus = p.status || "idle";
    })
    .catch(function() {});
}

// ─────────────────────────────────────────────────────────────
// Header stats
// ─────────────────────────────────────────────────────────────

function updateHeaderStats(programs, totalDetections, totalTechs) {
  var chipsContainer = document.getElementById("header-stats");
  if (!chipsContainer) return;

  var chipPrograms   = document.getElementById("stat-programs");
  var chipDetections = document.getElementById("stat-detections");
  var chipTechs      = document.getElementById("stat-techs");

  if (chipPrograms) {
    chipPrograms.innerHTML = "<strong>" + programs.toLocaleString() + "</strong> programs";
    chipPrograms.classList.add("loaded");
  }
  if (chipDetections) {
    chipDetections.innerHTML = "<strong>" + totalDetections.toLocaleString() + "</strong> detections";
    chipDetections.classList.add("loaded");
  }
  if (chipTechs) {
    chipTechs.innerHTML = "<strong>" + totalTechs.toLocaleString() + "</strong> technologies";
    chipTechs.classList.add("loaded");
  }
}

function updateCopyAllBanner(activeTech) {
  if (!copyAllBannerEl) return;
  if (!activeTech) {
    copyAllBannerEl.updateBanner("", []);
    return;
  }
  var allHostnames = [];
  var programs = window.stackrecon.programs;
  for (var i = 0; i < programs.length; i++) {
    var dets = programs[i].detections;
    for (var j = 0; j < dets.length; j++) {
      if (dets[j].technologies.indexOf(activeTech) !== -1) {
        allHostnames.push(dets[j].hostname);
      }
    }
  }
  copyAllBannerEl.updateBanner(activeTech, allHostnames);
}

function renderResults(programIndices, activeTech) {
  resultsContainer.innerHTML = "";

  if (programIndices.length === 0) {
    resultsContainer.appendChild(
      C("EmptyState")("No programs match the current filters.", clearAllFilters)
    );
    statsBar.textContent = "No programs found";
    return;
  }

  var frag = document.createDocumentFragment();
  for (var i = 0; i < programIndices.length; i++) {
    var card = C("ProgramCard")(window.stackrecon.programs[programIndices[i]], activeTech || null);
    card.style.setProperty("--card-index", String(Math.min(i, 30)));
    frag.appendChild(card);
  }
  resultsContainer.appendChild(frag);
  statsBar.textContent =
    "Showing " + programIndices.length + " of " + window.stackrecon.programs.length + " programs";
}

function buildIndices(programs) {
  window.stackrecon.indices = {
    tech:     F("buildTechIndex")(programs),
    platform: F("buildPlatformIndex")(programs),
    reward:   F("buildRewardIndex")(programs),
    severity: F("buildSeverityIndex")(programs),
  };
}

function applyFilters() {
  var state = {
    techIndex:     window.stackrecon.indices.tech,
    platformIndex: window.stackrecon.indices.platform,
    rewardIndex:   window.stackrecon.indices.reward,
    severityIndex: window.stackrecon.indices.severity,
    programs:      window.stackrecon.programs,
    activeFilters: window.stackrecon.activeFilters,
  };
  var indices = F("applyAllFilters")(state);
  S("writeFiltersToHash")(window.stackrecon.activeFilters);
  var activeTech = window.stackrecon.activeFilters.tech;
  updateCopyAllBanner(activeTech);
  renderResults(indices, activeTech);
}

function clearAllFilters() {
  window.stackrecon.activeFilters = { tech: "", platform: "", reward: "", severity: "", name: "" };
  techSelect.value      = "";
  platformSelect.value  = "";
  rewardSelect.value    = "";
  severitySelect.value  = "";
  nameInput.value       = "";
  S("writeFiltersToHash")({});
  updateCopyAllBanner("");
  var allIndices = window.stackrecon.programs.map(function (_, i) { return i; });
  renderResults(allIndices, null);
  statsBar.textContent =
    "Showing " + window.stackrecon.programs.length + " of " + window.stackrecon.programs.length + " programs";
}

function initTechDropdown(programs) {
  var techs = F("getAllTechnologies")(programs);
  for (var i = 0; i < techs.length; i++) {
    var opt = document.createElement("option");
    opt.value       = techs[i];
    opt.textContent = techs[i];
    techSelect.appendChild(opt);
  }
}

function restoreFiltersFromHash() {
  var saved = S("readFiltersFromHash")();
  window.stackrecon.activeFilters = saved;
  if (saved.tech)     techSelect.value     = saved.tech;
  if (saved.platform) platformSelect.value = saved.platform;
  if (saved.reward)   rewardSelect.value   = saved.reward;
  if (saved.severity) severitySelect.value = saved.severity;
  if (saved.name)     nameInput.value      = saved.name;
}

function setLastUpdated(meta) {
  var elUpdated = document.getElementById("last-updated");
  if (!elUpdated || !meta || !meta.generated_at) return;
  var d = new Date(meta.generated_at);
  elUpdated.textContent = isNaN(d.getTime())
    ? meta.generated_at
    : d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function computeTotals(programs) {
  var totalDetections = 0;
  var techSet = {};
  for (var i = 0; i < programs.length; i++) {
    totalDetections += programs[i].detection_count || 0;
    var techs = programs[i].technologies;
    for (var j = 0; j < techs.length; j++) {
      techSet[techs[j]] = true;
    }
  }
  return {
    detections: totalDetections,
    techs: Object.keys(techSet).length,
  };
}

function fetchData() {
  resultsContainer.innerHTML = "";
  resultsContainer.appendChild(C("LoadingSpinner")("Fetching program data…"));

  return fetch(DATA_URL)
    .then(function (resp) {
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      return resp.json();
    })
    .then(function (data) {
      window.stackrecon.programs = data.programs || [];
      buildIndices(window.stackrecon.programs);
      initTechDropdown(window.stackrecon.programs);
      setLastUpdated(data.meta);
      lastGeneratedAt = (data.meta && data.meta.generated_at) || null;

      var totals = computeTotals(window.stackrecon.programs);
      var programCount   = (data.meta && data.meta.programs_scanned) || window.stackrecon.programs.length;
      var detectionCount = (data.meta && data.meta.total_detections) || totals.detections;
      updateHeaderStats(programCount, detectionCount, totals.techs);

      initInsightsPanel(window.stackrecon.programs);
      restoreFiltersFromHash();
      applyFilters();
    })
    .catch(function (err) {
      resultsContainer.innerHTML = "";
      resultsContainer.appendChild(
        C("ErrorBanner")("Failed to load program data: " + err.message, fetchData)
      );
      statsBar.textContent = "Error loading data";
    });
}

function wireControls() {
  techSelect.addEventListener("change", function () {
    window.stackrecon.activeFilters.tech = techSelect.value;
    applyFilters();
  });

  platformSelect.addEventListener("change", function () {
    window.stackrecon.activeFilters.platform = platformSelect.value;
    applyFilters();
  });

  rewardSelect.addEventListener("change", function () {
    window.stackrecon.activeFilters.reward = rewardSelect.value;
    applyFilters();
  });

  severitySelect.addEventListener("change", function () {
    window.stackrecon.activeFilters.severity = severitySelect.value;
    applyFilters();
  });

  nameInput.addEventListener(
    "input",
    S("debounce")(function () {
      window.stackrecon.activeFilters.name = nameInput.value.trim();
      applyFilters();
    }, 200)
  );

  clearBtn.addEventListener("click", clearAllFilters);
}

function initCopyAllBanner() {
  copyAllBannerEl = C("CopyAllBanner")("", []);
  var statsBarEl  = document.getElementById("stats-bar");
  if (statsBarEl && statsBarEl.parentNode) {
    statsBarEl.parentNode.insertBefore(copyAllBannerEl, statsBarEl.nextSibling);
  } else {
    if (resultsContainer && resultsContainer.parentNode) {
      resultsContainer.parentNode.insertBefore(copyAllBannerEl, resultsContainer);
    }
  }
}

function initInsightsPanel(programs) {
  var newPanel = C("InsightsPanel")(programs);
  window.stackrecon._onInsightClick = function (tech) {
    techSelect.value = tech;
    window.stackrecon.activeFilters.tech = tech;
    applyFilters();
    resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (insightsPanelEl && insightsPanelEl.parentNode) {
    insightsPanelEl.parentNode.replaceChild(newPanel, insightsPanelEl);
  } else {
    var statsBarEl = document.getElementById("stats-bar");
    if (statsBarEl && statsBarEl.parentNode) {
      statsBarEl.parentNode.insertBefore(newPanel, statsBarEl.nextSibling);
    }
  }
  insightsPanelEl = newPanel;
}

var lastGeneratedAt = null;
var REFRESH_INTERVAL_MS = 15 * 60 * 1000;

function checkForUpdates() {
  fetch(DATA_URL, { cache: "no-store" })
    .then(function (resp) {
      if (!resp.ok) return;
      return resp.json();
    })
    .then(function (data) {
      if (!data || !data.meta) return;
      var newGenerated = data.meta.generated_at;
      if (lastGeneratedAt && newGenerated !== lastGeneratedAt) {
        window.stackrecon.programs = data.programs || [];
        buildIndices(window.stackrecon.programs);
        while (techSelect.options.length > 1) techSelect.remove(1);
        initTechDropdown(window.stackrecon.programs);
        setLastUpdated(data.meta);
        var totals = computeTotals(window.stackrecon.programs);
        var programCount   = (data.meta && data.meta.programs_scanned) || window.stackrecon.programs.length;
        var detectionCount = (data.meta && data.meta.total_detections) || totals.detections;
        updateHeaderStats(programCount, detectionCount, totals.techs);
        initInsightsPanel(window.stackrecon.programs);
        applyFilters();
      }
      lastGeneratedAt = newGenerated;
    })
    .catch(function () {});
}

document.addEventListener("DOMContentLoaded", function () {
  resultsContainer  = document.getElementById("results-container");
  statsBar          = document.getElementById("stats-bar");
  techSelect        = document.getElementById("tech-filter");
  platformSelect    = document.getElementById("platform-filter");
  rewardSelect      = document.getElementById("reward-filter");
  severitySelect    = document.getElementById("severity-filter");
  nameInput         = document.getElementById("name-search");
  clearBtn          = document.getElementById("clear-filters");

  initScanOverlay();
  wireControls();
  initCopyAllBanner();

  // Start progress polling immediately
  pollProgress();
  setInterval(pollProgress, PROGRESS_POLL_MS);

  fetchData().then(function () {
    setInterval(checkForUpdates, REFRESH_INTERVAL_MS);
  });
});
