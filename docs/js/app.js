/**
 * StackRecon — Application Entry Point
 * Fetches data.json, builds indices, wires all filter controls.
 */

"use strict";

window.stackrecon = window.stackrecon || {
  programs: [],
  indices: {},
  activeFilters: { tech: "", platform: "", reward: "", name: "" },
};

var DATA_URL = "./data/data.json";

// ---- DOM refs (resolved after DOMContentLoaded) ----------------------------
var resultsContainer, statsBar, techSelect, platformSelect, rewardSelect, nameInput, clearBtn;
var copyAllBannerEl;

// ---- Shortcuts — NEVER use top-level destructuring (Firefox global conflict) --
function C(name) { return window.stackrecon.components[name]; }
function F(name) { return window.stackrecon.filters[name]; }
function S(name) { return window.stackrecon.search[name]; }

// ---- Header stats chips ----------------------------------------------------

function updateHeaderStats(programs, totalDetections, totalTechs) {
  var chipsContainer = document.getElementById("header-stats");
  if (!chipsContainer) return;

  var chipPrograms = document.getElementById("stat-programs");
  var chipDetections = document.getElementById("stat-detections");
  var chipTechs = document.getElementById("stat-techs");

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

// ---- CopyAll banner --------------------------------------------------------

function updateCopyAllBanner(activeTech) {
  if (!copyAllBannerEl) return;

  if (!activeTech) {
    copyAllBannerEl.updateBanner("", []);
    return;
  }

  // Collect all hostnames from all programs whose detections match activeTech
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

// ---- Render ----------------------------------------------------------------

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
    // Staggered animation via CSS custom property
    card.style.setProperty("--card-index", String(Math.min(i, 30)));
    frag.appendChild(card);
  }
  resultsContainer.appendChild(frag);
  statsBar.textContent =
    "Showing " + programIndices.length + " of " + window.stackrecon.programs.length + " programs";
}

// ---- Index build -----------------------------------------------------------

function buildIndices(programs) {
  window.stackrecon.indices = {
    tech:     F("buildTechIndex")(programs),
    platform: F("buildPlatformIndex")(programs),
    reward:   F("buildRewardIndex")(programs),
  };
}

// ---- Filter application ----------------------------------------------------

function applyFilters() {
  var state = {
    techIndex:     window.stackrecon.indices.tech,
    platformIndex: window.stackrecon.indices.platform,
    rewardIndex:   window.stackrecon.indices.reward,
    programs:      window.stackrecon.programs,
    activeFilters: window.stackrecon.activeFilters,
  };
  var indices = F("applyAllFilters")(state);
  S("writeFiltersToHash")(window.stackrecon.activeFilters);
  var activeTech = window.stackrecon.activeFilters.tech;
  updateCopyAllBanner(activeTech);
  renderResults(indices, activeTech);
}

// ---- Clear filters ---------------------------------------------------------

function clearAllFilters() {
  window.stackrecon.activeFilters = { tech: "", platform: "", reward: "", name: "" };
  techSelect.value     = "";
  platformSelect.value = "";
  rewardSelect.value   = "";
  nameInput.value      = "";
  S("writeFiltersToHash")({});
  updateCopyAllBanner("");
  var allIndices = window.stackrecon.programs.map(function (_, i) { return i; });
  renderResults(allIndices, null);
  statsBar.textContent =
    "Showing " + window.stackrecon.programs.length + " of " + window.stackrecon.programs.length + " programs";
}

// ---- Populate tech dropdown ------------------------------------------------

function initTechDropdown(programs) {
  var techs = F("getAllTechnologies")(programs);
  for (var i = 0; i < techs.length; i++) {
    var opt = document.createElement("option");
    opt.value       = techs[i];
    opt.textContent = techs[i];
    techSelect.appendChild(opt);
  }
}

// ---- Restore filters from URL hash ----------------------------------------

function restoreFiltersFromHash() {
  var saved = S("readFiltersFromHash")();
  window.stackrecon.activeFilters = saved;
  if (saved.tech)     techSelect.value     = saved.tech;
  if (saved.platform) platformSelect.value = saved.platform;
  if (saved.reward)   rewardSelect.value   = saved.reward;
  if (saved.name)     nameInput.value      = saved.name;
}

// ---- Last-updated footer ---------------------------------------------------

function setLastUpdated(meta) {
  var elUpdated = document.getElementById("last-updated");
  if (!elUpdated || !meta || !meta.generated_at) return;
  var d = new Date(meta.generated_at);
  elUpdated.textContent = isNaN(d.getTime())
    ? meta.generated_at
    : d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

// ---- Compute totals --------------------------------------------------------

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

// ---- Data fetch ------------------------------------------------------------

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
      lastGeneratedAt = data.meta && data.meta.generated_at || null;

      var totals = computeTotals(window.stackrecon.programs);
      // Use meta counts if available, fall back to computed
      var programCount    = (data.meta && data.meta.programs_scanned) || window.stackrecon.programs.length;
      var detectionCount  = (data.meta && data.meta.total_detections) || totals.detections;
      updateHeaderStats(programCount, detectionCount, totals.techs);

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

// ---- Wire controls ---------------------------------------------------------

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

  nameInput.addEventListener(
    "input",
    S("debounce")(function () {
      window.stackrecon.activeFilters.name = nameInput.value.trim();
      applyFilters();
    }, 200)
  );

  clearBtn.addEventListener("click", clearAllFilters);
}

// ---- Insert CopyAllBanner into DOM -----------------------------------------

function initCopyAllBanner() {
  // Insert banner between stats-bar and results-container
  copyAllBannerEl = C("CopyAllBanner")("", []);
  var statsBarEl  = document.getElementById("stats-bar");
  if (statsBarEl && statsBarEl.parentNode) {
    statsBarEl.parentNode.insertBefore(copyAllBannerEl, statsBarEl.nextSibling);
  } else {
    // Fallback: insert before results container
    if (resultsContainer && resultsContainer.parentNode) {
      resultsContainer.parentNode.insertBefore(copyAllBannerEl, resultsContainer);
    }
  }
}

// ---- Auto-refresh ----------------------------------------------------------

var lastGeneratedAt = null;
var REFRESH_INTERVAL_MS = 15 * 60 * 1000; // 15 minutes

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
        // New data available — reload silently
        window.stackrecon.programs = data.programs || [];
        buildIndices(window.stackrecon.programs);

        // Rebuild tech dropdown
        while (techSelect.options.length > 1) techSelect.remove(1);
        initTechDropdown(window.stackrecon.programs);

        setLastUpdated(data.meta);
        var totals = computeTotals(window.stackrecon.programs);
        var programCount   = (data.meta && data.meta.programs_scanned) || window.stackrecon.programs.length;
        var detectionCount = (data.meta && data.meta.total_detections) || totals.detections;
        updateHeaderStats(programCount, detectionCount, totals.techs);
        applyFilters();
      }
      lastGeneratedAt = newGenerated;
    })
    .catch(function () {});
}

// ---- Bootstrap -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  resultsContainer = document.getElementById("results-container");
  statsBar         = document.getElementById("stats-bar");
  techSelect       = document.getElementById("tech-filter");
  platformSelect   = document.getElementById("platform-filter");
  rewardSelect     = document.getElementById("reward-filter");
  nameInput        = document.getElementById("name-search");
  clearBtn         = document.getElementById("clear-filters");

  wireControls();
  initCopyAllBanner();
  fetchData().then(function () {
    // Start auto-refresh after initial load
    setInterval(checkForUpdates, REFRESH_INTERVAL_MS);
  });
});
